"""
🎥 Video Transcription Console Tool
Batch transcribe MP4 files with OpenAI Whisper + Facebook BART AI Summary

✨ Features:
- 🚀 High-quality transcription using Whisper large-v3 model
- 🤖 AI-powered summarization with Facebook BART
- 📁 Batch processing with smart resume capability  
- 🔄 Robust error handling and automatic retries
- 📊 Real-time progress tracking and feedback
- 🎯 Multiple output formats (SRT, VTT, TXT, MD)

🛠️  Quick Setup:
  brew install ffmpeg                    # Install FFmpeg
  pip install faster-whisper transformers torch sentencepiece

🚀 Usage Examples:
  video-transcribe --help               # Show detailed help
  video-transcribe --interactive        # Interactive setup wizard
  video-transcribe run --quick          # Quick start with defaults
  
  # Advanced batch processing:
  video-transcribe run \\
    --input input_mp4 \\
    --output outputs \\
    --model large-v3 \\
    --language en
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Console styling
class Colors:
    """ANSI color codes for console output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    
    @staticmethod
    def disable():
        """Disable colors for environments that don't support them"""
        Colors.HEADER = Colors.BLUE = Colors.CYAN = ''
        Colors.GREEN = Colors.YELLOW = Colors.RED = ''
        Colors.BOLD = Colors.UNDERLINE = Colors.END = ''

# Auto-detect color support
if not sys.stdout.isatty() or os.getenv('NO_COLOR'):
    Colors.disable()

def print_banner():
    """Print a nice banner for the application"""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔════════════════════════════════════════════════════════════════╗
║                   🎥 Video Transcription Tool                  ║
║                 AI-Powered Speech-to-Text + Summary            ║
╚════════════════════════════════════════════════════════════════╝
{Colors.END}
{Colors.BLUE}Powered by OpenAI Whisper + Facebook BART{Colors.END}
"""
    print(banner)

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

def create_progress_bar(current: int, total: int, width: int = 30) -> str:
    """Create a simple progress bar"""
    if total == 0:
        return "[" + "?" * width + "]"
    
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    percentage = int(100 * current / total)
    return f"[{bar}] {percentage:3d}%"

def transcribe_with_feedback(model, media_path: Path, language: str, beam_size: int, progress_timeout: int):
    """
    Enhanced transcription with visual progress feedback.
    Streams segments and prints progress with time estimates.
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
    start_time = time.time()
    
    # Try to get total duration for better progress tracking
    total_duration = getattr(info, 'duration', None)

    for seg in seg_iter:
        text = seg.text.strip()
        segments.append((seg.start, seg.end, text))
        parts.append(text)

        # Enhanced progress print every ~10s of audio
        bucket = int(seg.end) // 10
        if bucket != last_printed_bucket:
            elapsed = time.time() - start_time
            current_pos = int(seg.end)
            
            # Create progress display
            if total_duration and total_duration > 0:
                progress_bar = create_progress_bar(current_pos, int(total_duration))
                eta_seconds = (elapsed / current_pos) * (total_duration - current_pos) if current_pos > 0 else 0
                eta_str = f" | ETA: {int(eta_seconds)}s" if eta_seconds > 0 else ""
                print(f"    🎵 {progress_bar} {current_pos}s/{int(total_duration)}s{eta_str}", flush=True)
            else:
                # Fallback when duration unknown
                print(f"    🎵 Processed: {current_pos}s | Elapsed: {int(elapsed)}s", flush=True)
            
            last_printed_bucket = bucket

        # Update progress tracking
        if seg.end > last_audio_s + 0.5:
            last_audio_s = seg.end
            last_wall = time.time()

        # Watchdog: no progress for too long
        if progress_timeout > 0 and (time.time() - last_wall) > progress_timeout:
            print(f"    ⚠️  No progress for {progress_timeout}s - aborting", flush=True)
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
    """Enhanced worker with better progress feedback"""
    vid = Path(args.input_file)
    stem = re.sub(r"[^A-Za-z0-9._-]", "_", vid.stem)
    out_dir = Path(args.output_root) / stem
    ensure_dirs(out_dir)

    if outputs_present(out_dir):
        return 0  # Skip message handled by controller

    try:
        # Load model with feedback
        print(f"    🤖 Loading {args.model} model...", flush=True)
        model = load_whisper(args.model, args.compute_type)
        
        print(f"    🎵 Transcribing audio...", flush=True)
        segments, full_text, info = transcribe_with_feedback(
            model,
            vid,
            language=args.language,
            beam_size=args.beam,
            progress_timeout=args.progress_timeout,
        )
        
        # Show transcription results
        duration = info.duration if hasattr(info, 'duration') else 0
        detected_lang = info.language if hasattr(info, 'language') else 'unknown'
        print(f"    📊 Audio: {duration:.1f}s | Language: {detected_lang} | Segments: {len(segments)}", flush=True)
        
        # Generate summary if enabled
        if args.summarizer == "bart":
            print(f"    🧠 Generating AI summary...", flush=True)
        
        # Write all output files
        print(f"    💾 Writing output files...", flush=True)
        write_artifacts(
            out_dir=out_dir,
            segments=segments,
            full_text=full_text,
            stem=stem,
            do_summary=(args.summarizer == "bart"),
            summary_max=args.summary_max,
        )
        
        # Success feedback
        word_count = len(full_text.split())
        print(f"    ✨ Generated {word_count} words in {len(segments)} segments", flush=True)
        
        return 0
        
    except RuntimeError as e:
        if "progress-timeout" in str(e):
            print(f"    ⏰ Timeout: No progress for {args.progress_timeout}s", flush=True)
            return 98
        else:
            print(f"    💥 Runtime error: {e}", flush=True)
            return 99
    except Exception as e:
        print(f"    ❌ Unexpected error: {e}", flush=True)
        return 99

# --------------------------- controller ---------------------------

