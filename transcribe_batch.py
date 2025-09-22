"""
Batch transcribe .mp4 files with faster-whisper + BART summary.

Features:
- Processes one video at a time in a child subprocess (avoids hangs).
- Skips files that already have outputs.
- Clear terminal feedback: START / progress seconds / DONE / SKIP / ERROR / TIMEOUT / RETRY / FAIL.
- Kills and retries a file if no audio progress for --progress-timeout seconds.

Setup (macOS):
  brew install ffmpeg
  python -m venv venv && source venv/bin/activate
  pip install --upgrade pip
  pip install faster-whisper transformers sentencepiece

Run (CPU on MacBook Air):
  python transcribe_batch.py run \
    --input input_mp4 \
    --output outputs \
    --model large-v3 \
    --language en \
    --compute-type int8 \
    --beam 5 \
    --timeout 7200 \
    --retries 2 \
    --progress-timeout 180
"""

import argparse
import re
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple

# --------------------------- formatting ---------------------------

def srt_timestamp(t: float) -> str:
    h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# --------------------------- summarization ---------------------------

_summ = None
def _load_summarizer():
    global _summ
    from transformers import pipeline
    _summ = pipeline("summarization", model="facebook/bart-large-cnn", device_map="auto")

def _chunk(text: str, max_chars: int = 3500):
    import re as _re
    text = _re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars: return [text]
    sents = _re.split(r"(?<=[.!?])\s+", text)
    chunks, cur = [], ""
    for s in sents:
        if len(cur) + len(s) + 1 > max_chars and cur:
            chunks.append(cur.strip()); cur = s
        else:
            cur = f"{cur} {s}" if cur else s
    if cur: chunks.append(cur.strip())
    return chunks

def summarize_text(full_text: str, max_sentences: int = 8):
    if not full_text.strip(): return []
    if _summ is None: _load_summarizer()
    first = []
    for c in _chunk(full_text, 3500):
        first.append(_summ(c, max_length=128, min_length=40, do_sample=False)[0]["summary_text"])
    merged = " ".join(first)
    out2 = _summ(merged, max_length=128, min_length=40, do_sample=False)[0]["summary_text"]
    import re as _re
    sents = [s.strip() for s in _re.split(r"(?<=[.!?])\s+", out2) if s.strip()]
    return sents[:max_sentences]

# --------------------------- whisper ---------------------------

_WM = None
def load_whisper(model_size: str, compute_type: str):
    global _WM
    if _WM is None:
        from faster_whisper import WhisperModel as _WM_
        _WM = _WM_
    return _WM(model_size, compute_type=compute_type)

def transcribe_with_feedback(model, media_path: Path, language: str, beam_size: int, progress_timeout: int):
    """
    Streams segments. Prints progress every ~10s of audio.
    Aborts with RuntimeError if no new audio seconds for progress_timeout.
    """
    seg_iter, info = model.transcribe(
        str(media_path),
        language=None if language == "auto" else language,
        beam_size=beam_size,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=400),
    )
    segments: List[Tuple[float, float, str]] = []
    parts: List[str] = []
    last_audio_s = 0.0
    last_wall = time.time()
    last_printed_bucket = -1

    for seg in seg_iter:
        text = seg.text.strip()
        segments.append((seg.start, seg.end, text))
        parts.append(text)

        # progress print every ~10s of audio
        bucket = int(seg.end) // 10
        if bucket != last_printed_bucket:
            print(f"    {media_path.name}: processed {int(seg.end)}s of audio", flush=True)
            last_printed_bucket = bucket

        # update progress tracking
        if seg.end > last_audio_s + 0.5:
            last_audio_s = seg.end
            last_wall = time.time()

        # watchdog: no progress for too long
        if progress_timeout > 0 and (time.time() - last_wall) > progress_timeout:
            print(f"    {media_path.name}: no progress for {progress_timeout}s → aborting", flush=True)
            raise RuntimeError("progress-timeout")

    return segments, " ".join(parts), info

# --------------------------- helpers ---------------------------

def outputs_present(out_dir: Path) -> bool:
    # Consider completed if both transcript and summary exist
    return (out_dir / "transcript.txt").exists() and (out_dir / "summary.md").exists()

