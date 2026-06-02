"""
Push-to-talk daemon. Long-running. Watches %TEMP% for trigger flags from the
AHK hotkey script, records mic when told to start, transcribes via
faster-whisper when told to stop, writes the result to a file the AHK script
reads.

Why a long-running daemon: faster-whisper takes a few seconds to load the model.
Loading on every PTT press would make the system feel sluggish. The daemon
loads once and stays warm, so each press incurs only the actual transcription
cost (~0.5-1s for short clips).
"""

import sys
import time
import tempfile
import threading
from pathlib import Path

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

TMP = Path(tempfile.gettempdir())
START_FLAG = TMP / "ptt_start.flag"
STOP_FLAG = TMP / "ptt_stop.flag"
RESULT_FILE = TMP / "ptt_result.txt"
READY_FILE = TMP / "ptt_ready.flag"
LOG_FILE = Path(__file__).parent / "ptt_daemon.log"

SAMPLERATE = 16000
CHANNELS = 1


def log(msg):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def main():
    # Clear any stale state from a previous run.
    for p in (START_FLAG, STOP_FLAG, RESULT_FILE, READY_FILE):
        try:
            p.unlink()
        except FileNotFoundError:
            pass

    log("daemon starting; loading whisper small.en")
    try:
        model = WhisperModel("small.en", device="cpu", compute_type="int8")
    except Exception as e:
        log(f"FATAL: model load failed: {e}")
        return
    log("model loaded; opening audio stream")

    state = {"frames": [], "recording": False, "lock": threading.Lock()}

    def callback(indata, n_frames, time_info, status):
        if state["recording"]:
            with state["lock"]:
                state["frames"].append(indata.copy())

    try:
        stream = sd.InputStream(
            samplerate=SAMPLERATE, channels=CHANNELS, callback=callback, dtype="float32"
        )
        stream.start()
    except Exception as e:
        log(f"FATAL: audio stream failed: {e}")
        return

    READY_FILE.write_text("ready", encoding="utf-8")
    log("ready; waiting for triggers")

    try:
        while True:
            if START_FLAG.exists():
                try:
                    START_FLAG.unlink()
                except FileNotFoundError:
                    pass
                with state["lock"]:
                    state["frames"] = []
                state["recording"] = True
                log("recording started")
            elif STOP_FLAG.exists() and state["recording"]:
                try:
                    STOP_FLAG.unlink()
                except FileNotFoundError:
                    pass
                state["recording"] = False
                with state["lock"]:
                    frames = list(state["frames"])
                    state["frames"] = []
                log(f"recording stopped; {len(frames)} chunks")

                text = ""
                if frames:
                    try:
                        audio = np.concatenate(frames, axis=0).flatten().astype(np.float32)
                        # Skip if too short (< 0.3s) -- likely an accidental tap.
                        if len(audio) >= int(SAMPLERATE * 0.3):
                            t0 = time.time()
                            segments, info = model.transcribe(
                                audio,
                                language="en",
                                beam_size=1,
                                vad_filter=True,
                            )
                            text = " ".join(seg.text for seg in segments).strip()
                            log(f"transcribed in {time.time() - t0:.2f}s: {text!r}")
                        else:
                            log(f"audio too short ({len(audio)/SAMPLERATE:.2f}s); skipping")
                    except Exception as e:
                        log(f"transcription error: {e}")

                RESULT_FILE.write_text(text, encoding="utf-8")
            time.sleep(0.04)
    except KeyboardInterrupt:
        log("daemon interrupted; shutting down")
    finally:
        try:
            stream.stop()
            stream.close()
        except Exception:
            pass
        try:
            READY_FILE.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