def print_summary_stats(total: int, done: int, skipped: int, failed: int):
    """Print a nicely formatted summary of processing results"""
    success_rate = (done / total * 100) if total > 0 else 0
    
    print(f"\n{Colors.BOLD}📊 Processing Summary{Colors.END}")
    print("═" * 50)
    print(f"{Colors.GREEN}✅ Completed:{Colors.END}    {done:3d} files")
    print(f"{Colors.YELLOW}⏭️  Skipped:{Colors.END}      {skipped:3d} files (already done)")
    print(f"{Colors.RED}❌ Failed:{Colors.END}       {failed:3d} files")
    print("─" * 50)
    print(f"{Colors.BOLD}📈 Total:{Colors.END}        {total:3d} files")
    print(f"{Colors.BOLD}🎯 Success Rate:{Colors.END} {success_rate:5.1f}%")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All files processed successfully!{Colors.END}")
    elif failed > 0:
        print(f"\n{Colors.YELLOW}⚠️  Some files failed - check error messages above{Colors.END}")

def controller(args):
    """Enhanced controller with better visual feedback and error handling"""
    
    # Print startup info
    print_banner()
    
    in_dir = Path(args.input)
    out_root = Path(args.output)
    
    # Validate input directory
    if not in_dir.exists():
        print(f"{Colors.RED}❌ Error: Input directory not found: {in_dir.resolve()}{Colors.END}")
        return
    
    out_root.mkdir(parents=True, exist_ok=True)
    
    # Find video files
    print(f"\n{Colors.BLUE}🔍 Scanning for MP4 files in: {Colors.BOLD}{in_dir.resolve()}{Colors.END}")
    all_files = sorted(in_dir.glob("*.mp4"))
    
    if not all_files:
        print(f"{Colors.YELLOW}⚠️  No .mp4 files found in {in_dir.resolve()}{Colors.END}")
        print(f"{Colors.CYAN}💡 Make sure your video files are in .mp4 format and in the correct directory{Colors.END}")
        return

    # File selection
    if hasattr(args, 'select') and args.select:
        files = select_files_interactive(in_dir)
        if not files:
            print(f"{Colors.YELLOW}⚠️  No files selected for processing{Colors.END}")
            return
    else:
        files = all_files

    total = len(files)
    done = 0
    skipped = 0 
    failed = 0
    
    # Print processing info
    print(f"{Colors.GREEN}✅ Found {total} MP4 files{Colors.END}")
    print(f"{Colors.BLUE}📁 Output directory: {Colors.BOLD}{out_root.resolve()}{Colors.END}")
    print(f"{Colors.BLUE}🤖 Model: {Colors.BOLD}{args.model}{Colors.END} | Language: {Colors.BOLD}{args.language}{Colors.END}")
    print("\n" + "═" * 70)
    print(f"{Colors.BOLD}🚀 Starting batch processing...{Colors.END}")
    print("═" * 70)

    start_time = time.time()
    
    for idx, vid in enumerate(files, 1):
        stem = re.sub(r"[^A-Za-z0-9._-]", "_", vid.stem)
        out_dir = out_root / stem
        
        # Progress header
        progress = f"[{idx:2d}/{total}]"
        file_size = vid.stat().st_size / (1024 * 1024)  # MB
        
        print(f"\n{Colors.CYAN}{progress}{Colors.END} {Colors.BOLD}{vid.name}{Colors.END} ({file_size:.1f} MB)")

        if outputs_present(out_dir):
            print(f"         {Colors.YELLOW}⏭️  SKIP - Already processed{Colors.END}")
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
        file_start_time = time.time()
        
        while attempt <= tries:
            if attempt > 1:
                print(f"         {Colors.YELLOW}🔄 Retry {attempt}/{tries}{Colors.END}")
            
            try:
                subprocess.run(
                    cmd,
                    check=True,
                    timeout=args.timeout if args.timeout > 0 else None,
                )
                file_duration = time.time() - file_start_time
                print(f"         {Colors.GREEN}✅ DONE in {file_duration:.1f}s{Colors.END}")
                done += 1
                break
                
            except subprocess.TimeoutExpired:
                print(f"         {Colors.RED}⏰ TIMEOUT after {args.timeout}s{Colors.END}")
            except subprocess.CalledProcessError as e:
                print(f"         {Colors.RED}❌ ERROR (exit code {e.returncode}){Colors.END}")
                
            attempt += 1
            if attempt <= tries:
                time.sleep(3)
            else:
                print(f"         {Colors.RED}💥 FAILED after {tries} attempts{Colors.END}")
                failed += 1

    # Final summary
    total_duration = time.time() - start_time
    print("\n" + "═" * 70)
    print_summary_stats(total, done, skipped, failed)
    print(f"\n{Colors.BLUE}⏱️  Total processing time: {total_duration/60:.1f} minutes{Colors.END}")
    print("═" * 70)

