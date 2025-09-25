# MyGPT

An AI Chat Assistant application built with Flask that provides users with a conversational interface to interact with OpenAI's GPT models.

## Features

- User authentication with admin approval system
- Chat history management
- Tag-based organization for chats
- Email notifications
- Multiple chat sessions
- Modern web interface with Bootstrap 5 dark theme
- AI model integration (GPT, Claude, Gemini, etc.)

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL (for production) or SQLite (for development)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Set up environment variables:
   ```bash
   export DATABASE_URL="your_database_url"
   export FLASK_SECRET_KEY="your_secret_key"
   export OPENAI_API_KEY="your_openai_api_key"
   export SENDGRID_API_KEY="your_sendgrid_api_key"
   export VERIFIED_SENDER_EMAIL="your_verified_email"
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## CI/CD Setup

This project uses GitHub Actions for continuous integration. To set up CI/CD:

1. **Configure GitHub Secrets**: See [`CI_SETUP.md`](CI_SETUP.md) for detailed instructions on setting up required secrets.

2. **Required Secrets**:
   - `POSTGRES_PASSWORD` - PostgreSQL database password for testing
   - `FLASK_SECRET_KEY` - Flask application secret key

The CI workflow automatically runs:
- Code formatting checks (Black, isort)
- Linting with flake8
- Test suite with pytest
- Coverage reporting

## Documentation

- [`CODEBASE_REVIEW.md`](CODEBASE_REVIEW.md) - Comprehensive code analysis and recommendations
- [`IMPLEMENTATION_GUIDE.md`](IMPLEMENTATION_GUIDE.md) - Step-by-step implementation guide
- [`TESTING.md`](TESTING.md) - Testing framework documentation
- [`TECHNICAL_DEBT_ANALYSIS.md`](TECHNICAL_DEBT_ANALYSIS.md) - Technical debt analysis and resolution guide
- [`CI_SETUP.md`](CI_SETUP.md) - CI/CD setup instructions

## Architecture

The application follows the MVC pattern with Flask:
- **Routes**: HTTP request handling (`routes.py`)
- **Models**: Database schemas using SQLAlchemy ORM (`models.py`)
- **Services**: Business logic separation (`chat_handler.py`, `email_handler.py`)
- **Configuration**: Application setup (`app.py`)

## Testing

Run tests with:
```bash
pytest --cov=. --cov-report=term-missing
```

Current test coverage: 31.22% (see [`TESTING.md`](TESTING.md) for details)

## Security

- Flask-Login for session management
- CSRF protection with Flask-WTF
- Input validation with Marshmallow schemas
- Secure password hashing
- GitHub Actions secrets for CI/CD

## License

This project is part of a code review and improvement initiative.