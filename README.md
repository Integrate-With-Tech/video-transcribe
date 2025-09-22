# Video Transcription with AI Summary

[![License](https://img.shields.io/badge/License-Custom-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/sejalsheth/integrate-with-tech/actions/workflows/ci.yml/badge.svg)](https://github.com/sejalsheth/integrate-with-tech/actions/workflows/ci.yml)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)](https://github.com/sejalsheth/integrate-with-tech/tree/main/Video-Transcribing)

<p align="center">
  <img alt="Video Transcribe" src="https://img.shields.io/badge/Video%20Transcribe-CLI-blue">
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-green"></a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-informational">
  <img alt="Platforms" src="https://img.shields.io/badge/OS-macOS%20%7C%20Linux-lightgrey">
  <a href="https://github.com/Integrate-With-Tech/video-transcribe/actions/workflows/ci.yml">
    <img alt="CI" src="https://github.com/Integrate-With-Tech/video-transcribe/actions/workflows/ci.yml/badge.svg">
  </a>
  <img alt="Stars" src="https://img.shields.io/github/stars/Integrate-With-Tech/video-transcribe?style=social">
</p>

A robust batch transcription tool that processes MP4 videos using OpenAI's Whisper model (via faster-whisper) and generates AI-powered summaries using Facebook's BART model.

## 🚀 Features

- **Batch Processing**: Process multiple MP4 videos automatically
- **High-Quality Transcription**: Uses OpenAI's Whisper large-v3 model for accurate speech-to-text
- **AI Summarization**: Generates concise summaries using Facebook's BART large CNN model
- **Multiple Output Formats**: Produces transcripts, SRT subtitles, VTT captions, and markdown summaries
- **Robust Error Handling**: Built-in retry logic, timeout protection, and progress monitoring
- **Resume Capability**: Automatically skips already processed files
- **Real-time Feedback**: Clear terminal output showing processing progress

## 📁 Output Structure

For each processed video, the tool creates a folder with the following files:

```
outputs/
└── VideoName/
    ├── transcript.txt    # Timestamped transcript
    ├── captions.srt      # SRT subtitle format
    ├── captions.vtt      # WebVTT caption format
    ├── full.txt          # Plain text transcript
    └── summary.md        # AI-generated summary
```

### Output Examples

**Transcript Format** (`transcript.txt`):
```
[00:00:01,010 - 00:00:07,540] Hello everyone and welcome to today's presentation
[00:00:07,540 - 00:00:12,619] In this video we'll be covering the main topics and key concepts
[00:00:12,619 - 00:00:18,240] Let's start with the first section which discusses the fundamentals
```

**Summary Format** (`summary.md`):
```markdown
# Summary: VideoName

- The presentation covers fundamental concepts and key topics
- Main discussion points include practical applications and examples  
- The video concludes with actionable takeaways for viewers
```

## 🛠️ Installation

### Quick Installation

```bash
# Clone the repository
git clone <repository-url>
cd video-transcribe

# Install as a global console application
pip install -e .

# Verify installation
video-transcribe --version
```

### Prerequisites

The installer will help you check these, but you'll need:

- **Python 3.8+**
- **FFmpeg** (for audio processing)

### System Setup

1. **Install FFmpeg**:
   ```bash
   # macOS (using Homebrew)
   brew install ffmpeg
   
   # Ubuntu/Debian  
   sudo apt update && sudo apt install ffmpeg
   
   # Windows (using Chocolatey)
   choco install ffmpeg
   ```

2. **Python Dependencies** (auto-installed):
   ```bash
   # These are installed automatically with pip install -e .
   pip install faster-whisper transformers sentencepiece torch
   ```

3. **Verify Setup**:
   ```bash
   video-transcribe --check-deps
   ```

## 📖 Usage

This is now a full-featured **console application** with interactive menus, configuration management, and user-friendly commands.

### 🚀 Quick Start (Recommended)

1. **Install the application**:
   ```bash
   pip install -e .
   ```

2. **Interactive setup** (first time):
   ```bash
   video-transcribe --interactive
   ```

3. **Check your system**:
   ```bash
   video-transcribe --check-deps
   ```

4. **Process videos**:
   ```bash
   video-transcribe run --quick --input input_mp4 --output outputs
   ```

### 📱 Available Commands

| Command | Description |
|---------|-------------|
| `video-transcribe --interactive` | 🧙‍♂️ Interactive setup wizard |
| `video-transcribe run` | 📁 Batch process directory |
| `video-transcribe file` | 📄 Process single file |
| `video-transcribe --guide` | 📚 Complete usage guide |
| `video-transcribe --check-deps` | 🔍 Verify dependencies |
| `video-transcribe --show-config` | ⚙️ View settings |

### 🎯 Processing Modes

**Batch Processing:**
```bash
# Quick mode (balanced speed/quality)
video-transcribe run --quick --input videos/ --output results/

# Quality mode (best accuracy)
video-transcribe run --quality --input videos/ --output results/

# Fast mode (for testing)
video-transcribe run --fast --input videos/ --output results/

# Select specific files interactively
video-transcribe run --select --input videos/ --output results/
```

**Single File Processing:**
```bash
# Process one file
video-transcribe file --input myvideo.mp4 --output results/

# Browse and select file interactively
video-transcribe file --browse
```

### 🌍 Language Options

```bash
# Auto-detect language (recommended)
video-transcribe run --language auto --input videos/ --output results/

# Specific languages
video-transcribe run --language en --input videos/ --output results/  # English
video-transcribe run --language es --input videos/ --output results/  # Spanish
video-transcribe run --language fr --input videos/ --output results/  # French
```

### 🤖 Model Selection

```bash
# Available models (size vs accuracy tradeoff)
video-transcribe --models  # Show model information

# Use specific model
video-transcribe run --model tiny --input videos/ --output results/     # Fastest
video-transcribe run --model small --input videos/ --output results/    # Balanced  
video-transcribe run --model large-v3 --input videos/ --output results/ # Best quality
```

### Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | Required | Directory containing MP4 files |
| `--output` | Required | Directory for output files |
| `--model` | `large-v3` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large-v3`) |
| `--language` | `auto` | Language code (`en`, `es`, `fr`, etc.) or `auto` for detection |
| `--compute-type` | `int8` | Computation precision (`auto`, `int8`, `int16`, `float16`) |
| `--beam` | `5` | Beam size for decoding (higher = more accurate, slower) |
| `--timeout` | `0` | Maximum processing time per file in seconds (0 = no limit) |
| `--retries` | `2` | Number of retry attempts for failed files |
| `--progress-timeout` | `180` | Abort if no progress for N seconds |
| `--summarizer` | `bart` | Summarization method (`bart` or `none`) |
| `--summary-max` | `8` | Maximum sentences in summary |

## 🎯 VS Code Integration

The project includes a VS Code launch configuration for easy debugging:

1. Open the project in VS Code
2. Go to **Run and Debug** (Ctrl/Cmd + Shift + D)
3. Select "Transcribe batch" configuration
4. Press F5 to start debugging

## 🔧 Performance Tips

- **Model Selection**: 
  - `tiny`: Fastest, least accurate
  - `base`: Good balance for quick processing
  - `large-v3`: Most accurate, slower (recommended for quality)

- **Compute Type**:
  - `int8`: Good balance of speed and accuracy
  - `int8_float16`: Better accuracy, slightly slower
  - `float16`: Best accuracy on GPU

- **Hardware Requirements**:
  - **CPU**: Works on any modern processor
  - **RAM**: 4GB+ recommended for large-v3 model
  - **GPU**: Optional but significantly speeds up processing

## 🚨 Troubleshooting

### Common Issues

1. **"No module named 'faster_whisper'"**
   ```bash
   pip install faster-whisper
   ```

2. **FFmpeg not found**
   ```bash
   # Ensure FFmpeg is in your PATH
   ffmpeg -version
   ```

3. **Out of memory errors**
   - Use smaller model (`medium` or `small`)
   - Reduce `--beam` size
   - Use `int8` compute type

4. **Process hangs**
   - The tool includes automatic timeout and retry logic
   - Adjust `--progress-timeout` if needed

### Processing Status Messages

- `START`: Processing begins
- `SKIP`: File already processed
- `DONE`: Successfully completed
- `ERROR`: Processing failed
- `TIMEOUT`: Hit time limit
- `RETRY`: Attempting again
- `FAIL`: All retries exhausted

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## 📄 License

**Personal Use License** - This project is free for personal, educational, and non-commercial use.

**Commercial Use Restrictions** - Commercial use requires explicit permission and licensing. 

### ✅ Allowed (Personal Use):
- Personal projects and learning
- Academic research and education
- Non-profit organizations  
- Open source contributions

### ❌ Requires Permission (Commercial Use):
- Business or commercial environments
- Providing transcription services for payment
- Commercial products or services
- Any revenue-generating activities

**For commercial licensing**, contact: integratewithtech@gmail.com

See the [LICENSE](LICENSE) file for complete terms.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) for optimized inference
- [Facebook BART](https://huggingface.co/facebook/bart-large-cnn) for text summarization
- [Transformers](https://huggingface.co/transformers/) library by Hugging Face