def process_single_file(args):
    """Process a single video file"""
    print_banner()
    
    # Handle file browsing
    if hasattr(args, 'browse') and args.browse:
        file_path = browse_for_file()
        if not file_path:
            print(f"{Colors.YELLOW}❌ No file selected{Colors.END}")
            return
        args.input = file_path
    
    # Validate input file
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"{Colors.RED}❌ File not found: {input_file}{Colors.END}")
        return
    
    if not input_file.suffix.lower() == '.mp4':
        print(f"{Colors.YELLOW}⚠️  Warning: File is not .mp4 format. Proceeding anyway...{Colors.END}")
    
    # Determine output directory
    if hasattr(args, 'output') and args.output:
        output_root = Path(args.output)
    else:
        output_root = input_file.parent / "outputs"
    
    output_root.mkdir(parents=True, exist_ok=True)
    
    # Apply presets
    apply_preset(args)
    
    # Show processing info
    file_size = input_file.stat().st_size / (1024 * 1024)
    print(f"\n{Colors.BLUE}📋 Processing Information{Colors.END}")
    print(f"📁 Input file:  {Colors.BOLD}{input_file.name}{Colors.END} ({file_size:.1f} MB)")
    print(f"📂 Output dir:  {Colors.BOLD}{output_root.resolve()}{Colors.END}")
    print(f"🤖 Model:       {Colors.BOLD}{args.model}{Colors.END}")
    print(f"🗣️  Language:    {Colors.BOLD}{args.language}{Colors.END}")
    print(f"🧠 Summary:     {Colors.BOLD}{'Yes' if args.summarizer == 'bart' else 'No'}{Colors.END}")
    
    # Create worker args
    stem = re.sub(r"[^A-Za-z0-9._-]", "_", input_file.stem)
    out_dir = output_root / stem
    
    if outputs_present(out_dir):
        print(f"\n{Colors.YELLOW}⏭️  File already processed. Outputs exist in: {out_dir}{Colors.END}")
        overwrite = input(f"Overwrite existing outputs? [y/N]: ").strip().lower()
        if overwrite != 'y':
            print(f"{Colors.BLUE}✋ Skipping file{Colors.END}")
            return
    
    # Create single file worker args structure
    class SingleFileArgs:
        def __init__(self):
            self.input_file = str(input_file)
            self.output_root = str(output_root)
            self.model = args.model
            self.compute_type = args.compute_type
            self.language = args.language
            self.beam = args.beam
            self.summarizer = args.summarizer if not (hasattr(args, 'no_summary') and args.no_summary) else "none"
            self.summary_max = args.summary_max
            self.progress_timeout = 180  # Default
    
    worker_args = SingleFileArgs()
    
    print(f"\n{Colors.GREEN}🚀 Starting transcription...{Colors.END}")
    start_time = time.time()
    
    try:
        result = worker(worker_args)
        duration = time.time() - start_time
        
        if result == 0:
            print(f"\n{Colors.GREEN}✅ Processing completed successfully in {duration/60:.1f} minutes!{Colors.END}")
            print(f"📁 Outputs saved to: {Colors.BOLD}{out_dir}{Colors.END}")
            
            # Show output files
            print(f"\n{Colors.BLUE}📋 Generated files:{Colors.END}")
            output_files = ["transcript.txt", "captions.srt", "captions.vtt", "full.txt", "summary.md"]
            for filename in output_files:
                filepath = out_dir / filename
                if filepath.exists():
                    file_size = filepath.stat().st_size
                    print(f"  ✅ {filename} ({file_size:,} bytes)")
                else:
                    print(f"  ❌ {filename} (missing)")
        else:
            print(f"\n{Colors.RED}❌ Processing failed with exit code {result}{Colors.END}")
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Processing interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}💥 Unexpected error: {e}{Colors.END}")

# --------------------------- config management ---------------------------

def get_config_path() -> Path:
    """Get the path to the user configuration file"""
    # Use XDG Base Directory specification on Unix-like systems
    if os.name == 'posix':
        config_dir = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    else:
        config_dir = os.getenv('APPDATA', os.path.expanduser('~'))
    
    config_path = Path(config_dir) / 'video-transcribe' / 'config.json'
    return config_path

def load_config() -> Dict:
    """Load configuration from file"""
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def save_config(config: Dict) -> None:
    """Save configuration to file"""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"{Colors.GREEN}💾 Configuration saved to {config_path}{Colors.END}")
    except IOError as e:
        print(f"{Colors.YELLOW}⚠️  Could not save config: {e}{Colors.END}")

def show_config() -> None:
    """Display current configuration"""
    config = load_config()
    config_path = get_config_path()
    
    print(f"\n{Colors.BOLD}⚙️  Current Configuration{Colors.END}")
    print(f"📄 Config file: {config_path}")
    
    if not config:
        print(f"{Colors.YELLOW}No saved configuration found{Colors.END}")
        return
    
    print("\nSaved settings:")
    for key, value in config.items():
        print(f"  {key}: {value}")

# --------------------------- file selection ---------------------------

