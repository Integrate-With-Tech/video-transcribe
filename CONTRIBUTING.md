# Contributing to Video Transcription Tool

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## 🚀 Getting Started

### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/sejalsheth/integrate-with-tech.git
   cd integrate-with-tech/Video-Transcribing
   ```

2. **Set up development environment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements-dev.txt
   ```

3. **Install system dependencies**:
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt install ffmpeg
   ```

4. **Run tests to verify setup**:
   ```bash
   pytest tests/
   ```

## 🛠️ Development Workflow

### Before Making Changes

1. **Create a new branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Run the test suite**:
   ```bash
   pytest tests/ -v
   ```

### Code Standards

- **Code Formatting**: Use `black` for code formatting
  ```bash
  black .
  ```

- **Linting**: Use `flake8` for linting
  ```bash
  flake8 . --max-line-length=127
  ```

- **Type Hints**: Add type hints where appropriate, check with `mypy`
  ```bash
  mypy transcribe_batch.py --ignore-missing-imports
  ```

### Making Changes

1. **Write tests** for new functionality
2. **Update documentation** if needed
3. **Follow existing code patterns**
4. **Add docstrings** to new functions

### Testing

- **Run all tests**: `pytest tests/`
- **Run with coverage**: `pytest tests/ --cov=. --cov-report=term`
- **Test specific file**: `pytest tests/test_specific.py`

## 📝 Contribution Types

### 🐛 Bug Reports

When reporting bugs, please include:
- **OS and Python version**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Error messages/logs**
- **Sample files** (if applicable)

### ✨ Feature Requests

For new features, please:
- **Describe the use case**
- **Explain expected behavior**
- **Consider backward compatibility**
- **Discuss implementation approach**

### 🔧 Code Contributions

**Good first contributions**:
- Bug fixes
- Documentation improvements
- Adding tests
- Performance optimizations
- New output formats
- Additional language support

**Areas for improvement**:
- Better error handling
- GPU acceleration
- Batch size optimization
- Progress indicators
- Configuration file support
- Web interface

## 🎯 Pull Request Process

### Before Submitting

1. **Ensure tests pass**:
   ```bash
   pytest tests/
   ```

2. **Check code quality**:
   ```bash
   black --check .
   flake8 .
   ```

3. **Update documentation** if needed
4. **Add entry to CHANGELOG.md**

### PR Guidelines

- **Clear title** describing the change
- **Detailed description** of what and why
- **Link related issues** using `Fixes #123`
- **Include screenshots** for UI changes
- **Test instructions** for reviewers

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## 🏗️ Project Structure

```
Video-Transcribing/
├── transcribe_batch.py     # Main script
├── tests/                  # Unit tests
├── input_mp4/             # Input videos (gitignored)
├── outputs/               # Generated outputs (gitignored)
├── requirements.txt       # Dependencies
├── requirements-dev.txt   # Dev dependencies
└── .github/workflows/     # CI/CD
```

## 🔒 Security

- **Report security issues** privately to the maintainers
- **Don't commit sensitive data** (API keys, credentials)
- **Follow secure coding practices**

## 📞 Getting Help

- **Create an issue** for questions
- **Check existing issues** first
- **Provide context** and details
- **Be respectful** and patient

## 📄 Licensing Note

This project uses a **Custom License**:
- ✅ **Personal use** is free and encouraged
- ❌ **Commercial use** requires permission and licensing
- All contributions become part of this licensing model
- Contributors agree that their contributions may be used under commercial licenses by the project owner

## 🏷️ Release Process

1. Update version in `setup.py`/`pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release tag
4. GitHub Actions handles publishing

## 📋 Code of Conduct

- **Be respectful** and inclusive
- **Welcome newcomers** and help them learn
- **Focus on constructive feedback**
- **Maintain professional communication**

## 🎉 Recognition

Contributors will be:
- Added to the README contributors section
- Mentioned in release notes
- Credited in significant feature additions

Thank you for contributing! 🚀