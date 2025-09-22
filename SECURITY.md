# Security Policy

## Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### 1. Do NOT create a public issue

Please **do not** report security vulnerabilities through public GitHub issues, discussions, or pull requests.

### 2. Report privately

Send an email to the maintainers with the following information:

- **Subject**: Security Vulnerability Report - Video Transcription Tool
- **Description**: Detailed description of the vulnerability
- **Steps to reproduce**: Clear steps to reproduce the issue
- **Impact**: Potential impact and severity
- **Suggested fix**: If you have suggestions for fixing the issue

### 3. Response Timeline

- **Initial response**: Within 48 hours of receiving the report
- **Status update**: Within 1 week with preliminary analysis
- **Resolution**: Security fixes will be prioritized and released as soon as possible

### 4. Coordinated Disclosure

We follow responsible disclosure practices:

1. We will acknowledge receipt of your vulnerability report
2. We will investigate and validate the issue
3. We will develop and test a fix
4. We will coordinate the release timing with you
5. We will publicly acknowledge your responsible disclosure (unless you prefer to remain anonymous)

## Security Best Practices

When using this tool:

### Input Validation
- Only process video files from trusted sources
- Be cautious with files from unknown origins
- Scan files with antivirus software before processing

### Environment Security
- Use virtual environments to isolate dependencies
- Keep dependencies up to date
- Regularly audit installed packages for vulnerabilities

### Data Privacy
- Be mindful of sensitive content in videos
- Consider local processing for confidential material
- Implement proper access controls for output files
- Clean up temporary files and model caches appropriately

### Network Security
- Model downloads occur over HTTPS
- Verify model checksums when possible
- Use secure networks for downloading models

## Dependencies

This project relies on several external dependencies:

- **faster-whisper**: Speech recognition model
- **transformers**: ML model library
- **torch**: Deep learning framework
- **sentencepiece**: Text processing

We monitor these dependencies for security vulnerabilities and update them regularly.

## Security Features

- **No network communication** during processing (after initial model download)
- **Local processing** - no data sent to external services
- **Sandboxed execution** through subprocess isolation
- **Input validation** for file paths and parameters
- **Timeout protection** against resource exhaustion

## Vulnerability Response

When a security vulnerability is confirmed:

1. **Immediate action**: If critical, we may temporarily disable affected features
2. **Fix development**: Priority development of security patches
3. **Testing**: Thorough testing of security fixes
4. **Release**: Emergency release for critical vulnerabilities
5. **Communication**: Clear communication about the issue and fix

## Security Updates

Security updates are distributed through:

- **GitHub Releases**: Tagged security releases
- **Package managers**: Updated packages on PyPI
- **Notifications**: GitHub security advisories
- **Documentation**: Updated security recommendations

## Hall of Fame

We appreciate researchers and users who help improve our security:

<!-- Security researchers will be listed here with their permission -->

## Contact

For security-related questions or concerns:
- Create a private security issue on GitHub
- Follow our responsible disclosure guidelines

Thank you for helping keep our project and users safe! 🔒