def browse_for_file() -> Optional[str]:
    """Interactive file browser for selecting input video"""
    print(f"\n{Colors.BOLD}📁 File Browser{Colors.END}")
    
    current_dir = Path.cwd()
    
    while True:
        print(f"\n📍 Current directory: {Colors.BOLD}{current_dir}{Colors.END}")
        
        # List video files and directories
        items = []
        
        # Add parent directory option if not at root
        if current_dir.parent != current_dir:
            items.append(("📁 ..", current_dir.parent, "directory"))
        
        # Add subdirectories
        try:
            for item in sorted(current_dir.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    items.append((f"📁 {item.name}/", item, "directory"))
                elif item.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
                    size_mb = item.stat().st_size / (1024 * 1024)
                    items.append((f"🎥 {item.name} ({size_mb:.1f} MB)", item, "video"))
        except PermissionError:
            print(f"{Colors.RED}❌ Permission denied accessing this directory{Colors.END}")
            return None
        
        if not items:
            print(f"{Colors.YELLOW}No directories or video files found{Colors.END}")
        else:
            print("\nAvailable items:")
            for i, (display, path, item_type) in enumerate(items, 1):
                print(f"  {i}. {display}")
        
        print(f"\nOptions:")
        print(f"  Enter number to select")
        print(f"  'q' to quit")
        print(f"  'd' to enter directory path directly")
        
        choice = input(f"\nChoice: ").strip().lower()
        
        if choice == 'q':
            return None
        elif choice == 'd':
            path_input = input("Enter directory path: ").strip()
            try:
                new_dir = Path(path_input).resolve()
                if new_dir.exists() and new_dir.is_dir():
                    current_dir = new_dir
                else:
                    print(f"{Colors.RED}❌ Invalid directory path{Colors.END}")
            except Exception:
                print(f"{Colors.RED}❌ Invalid path{Colors.END}")
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    display, path, item_type = items[idx]
                    if item_type == "directory":
                        current_dir = path
                    else:  # video file
                        return str(path)
                else:
                    print(f"{Colors.RED}❌ Invalid choice{Colors.END}")
            except ValueError:
                print(f"{Colors.RED}❌ Please enter a number or 'q' to quit{Colors.END}")

def select_files_interactive(input_dir: Path) -> List[Path]:
    """Interactive file selection from input directory"""
    print(f"\n{Colors.BOLD}📋 File Selection{Colors.END}")
    
    files = sorted(input_dir.glob("*.mp4"))
    if not files:
        print(f"{Colors.YELLOW}No MP4 files found in {input_dir}{Colors.END}")
        return []
    
    print(f"\nFound {len(files)} MP4 files:")
    selected = [False] * len(files)
    
    while True:
        print(f"\n📁 Files in {Colors.BOLD}{input_dir.name}{Colors.END}:")
        for i, file in enumerate(files):
            status = "✅" if selected[i] else "⬜"
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"  {i+1:2d}. {status} {file.name} ({size_mb:.1f} MB)")
        
        selected_count = sum(selected)
        print(f"\n📊 Selected: {selected_count}/{len(files)} files")
        print(f"\nOptions:")
        print(f"  Enter numbers (e.g., '1 3 5-7') to toggle selection")
        print(f"  'a' to select all")
        print(f"  'n' to select none") 
        print(f"  'done' to proceed with selected files")
        print(f"  'q' to quit")
        
        choice = input(f"\nChoice: ").strip().lower()
        
        if choice == 'q':
            return []
        elif choice == 'done':
            selected_files = [files[i] for i in range(len(files)) if selected[i]]
            if not selected_files:
                print(f"{Colors.YELLOW}⚠️  No files selected{Colors.END}")
                continue
            return selected_files
        elif choice == 'a':
            selected = [True] * len(files)
        elif choice == 'n':
            selected = [False] * len(files)
        else:
            # Parse number ranges like "1 3 5-7"
            try:
                for part in choice.split():
                    if '-' in part:
                        start, end = part.split('-', 1)
                        start_idx = max(0, min(len(files) - 1, int(start) - 1))
                        end_idx = max(0, min(len(files) - 1, int(end) - 1))
                        for idx in range(min(start_idx, end_idx), max(start_idx, end_idx) + 1):
                            selected[idx] = not selected[idx]
                    else:
                        idx = int(part) - 1
                        if 0 <= idx < len(files):
                            selected[idx] = not selected[idx]
            except ValueError:
                print(f"{Colors.RED}❌ Invalid input. Use numbers, ranges (1-5), or commands{Colors.END}")

# --------------------------- interactive setup ---------------------------

def interactive_setup() -> Dict:
    """Interactive wizard to set up transcription parameters"""
    print_banner()
    
    print(f"\n{Colors.BOLD}🧙‍♂️ Interactive Setup Wizard{Colors.END}")
    print("Let's configure your video transcription settings...\n")
    
    # Load existing config as defaults
    saved_config = load_config()
    
    config = {}
    
    # Input directory
    while True:
        default_input = saved_config.get("input", "./input_mp4")
        prompt = f"📁 Input directory [{default_input}]: "
        config["input"] = input(prompt).strip() or default_input
        if Path(config["input"]).exists():
            break
        print(f"{Colors.RED}❌ Directory not found. Please enter a valid path.{Colors.END}")
    
    # Output directory  
    default_output = saved_config.get("output", "./outputs")
    prompt = f"📂 Output directory [{default_output}]: "
    config["output"] = input(prompt).strip() or default_output
    
    # Model selection
    models = {
        "1": ("tiny", "Fastest, least accurate (~39 MB)"),
        "2": ("base", "Fast, good for real-time (~74 MB)"),
        "3": ("small", "Balanced speed/accuracy (~244 MB)"),
        "4": ("medium", "Good accuracy (~769 MB)"),
        "5": ("large-v3", "Best accuracy, slower (~1550 MB)")
    }
    
    # Find default model choice
    saved_model = saved_config.get("model", "large-v3")
    model_to_num = {v[0]: k for k, v in models.items()}
    default_choice = model_to_num.get(saved_model, "5")
    
    print(f"\n🤖 {Colors.BOLD}Select Whisper Model:{Colors.END}")
    for key, (name, desc) in models.items():
        marker = " (current)" if name == saved_model else ""
        print(f"  {key}. {Colors.BOLD}{name}{Colors.END} - {desc}{marker}")
    
    while True:
        choice = input(f"\nEnter choice [{default_choice}]: ").strip() or default_choice
        if choice in models:
            config["model"] = models[choice][0]
            break
        print(f"{Colors.RED}❌ Invalid choice. Please enter 1-5.{Colors.END}")
    
    # Language
    saved_language = saved_config.get("language", "auto")
    print(f"\n🗣️  {Colors.BOLD}Language Detection:{Colors.END}")
    print("  1. Auto-detect (recommended)")
    print("  2. English (en)")
    print("  3. Spanish (es)")
    print("  4. French (fr)")
    print("  5. Other (specify code)")
    
    # Determine default based on saved config
    lang_map = {"auto": "1", "en": "2", "es": "3", "fr": "4"}
    default_lang_choice = lang_map.get(saved_language, "5" if saved_language != "auto" else "1")
    
    lang_choice = input(f"\nEnter choice [{default_lang_choice}]: ").strip() or default_lang_choice
    reverse_lang_map = {"1": "auto", "2": "en", "3": "es", "4": "fr"}
    
    if lang_choice in reverse_lang_map:
        config["language"] = reverse_lang_map[lang_choice]
    elif lang_choice == "5":
        default_other = saved_language if saved_language not in reverse_lang_map.values() else ""
        config["language"] = input(f"Enter language code [{default_other}]: ").strip() or default_other
    else:
        config["language"] = "auto"
    
    # AI Summary
    saved_summarizer = saved_config.get("summarizer", "bart")
    default_summary = "Y" if saved_summarizer == "bart" else "n"
    summary_choice = input(f"\n🤖 Generate AI summary? [{default_summary}/n]: ").strip().lower() or default_summary.lower()
    config["summarizer"] = "none" if summary_choice == "n" else "bart"
    
    # Advanced options
    advanced_choice = input(f"\n⚙️  Configure advanced options? [y/N]: ").strip().lower()
    if advanced_choice == "y":
        # Compute type
        print(f"\n💻 {Colors.BOLD}Compute Type:{Colors.END}")
        print("  1. int8 - Balanced (recommended)")
        print("  2. int16 - Better quality, more memory") 
        print("  3. float16 - Best quality (GPU recommended)")
        
        compute_choice = input(f"\nEnter choice [1]: ").strip() or "1"
        compute_map = {"1": "int8", "2": "int16", "3": "float16"}
        config["compute_type"] = compute_map.get(compute_choice, "int8")
        
        # Beam size
        default_beam = saved_config.get("beam", 5)
        beam_input = input(f"\n🎯 Beam size (1-10, higher=more accurate) [{default_beam}]: ").strip()
        try:
            config["beam"] = max(1, min(10, int(beam_input))) if beam_input else default_beam
        except ValueError:
            config["beam"] = default_beam
    else:
        config["compute_type"] = saved_config.get("compute_type", "int8")
        config["beam"] = saved_config.get("beam", 5)
    
    # Ask to save config
    save_choice = input(f"\n💾 Save these settings as defaults? [Y/n]: ").strip().lower()
    if save_choice != "n":
        save_config(config)
    
    print(f"\n{Colors.GREEN}✅ Configuration complete!{Colors.END}")
    print("\nYour settings:")
    print(f"  Input:       {config['input']}")
    print(f"  Output:      {config['output']}")
    print(f"  Model:       {config['model']}")
    print(f"  Language:    {config['language']}")
    print(f"  Summary:     {'Yes' if config['summarizer'] == 'bart' else 'No'}")
    print(f"  Compute:     {config['compute_type']}")
    print(f"  Beam size:   {config['beam']}")
    
    return config

