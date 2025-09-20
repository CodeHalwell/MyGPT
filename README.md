# MyGPT - Multi-Provider AI Chat Application

A modern Flask-based AI chat application supporting multiple AI providers including OpenAI, Anthropic Claude, Google Gemini, and Mistral AI.

## Features

- **Multi-Provider Support**: Switch between OpenAI GPT-4, Claude, Gemini, and Mistral models
- **Real-time Streaming**: Server-sent events for real-time response streaming
- **User Management**: Registration, authentication, and admin approval system
- **Chat History**: Persistent chat storage with search and tagging
- **Modern UI**: Responsive Bootstrap 5 dark theme interface
- **Security**: CSRF protection, secure sessions, and input validation

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (for production) or SQLite (for development)
- API keys for desired AI providers

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/CodeHalwell/MyGPT.git
   cd MyGPT
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # or if using pip-tools:
   pip install -e .
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**
   ```bash
   python db_migrate.py
   ```

5. **Run the application**
   ```bash
   # Development
   python main.py
   
   # Production
   gunicorn -w 4 -b 0.0.0.0:8000 main:app
   ```

## Configuration

### Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `FLASK_SECRET_KEY` | Flask session secret key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Optional* |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Optional* |
| `GOOGLE_API_KEY` | Google Gemini API key | Optional* |
| `MISTRAL_API_KEY` | Mistral AI API key | Optional* |
| `SENDGRID_API_KEY` | SendGrid email API key | Optional |
| `VERIFIED_SENDER_EMAIL` | Verified sender email for notifications | Optional |

*At least one AI provider API key is required

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `PORT` | Application port | `8000` |
| `ADMIN_EMAIL` | Default admin email | None |

## Project Structure

```
MyGPT/
├── app.py                          # Flask application factory
├── main.py                         # Application entry point
├── routes.py                       # API routes and handlers
├── models.py                       # Database models
├── schemas.py                      # Input validation schemas
├── chat_handler.py                 # Chat utilities and model mapping
├── multi_provider_chat_handler.py  # Multi-provider AI integration
├── email_handler.py                # Email notification system
├── static/                         # CSS, JS, and static assets
├── templates/                      # Jinja2 HTML templates
├── tests/                          # Test suite
├── docs/                           # Documentation and analysis
└── pyproject.toml                  # Project configuration
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/test_models.py -v
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking (if configured)
mypy .
```

### Database Operations

```bash
# Create database tables
python db_migrate.py

# Add performance indexes
python db_add_indexes.py

# Test database performance
python test_indexes.py
```

## Deployment

### Using Docker (Recommended)

```bash
# Build image
docker build -t mygpt .

# Run container
docker run -p 8000:8000 --env-file .env mygpt
```

### Manual Deployment

1. **Set up production environment**
   ```bash
   pip install -e .
   ```

2. **Configure production database**
   ```bash
   export DATABASE_URL="postgresql://user:pass@host:port/dbname"
   python db_migrate.py
   python db_add_indexes.py
   ```

3. **Run with production server**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 main:app
   # or
   waitress-serve --host=0.0.0.0 --port=8000 main:app
   ```

### Environment-Specific Configuration

- **Development**: Uses SQLite, debug mode enabled
- **Production**: Requires PostgreSQL, security headers enabled, debug disabled

## API Documentation

### Authentication Endpoints

- `POST /register` - User registration
- `POST /login` - User login  
- `POST /logout` - User logout
- `POST /forgot-password` - Password reset request
- `POST /reset-password` - Password reset confirmation

### Chat Endpoints

- `GET /` - Dashboard with chat history
- `GET /chat/<id>` - Chat interface
- `POST /chat/<id>/message` - Send message
- `GET /chat/<id>/message/stream` - Stream AI response

### Admin Endpoints

- `GET /admin` - Admin dashboard
- `POST /admin/approve/<user_id>` - Approve user
- `POST /admin/toggle-admin/<user_id>` - Toggle admin status

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Ensure all tests pass: `python -m pytest`
5. Format code: `black . && isort .`
6. Submit a pull request

### Development Guidelines

- Write tests for new features
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Update documentation for significant changes
- Ensure security best practices

## Security

- CSRF protection on all forms
- Secure session cookies
- Input validation and sanitization
- SQL injection prevention via ORM
- Environment-based configuration
- Security headers for production

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue on GitHub or contact the development team.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.