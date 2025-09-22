@echo off
REM Example batch script for Windows users
REM Usage: examples\basic_transcription_windows.bat

echo 🎬 Basic Video Transcription Example (Windows)
echo =============================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org/
    pause
    exit /b 1
)

REM Check if FFmpeg is installed
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo ❌ FFmpeg is not installed or not in PATH
    echo Please install FFmpeg from https://ffmpeg.org/
    echo Or use chocolatey: choco install ffmpeg
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Create input directory if it doesn't exist
if not exist "input_mp4" mkdir input_mp4

REM Check for MP4 files
dir input_mp4\*.mp4 >nul 2>&1
if errorlevel 1 (
    echo 📁 No MP4 files found in input_mp4\
    echo    Please add some MP4 files to the input_mp4\ directory
    echo    Example: copy "C:\path\to\your\video.mp4" input_mp4\
    pause
    exit /b 1
)

REM Run transcription with basic settings
echo 🚀 Starting transcription with basic settings...
python transcribe_batch.py run ^
    --input input_mp4 ^
    --output outputs ^
    --model large-v3 ^
    --language auto ^
    --compute-type int8 ^
    --beam 5 ^
    --summarizer bart ^
    --summary-max 8 ^
    --timeout 3600 ^
    --retries 2 ^
    --progress-timeout 180

echo ✅ Transcription complete!
echo 📄 Check the outputs\ directory for results
pause