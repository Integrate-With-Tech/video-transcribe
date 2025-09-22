#!/bin/bash

# Example script for basic video transcription
# Usage: ./examples/basic_transcription.sh

echo "🎬 Basic Video Transcription Example"
echo "======================================"

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg is not installed. Please install it first:"
    echo "   macOS: brew install ffmpeg"
    echo "   Ubuntu: sudo apt install ffmpeg"
    exit 1
fi

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create input directory if it doesn't exist
mkdir -p input_mp4

# Check if there are any MP4 files
if [ ! "$(ls -A input_mp4/*.mp4 2>/dev/null)" ]; then
    echo "📁 No MP4 files found in input_mp4/"
    echo "   Please add some MP4 files to the input_mp4/ directory"
    echo "   Example: cp /path/to/your/video.mp4 input_mp4/"
    exit 1
fi

# Run transcription with basic settings
echo "🚀 Starting transcription with basic settings..."
python transcribe_batch.py run \
    --input input_mp4 \
    --output outputs \
    --model large-v3 \
    --language auto \
    --compute-type int8 \
    --beam 5 \
    --summarizer bart \
    --summary-max 8 \
    --timeout 3600 \
    --retries 2 \
    --progress-timeout 180

echo "✅ Transcription complete!"
echo "📄 Check the outputs/ directory for results"