def ensure_dirs(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

def write_artifacts(out_dir: Path, segments: List[Tuple[float, float, str]], full_text: str, stem: str, do_summary: bool, summary_max: int):
    # transcript.txt
    with (out_dir / "transcript.txt").open("w", encoding="utf-8") as f:
        for (start, end, text) in segments:
            f.write(f"[{srt_timestamp(start)} - {srt_timestamp(end)}] {text}\n")

    # captions.srt
    with (out_dir / "captions.srt").open("w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(segments, 1):
            f.write(f"{i}\n{srt_timestamp(start)} --> {srt_timestamp(end)}\n{text.strip()}\n\n")

    # captions.vtt
    with (out_dir / "captions.vtt").open("w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for (start, end, text) in segments:
            f.write(f"{srt_timestamp(start).replace(',', '.')} --> {srt_timestamp(end).replace(',', '.')}\n{text.strip()}\n\n")

    # full.txt
    (out_dir / "full.txt").write_text(full_text, encoding="utf-8")

    # summary.md
    if do_summary:
        bullets = summarize_text(full_text, max_sentences=summary_max)
        with (out_dir / "summary.md").open("w", encoding="utf-8") as f:
            f.write(f"# Summary: {stem}\n\n")
            if bullets:
                for b in bullets:
                    f.write(f"- {b}\n")
            else:
                f.write("- No content to summarize.\n")
    else:
        if not (out_dir / "summary.md").exists():
            (out_dir / "summary.md").write_text("# Summary\n\n", encoding="utf-8")

# --------------------------- worker ---------------------------

def worker(args) -> int:
    vid = Path(args.input_file)
    stem = re.sub(r"[^A-Za-z0-9._-]", "_", vid.stem)
    out_dir = Path(args.output_root) / stem
    ensure_dirs(out_dir)

    if outputs_present(out_dir):
        print(f"SKIP (already done): {vid.name}")
        return 0

    model = load_whisper(args.model, args.compute_type)
    print(f"START: {vid.name}", flush=True)

    try:
        segments, full_text, _ = transcribe_with_feedback(
            model,
            vid,
            language=args.language,
            beam_size=args.beam,
            progress_timeout=args.progress_timeout,
        )
    except RuntimeError:
        print(f"ERROR (progress-timeout): {vid.name}", flush=True)
        return 98
    except Exception as e:
        print(f"ERROR: {vid.name} -> {e}", flush=True)
        return 99

    write_artifacts(
        out_dir=out_dir,
        segments=segments,
        full_text=full_text,
        stem=stem,
        do_summary=(args.summarizer == "bart"),
        summary_max=args.summary_max,
    )

    print(f"DONE: {vid.name}", flush=True)
    return 0

# --------------------------- controller ---------------------------

def controller(args):
    in_dir = Path(args.input)
    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)

    files = sorted(in_dir.glob("*.mp4"))
    if not files:
        print(f"No .mp4 files in {in_dir.resolve()}")
        return

    total = len(files)
    done = 0
    skipped = 0
    failed = 0

    for idx, vid in enumerate(files, 1):
        stem = re.sub(r"[^A-Za-z0-9._-]", "_", vid.stem)
        out_dir = out_root / stem

        if outputs_present(out_dir):
            print(f"[{idx}/{total}] SKIP (already done): {vid.name}")
            skipped += 1
            continue

        cmd = [
            sys.executable, __file__, "single",
            "--input-file", str(vid),
            "--output-root", str(out_root),
            "--model", args.model,
            "--compute-type", args.compute_type,
            "--language", args.language,
            "--beam", str(args.beam),
            "--summarizer", args.summarizer,
            "--summary-max", str(args.summary_max),
            "--progress-timeout", str(args.progress_timeout),
        ]

        tries = args.retries + 1
        attempt = 1
        while attempt <= tries:
            print(f"[{idx}/{total}] RUN ({attempt}/{tries}): {vid.name}")
            try:
                subprocess.run(
                    cmd,
                    check=True,
                    timeout=args.timeout if args.timeout > 0 else None,
                )
                done += 1
                break
            except subprocess.TimeoutExpired:
                print(f"[{idx}/{total}] TIMEOUT: {vid.name}")
            except subprocess.CalledProcessError as e:
                print(f"[{idx}/{total}] ERROR (code {e.returncode}): {vid.name}")
            attempt += 1
            if attempt <= tries:
                print(f"[{idx}/{total}] RETRY: {vid.name}")
                time.sleep(3)
            else:
                print(f"[{idx}/{total}] FAIL: {vid.name}")
                failed += 1

    print(f"\nBatch complete. done={done}, skipped={skipped}, failed={failed}, total={total}")

# --------------------------- cli ---------------------------

def build_parser():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode")

    # Controller mode
    c = sub.add_parser("run", help="Batch controller")
    c.add_argument("--input", required=True)
    c.add_argument("--output", required=True)
    c.add_argument("--model", default="large-v3")  # tiny/base/small/medium/large-v3
    c.add_argument("--compute-type", default="int8")  # auto | int8 | int16 | float16 | int8_float16
    c.add_argument("--language", default="auto")
    c.add_argument("--beam", type=int, default=5)
    c.add_argument("--summarizer", choices=["bart", "none"], default="bart")
    c.add_argument("--summary-max", type=int, default=8)
    c.add_argument("--timeout", type=int, default=0, help="Hard wall-clock timeout per file (seconds). 0=off")
    c.add_argument("--retries", type=int, default=2, help="Retries per file on error/timeout")
    c.add_argument("--progress-timeout", type=int, default=180, help="Abort if no audio progress for N seconds")

    # Worker mode (internal)
    w = sub.add_parser("single", help=argparse.SUPPRESS)
    w.add_argument("--input-file", required=True)
    w.add_argument("--output-root", required=True)
    w.add_argument("--model", required=True)
    w.add_argument("--compute-type", required=True)
    w.add_argument("--language", required=True)
    w.add_argument("--beam", type=int, required=True)
    w.add_argument("--summarizer", choices=["bart", "none"], required=True)
    w.add_argument("--summary-max", type=int, required=True)
    w.add_argument("--progress-timeout", type=int, required=True)

    return ap

def main():
    ap = build_parser()
    args = ap.parse_args()
    if args.mode == "single":
        sys.exit(worker(args))
    else:
        controller(args)

if __name__ == "__main__":
    main()