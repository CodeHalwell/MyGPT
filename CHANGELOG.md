# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive README.md with setup and usage instructions
- .env.example file for environment variable guidance
- GitHub Actions CI/CD workflow for automated testing and building
- Pre-commit hooks configuration for code quality
- Docker support with Dockerfile and .dockerignore
- requirements.txt for easier deployment
- Comprehensive .gitignore covering all production artifacts
- Documentation organization in docs/ directory

### Changed
- Fixed pyproject.toml packaging configuration
- Organized analysis documents into docs/ directory
- Improved test reliability for environment-appropriate security settings
- Applied consistent code formatting with black and isort
- Enhanced project metadata and classifications

### Fixed
- Fixed failing test for SESSION_COOKIE_SECURE configuration
- Fixed import error in test_chat_handler.py
- Resolved packaging build issues

## [0.1.0] - Initial Release

### Added
- Multi-provider AI chat application supporting OpenAI, Anthropic, Google Gemini, and Mistral
- Flask-based web application with user authentication
- Real-time streaming chat responses
- Admin approval system
- Chat history and tagging functionality
- Comprehensive test suite with 24% coverage
- Production-ready configurations
- Database migration and indexing scripts