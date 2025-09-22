# Installation Guide for Video Transcription Tool

## Quick Install

```bash
# Clone the repository
git clone <repository-url>
cd video-transcribe

# Install the package globally
pip install -e .

# Now you can use the global command:
video-transcribe --help
```

## Development Install

```bash
# Install with development dependencies
pip install -e .[dev]

# Or install from PyPI (when available)
pip install video-transcription-tool
```

## System Requirements

### Prerequisites
- Python 3.8 or higher
- FFmpeg (for audio processing)

### Install FFmpeg

**macOS (using Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html or use chocolatey:
```bash
choco install ffmpeg
```

## Usage After Installation

Once installed, you can use the global `video-transcribe` command:

### Interactive Setup
```bash
video-transcribe --interactive
```

### Quick Processing
```bash
video-transcribe run --quick --input input_mp4 --output outputs
```

### Single File Processing
```bash
video-transcribe file --input myvideo.mp4 --output results/
```

### Browse for Files
```bash
video-transcribe file --browse
```

### Configuration Management
```bash
# Show current settings
video-transcribe --show-config

# Reset to defaults
video-transcribe --reset-config

# Check dependencies
video-transcribe --check-deps
```

## Available Commands

| Command | Description |
|---------|-------------|
| `video-transcribe --help` | Show full help |
| `video-transcribe --interactive` | Interactive setup wizard |
| `video-transcribe run` | Batch process directory of videos |
| `video-transcribe file` | Process single video file |
| `video-transcribe --check-deps` | Validate system dependencies |
| `video-transcribe --show-config` | Display current configuration |

## Troubleshooting

### Command not found
If `video-transcribe` command is not found after installation:
```bash
# Reinstall with pip
pip uninstall video-transcription-tool
pip install -e .

# Check if pip scripts directory is in PATH
python -m site --user-base
```

### Permission errors
On some systems you might need:
```bash
pip install --user -e .
```

### Virtual environment install
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```