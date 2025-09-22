"""
Basic tests for transcribe_batch.py functions
"""
import unittest
from pathlib import Path
import tempfile
import os
import sys

# Add the parent directory to the Python path so we can import transcribe_batch
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transcribe_batch import srt_timestamp, outputs_present, ensure_dirs


class TestTranscribeBatch(unittest.TestCase):
    
    def test_srt_timestamp_formatting(self):
        """Test SRT timestamp formatting function"""
        # Test basic formatting
        self.assertEqual(srt_timestamp(0.0), "00:00:00,000")
        self.assertEqual(srt_timestamp(1.5), "00:00:01,500")
        self.assertEqual(srt_timestamp(61.123), "00:01:01,123")
        self.assertEqual(srt_timestamp(3661.456), "01:01:01,456")
        
        # Test edge cases
        self.assertEqual(srt_timestamp(0.999), "00:00:00,999")
        self.assertEqual(srt_timestamp(7322.1), "02:02:02,100")

    def test_outputs_present(self):
        """Test output file detection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "test_output"
            
            # Should return False when directory doesn't exist
            self.assertFalse(outputs_present(output_dir))
            
            # Create directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Should return False when files don't exist
            self.assertFalse(outputs_present(output_dir))
            
            # Create only transcript.txt
            (output_dir / "transcript.txt").write_text("test")
            self.assertFalse(outputs_present(output_dir))
            
            # Create both required files
            (output_dir / "summary.md").write_text("test")
            self.assertTrue(outputs_present(output_dir))

    def test_ensure_dirs(self):
        """Test directory creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "nested" / "test" / "directory"
            
            # Directory shouldn't exist initially
            self.assertFalse(test_dir.exists())
            
            # ensure_dirs should create it
            ensure_dirs(test_dir)
            self.assertTrue(test_dir.exists())
            self.assertTrue(test_dir.is_dir())
            
            # Should not raise error if directory already exists
            ensure_dirs(test_dir)
            self.assertTrue(test_dir.exists())


if __name__ == "__main__":
    unittest.main()