def check_system_requirements():
    """Check system requirements and hardware capabilities"""
    print(f"\n{Colors.BOLD}🖥️  System Requirements Check{Colors.END}")
    print("─" * 50)
    
    import platform
    
    # Python version
    python_version = sys.version_info
    python_ok = python_version >= (3, 8)
    status = f"{Colors.GREEN}✅" if python_ok else f"{Colors.RED}❌"
    print(f"Python: {status} {sys.version.split()[0]} (requires 3.8+){Colors.END}")
    
    # Platform
    platform_name = platform.system()
    print(f"OS:     {Colors.BLUE}ℹ️  {platform_name} {platform.release()}{Colors.END}")
    
    # Try to get system info if psutil is available
    try:
        import psutil
        
        # RAM
        ram_gb = psutil.virtual_memory().total / (1024**3)
        ram_ok = ram_gb >= 4
        status = f"{Colors.GREEN}✅" if ram_ok else f"{Colors.YELLOW}⚠️ "
        print(f"RAM:    {status} {ram_gb:.1f} GB (recommended 4+ GB){Colors.END}")
        
        # Disk space
        try:
            disk_usage = psutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)
            disk_ok = free_gb >= 2
            status = f"{Colors.GREEN}✅" if disk_ok else f"{Colors.YELLOW}⚠️ "
            print(f"Disk:   {status} {free_gb:.1f} GB free (recommended 2+ GB){Colors.END}")
        except (OSError, AttributeError):
            disk_ok = True  # Assume OK if we can't check
            print(f"Disk:   {Colors.BLUE}ℹ️  Unable to check disk space{Colors.END}")
        
        # CPU cores
        try:
            cpu_count = psutil.cpu_count()
            print(f"CPU:    {Colors.BLUE}ℹ️  {cpu_count} cores{Colors.END}")
        except AttributeError:
            print(f"CPU:    {Colors.BLUE}ℹ️  Unable to detect CPU count{Colors.END}")
        
        return python_ok and (ram_ok if 'ram_ok' in locals() else True) and disk_ok
        
    except ImportError:
        print(f"System: {Colors.YELLOW}ℹ️  Install 'psutil' for detailed system info{Colors.END}")
        return python_ok

def validate_dependencies():
    """Enhanced dependency check with detailed feedback"""
    print(f"{Colors.BLUE}🔍 Checking dependencies...{Colors.END}")
    all_good = True
    
    # System requirements
    if not check_system_requirements():
        all_good = False
    
    print(f"\n{Colors.BOLD}📦 Required Software{Colors.END}")
    print("─" * 50)
    
    # Check FFmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, text=True)
        version_line = result.stdout.split('\n')[0]
        print(f"{Colors.GREEN}✅ FFmpeg: {version_line.split()[2]}{Colors.END}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{Colors.RED}❌ FFmpeg not found{Colors.END}")
        print(f"{Colors.YELLOW}💡 Installation instructions:{Colors.END}")
        print(f"   macOS:    brew install ffmpeg")
        print(f"   Ubuntu:   sudo apt install ffmpeg") 
        print(f"   Windows:  Download from https://ffmpeg.org/{Colors.END}")
        all_good = False
    
    # Check Python packages
    print(f"\n{Colors.BOLD}🐍 Python Packages{Colors.END}")
    print("─" * 50)
    
    package_info = [
        ("faster_whisper", "faster-whisper", "Speech recognition engine"),
        ("transformers", "transformers", "AI model framework"),
        ("torch", "torch", "PyTorch neural network library"),
        ("sentencepiece", "sentencepiece", "Text tokenization")
    ]
    
    missing = []
    
    for import_name, install_name, description in package_info:
        try:
            module = __import__(import_name.replace("-", "_"))
            version = getattr(module, '__version__', 'unknown')
            print(f"{Colors.GREEN}✅ {install_name}: {version}{Colors.END}")
        except ImportError:
            missing.append(install_name)
            print(f"{Colors.RED}❌ {install_name}: {description}{Colors.END}")
            all_good = False
    
    if missing:
        print(f"\n{Colors.YELLOW}💡 Install missing packages:{Colors.END}")
        print(f"pip install {' '.join(missing)}")
        print(f"\n{Colors.CYAN}Or install all at once:{Colors.END}")
        print(f"pip install faster-whisper transformers torch sentencepiece")
    
    return all_good

def show_model_info():
    """Display information about available Whisper models"""
    print(f"\n{Colors.BOLD}🤖 Available Whisper Models{Colors.END}")
    print("─" * 80)
    
    models = [
        ("tiny", "~39 MB", "Speed: Very Fast", "Accuracy: Basic", "Use: Quick tests"),
        ("base", "~74 MB", "Speed: Fast", "Accuracy: Good", "Use: Real-time apps"), 
        ("small", "~244 MB", "Speed: Medium", "Accuracy: Better", "Use: Balanced processing"),
        ("medium", "~769 MB", "Speed: Slower", "Accuracy: High", "Use: Quality transcription"),
        ("large-v3", "~1550 MB", "Speed: Slowest", "Accuracy: Best", "Use: Maximum quality")
    ]
    
    for name, size, speed, accuracy, use_case in models:
        print(f"{Colors.BOLD}{name:10}{Colors.END} | {size:8} | {speed:15} | {accuracy:15} | {use_case}")

def show_examples():
    """Show practical usage examples"""
    print(f"\n{Colors.BOLD}📚 Usage Examples{Colors.END}")
    print("─" * 60)
    
    examples = [
        ("🚀 Quick Start (Interactive)", "video-transcribe --interactive"),
        ("📁 Batch Process Directory", "video-transcribe run --input videos/ --output results/"),
        ("🎯 High Quality Mode", "video-transcribe run --quality --input videos/ --output results/"),
        ("⚡ Fast Testing Mode", "video-transcribe run --fast --input videos/ --output results/"),
        ("🔍 Select Files Manually", "video-transcribe run --select --input videos/ --output results/"),
        ("📄 Single File", "video-transcribe file --input myvideo.mp4"),
        ("📂 Browse for File", "video-transcribe file --browse"),
        ("🗣️  Spanish Language", "video-transcribe run --language es --input videos/ --output results/"),
        ("🚫 Skip AI Summary", "video-transcribe run --no-summary --input videos/ --output results/"),
        ("⚙️  Check Dependencies", "video-transcribe --check-deps"),
    ]
    
    for description, command in examples:
        print(f"{Colors.GREEN}{description}{Colors.END}")
        print(f"   {Colors.CYAN}{command}{Colors.END}\n")

def show_comprehensive_help():
    """Show detailed help information"""
    print_banner()
    
    print(f"\n{Colors.BOLD}🎥 Video Transcription Console Tool - Complete Guide{Colors.END}")
    print("=" * 70)
    
    show_model_info()
    show_examples()
    
    print(f"{Colors.BOLD}💡 Pro Tips{Colors.END}")
    print("─" * 60)
    tips = [
        "Use --interactive for first-time setup with guided configuration",
        "Save time with --quick preset for balanced speed/quality",
        "Use --select to choose specific files from a directory", 
        "Check --show-config to see your saved preferences",
        "Run --check-deps before processing to verify setup",
        "Files are automatically skipped if already processed",
        "Use Ctrl+C to safely interrupt processing (progress saved)"
    ]
    
    for tip in tips:
        print(f"• {tip}")
    
    print(f"\n{Colors.BOLD}🔧 Configuration{Colors.END}")
    print("─" * 60)
    print("Configuration is automatically saved in:")
    print(f"• macOS/Linux: ~/.config/video-transcribe/config.json")
    print(f"• Windows: %APPDATA%/video-transcribe/config.json")
    
    print(f"\n{Colors.BOLD}📁 Output Files{Colors.END}")
    print("─" * 60)
    print("Each processed video generates:")
    print("• transcript.txt - Timestamped transcript")
    print("• captions.srt - SRT subtitle file") 
    print("• captions.vtt - WebVTT caption file")
    print("• full.txt - Plain text transcript")
    print("• summary.md - AI-generated summary (if enabled)")
    
    print(f"\n{Colors.GREEN}For more help: {Colors.CYAN}video-transcribe <command> --help{Colors.END}")
    print(f"{Colors.GREEN}Report issues: {Colors.CYAN}https://github.com/sejalsheth/integrate-with-tech/issues{Colors.END}")
    print("=" * 70)

# --------------------------- cli ---------------------------

def build_parser():
    ap = argparse.ArgumentParser(
        prog="video-transcribe",
        description=f"""
{Colors.BOLD}🎥 Video Transcription Console Tool{Colors.END}

AI-powered batch transcription using OpenAI Whisper + Facebook BART summarization.
Converts MP4 videos to accurate text transcripts with optional AI summaries.

{Colors.CYAN}✨ Key Features:{Colors.END}
• High-quality speech-to-text with Whisper large-v3
• AI-powered summarization with Facebook BART  
• Multiple output formats (SRT, VTT, TXT, MD)
• Robust batch processing with resume capability
• Real-time progress tracking and error recovery
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global arguments
    ap.add_argument("--version", action="version", version="Video Transcribe v1.0.0")
    ap.add_argument("--no-color", action="store_true", help="Disable colored output")
    ap.add_argument("--interactive", "-i", action="store_true", help="Run interactive setup wizard")
    ap.add_argument("--check-deps", action="store_true", help="Check system dependencies")
    ap.add_argument("--show-config", action="store_true", help="Show current configuration")
    ap.add_argument("--reset-config", action="store_true", help="Reset configuration to defaults")
    ap.add_argument("--guide", action="store_true", help="Show comprehensive usage guide")
    ap.add_argument("--models", action="store_true", help="Show available Whisper models")
    ap.add_argument("--examples", action="store_true", help="Show usage examples")
    
    sub = ap.add_subparsers(dest="mode", title="Commands")

    # Run command (main batch processing)
    run_cmd = sub.add_parser(
        "run", 
        help="Start batch transcription",
        description=f"{Colors.BOLD}Batch Transcription Mode{Colors.END}\n\nProcess all MP4 files in input directory."
    )
    
    # File command (single file processing)
    file_cmd = sub.add_parser(
        "file",
        help="Process a single video file",
        description=f"{Colors.BOLD}Single File Mode{Colors.END}\n\nTranscribe one specific video file."
    )
    
    # Input/Output for batch mode
    io_group = run_cmd.add_argument_group("📁 Input/Output")
    io_group.add_argument("--input", "-i", required=True, 
                         help="Directory containing MP4 files to process")
    io_group.add_argument("--output", "-o", required=True,
                         help="Directory to save transcription outputs")
    io_group.add_argument("--select", action="store_true",
                         help="Interactively select which files to process")
    
    # Input/Output for single file mode
    file_io_group = file_cmd.add_argument_group("📁 Input/Output")
    file_io_group.add_argument("--input", "-i", required=True,
                              help="Video file to transcribe")
    file_io_group.add_argument("--output", "-o", 
                              help="Output directory (default: same as input file)")
    file_io_group.add_argument("--browse", action="store_true",
                              help="Browse and select input file interactively")
    
    # Quick presets
    preset_group = run_cmd.add_argument_group("🚀 Quick Presets")
    preset_group.add_argument("--quick", action="store_true",
                             help="Quick mode: small model, auto language, summaries enabled")
    preset_group.add_argument("--quality", action="store_true", 
                             help="Quality mode: large-v3 model, slower but most accurate")
    preset_group.add_argument("--fast", action="store_true",
                             help="Fast mode: tiny model, good for testing")
    
    # Model configuration  
    model_group = run_cmd.add_argument_group("🤖 Model Configuration")
    model_group.add_argument("--model", default="large-v3",
                           choices=["tiny", "base", "small", "medium", "large-v3"],
                           help="Whisper model size (default: large-v3)")
    model_group.add_argument("--compute-type", default="int8",
                           choices=["auto", "int8", "int16", "float16", "int8_float16"],
                           help="Computation precision (default: int8)")
    model_group.add_argument("--language", default="auto",
                           help="Language code (en, es, fr, etc.) or 'auto' for detection")
    model_group.add_argument("--beam", type=int, default=5,
                           help="Beam size for decoding (1-10, higher=more accurate)")
    
    # AI features
    ai_group = run_cmd.add_argument_group("🧠 AI Features") 
    ai_group.add_argument("--summarizer", choices=["bart", "none"], default="bart",
                         help="AI summarization method (default: bart)")
    ai_group.add_argument("--summary-max", type=int, default=8,
                         help="Maximum sentences in AI summary")
    ai_group.add_argument("--no-summary", action="store_true",
                         help="Skip AI summary generation")
    
    # Processing options
    proc_group = run_cmd.add_argument_group("⚙️  Processing Options")
    proc_group.add_argument("--timeout", type=int, default=0,
                          help="Per-file timeout in seconds (0=unlimited)")
    proc_group.add_argument("--retries", type=int, default=2,
                          help="Retry attempts for failed files")
    proc_group.add_argument("--progress-timeout", type=int, default=180,
                          help="Abort if no progress for N seconds")
    proc_group.add_argument("--parallel", type=int, default=1,
                          help="Number of files to process in parallel (experimental)")
    
    # Copy model configuration to single file mode
    file_model_group = file_cmd.add_argument_group("🤖 Model Configuration")
    file_model_group.add_argument("--model", default="large-v3",
                                 choices=["tiny", "base", "small", "medium", "large-v3"],
                                 help="Whisper model size (default: large-v3)")
    file_model_group.add_argument("--compute-type", default="int8",
                                 choices=["auto", "int8", "int16", "float16", "int8_float16"],
                                 help="Computation precision (default: int8)")
    file_model_group.add_argument("--language", default="auto",
                                 help="Language code (en, es, fr, etc.) or 'auto' for detection")
    file_model_group.add_argument("--beam", type=int, default=5,
                                 help="Beam size for decoding (1-10, higher=more accurate)")
    
    # Copy AI features to single file mode  
    file_ai_group = file_cmd.add_argument_group("🧠 AI Features")
    file_ai_group.add_argument("--summarizer", choices=["bart", "none"], default="bart",
                              help="AI summarization method (default: bart)")
    file_ai_group.add_argument("--summary-max", type=int, default=8,
                              help="Maximum sentences in AI summary")
    file_ai_group.add_argument("--no-summary", action="store_true",
                              help="Skip AI summary generation")
    
    # Copy presets to single file mode
    file_preset_group = file_cmd.add_argument_group("🚀 Quick Presets")
    file_preset_group.add_argument("--quick", action="store_true",
                                  help="Quick mode: small model, auto language, summaries enabled")
    file_preset_group.add_argument("--quality", action="store_true", 
                                  help="Quality mode: large-v3 model, slower but most accurate")
    file_preset_group.add_argument("--fast", action="store_true",
                                  help="Fast mode: tiny model, good for testing")
    
    # Single file mode (internal)
    single_cmd = sub.add_parser("single", help=argparse.SUPPRESS)
    single_cmd.add_argument("--input-file", required=True)
    single_cmd.add_argument("--output-root", required=True)
    single_cmd.add_argument("--model", required=True)
    single_cmd.add_argument("--compute-type", required=True)
    single_cmd.add_argument("--language", required=True)
    single_cmd.add_argument("--beam", type=int, required=True)
    single_cmd.add_argument("--summarizer", choices=["bart", "none"], required=True)
    single_cmd.add_argument("--summary-max", type=int, required=True)
    single_cmd.add_argument("--progress-timeout", type=int, required=True)

    return ap

def apply_preset(args):
    """Apply quick preset configurations"""
    if hasattr(args, 'quick') and args.quick:
        args.model = "small"
        args.language = "auto" 
        args.summarizer = "bart"
        args.compute_type = "int8"
        print(f"{Colors.GREEN}🚀 Quick mode activated: small model, auto language, summaries enabled{Colors.END}")
    
    elif hasattr(args, 'quality') and args.quality:
        args.model = "large-v3"
        args.language = "auto"
        args.summarizer = "bart"
        args.compute_type = "int8"
        args.beam = 5
        print(f"{Colors.GREEN}🎯 Quality mode activated: large-v3 model, maximum accuracy{Colors.END}")
    
    elif hasattr(args, 'fast') and args.fast:
        args.model = "tiny"
        args.language = "auto"
        args.summarizer = "none"
        args.compute_type = "int8"
        args.beam = 1
        print(f"{Colors.GREEN}⚡ Fast mode activated: tiny model, no summaries{Colors.END}")
    
    if hasattr(args, 'no_summary') and args.no_summary:
        args.summarizer = "none"

def main():
    """Enhanced main function with better UX"""
    ap = build_parser()
    
    # Handle no arguments - show help
    if len(sys.argv) == 1:
        print_banner()
        print(f"\n{Colors.YELLOW}💡 Welcome! Here's how to get started:{Colors.END}\n")
        
        print(f"{Colors.BOLD}🚀 Quick Start:{Colors.END}")
        print(f"  {Colors.CYAN}video-transcribe --interactive{Colors.END}     # Interactive setup wizard")
        print(f"  {Colors.CYAN}video-transcribe --check-deps{Colors.END}      # Verify your system is ready")
        print(f"  {Colors.CYAN}video-transcribe file --browse{Colors.END}     # Browse and select a video file")
        
        print(f"\n{Colors.BOLD}📚 Learning & Help:{Colors.END}")
        print(f"  {Colors.CYAN}video-transcribe --guide{Colors.END}          # Comprehensive usage guide")
        print(f"  {Colors.CYAN}video-transcribe --examples{Colors.END}       # Show practical examples")
        print(f"  {Colors.CYAN}video-transcribe --models{Colors.END}         # Available AI models info")
        print(f"  {Colors.CYAN}video-transcribe --help{Colors.END}           # Full command reference")
        
        print(f"\n{Colors.BOLD}⚙️  Configuration:{Colors.END}")
        print(f"  {Colors.CYAN}video-transcribe --show-config{Colors.END}    # View saved settings")
        print(f"  {Colors.CYAN}video-transcribe --reset-config{Colors.END}   # Reset to defaults")
        
        print(f"\n{Colors.GREEN}💡 Tip: Start with {Colors.BOLD}--interactive{Colors.END}{Colors.GREEN} for guided setup!{Colors.END}")
        sys.exit(0)
    
    args = ap.parse_args()
    
    # Handle color disabling
    if hasattr(args, 'no_color') and args.no_color:
        Colors.disable()
    
    # Handle global options
    if hasattr(args, 'check_deps') and args.check_deps:
        if validate_dependencies():
            print(f"\n{Colors.GREEN}✅ All dependencies satisfied!{Colors.END}")
        else:
            print(f"\n{Colors.RED}❌ Missing dependencies. Please install them first.{Colors.END}")
        sys.exit(0)
    
    if hasattr(args, 'show_config') and args.show_config:
        show_config()
        sys.exit(0)
    
    if hasattr(args, 'reset_config') and args.reset_config:
        config_path = get_config_path()
        if config_path.exists():
            config_path.unlink()
            print(f"{Colors.GREEN}✅ Configuration reset successfully{Colors.END}")
        else:
            print(f"{Colors.YELLOW}ℹ️  No configuration file to reset{Colors.END}")
        sys.exit(0)
    
    if hasattr(args, 'guide') and args.guide:
        show_comprehensive_help()
        sys.exit(0)
        
    if hasattr(args, 'models') and args.models:
        show_model_info()
        sys.exit(0)
        
    if hasattr(args, 'examples') and args.examples:
        show_examples()
        sys.exit(0)
    
    if hasattr(args, 'interactive') and args.interactive:
        if not validate_dependencies():
            print(f"\n{Colors.RED}❌ Please install missing dependencies first.{Colors.END}")
            sys.exit(1)
        
        config = interactive_setup()
        
        # Apply config to args
        args.mode = "run"
        args.input = config["input"]
        args.output = config["output"] 
        args.model = config["model"]
        args.language = config["language"]
        args.summarizer = config["summarizer"]
        # Use defaults for other settings
        args.compute_type = "int8"
        args.beam = 5
        args.timeout = 0
        args.retries = 2
        args.progress_timeout = 180
        args.summary_max = 8
    
    # Handle single file mode (internal)
    if args.mode == "single":
        sys.exit(worker(args))
    
    # Handle run mode
    elif args.mode == "run":
        # Validate dependencies for run mode
        if not hasattr(args, 'interactive') or not args.interactive:
            if not validate_dependencies():
                print(f"\n{Colors.RED}❌ Missing dependencies. Run with --check-deps for details.{Colors.END}")
                sys.exit(1)
        
        # Apply presets
        apply_preset(args)
        
        # Start processing
        try:
            controller(args)
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}⚠️  Processing interrupted by user{Colors.END}")
            print(f"{Colors.CYAN}💡 Partial results saved. You can resume by running again.{Colors.END}")
            sys.exit(1)
        except Exception as e:
            print(f"\n{Colors.RED}💥 Unexpected error: {e}{Colors.END}")
            sys.exit(1)
    
    # Handle single file mode
    elif args.mode == "file":
        # Validate dependencies
        if not validate_dependencies():
            print(f"\n{Colors.RED}❌ Missing dependencies. Run with --check-deps for details.{Colors.END}")
            sys.exit(1)
        
        try:
            process_single_file(args)
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}⚠️  Processing interrupted by user{Colors.END}")
            sys.exit(1)
        except Exception as e:
            print(f"\n{Colors.RED}💥 Unexpected error: {e}{Colors.END}")
            sys.exit(1)
    
    else:
        # Should not reach here with proper argparse setup
        ap.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()