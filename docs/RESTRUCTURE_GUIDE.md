# MyGPT - Production-Ready Directory Structure

This document describes the new production-ready directory structure for the MyGPT AI Chat Assistant application.

## 📁 Directory Structure

```
MyGPT/
├── src/mygpt/                    # Main application package
│   ├── __init__.py              # Package initialization
│   ├── app.py                   # Flask application factory
│   ├── models.py                # Database models
│   ├── routes.py                # Route handlers
│   ├── cli.py                   # Command-line interface
│   ├── config/                  # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py          # Environment-specific configs
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── chat_handler.py      # Chat processing logic
│   │   ├── multi_provider_chat_handler.py
│   │   └── email_handler.py     # Email notification service
│   └── schemas/                 # Data validation
│       ├── __init__.py
│       └── validation_schemas.py
├── templates/                   # Jinja2 HTML templates
├── static/                      # CSS, JS, images
│   ├── css/
│   ├── js/
│   └── generated-icon.png
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Test configuration
│   ├── test_app.py             # App tests
│   ├── test_models.py          # Model tests
│   └── test_*.py               # Additional tests
├── docs/                        # Documentation
│   ├── README.md               # Main documentation
│   ├── CODEBASE_REVIEW.md      # Code review findings
│   ├── IMPLEMENTATION_GUIDE.md  # Implementation guide
│   ├── TESTING.md              # Testing documentation
│   └── *.md                    # Other documentation
├── scripts/                     # Utility scripts
│   ├── setup-dev.sh            # Development setup
│   ├── db_*.py                 # Database utilities
│   └── test_*.py               # Test utilities
├── deployment/                  # Deployment configurations
│   ├── .env.production         # Production environment
│   ├── .replit                 # Replit configuration
│   └── replit.nix              # Nix dependencies
├── attached_assets/             # Project assets
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
├── pyproject.toml              # Project metadata and deps
├── main.py                     # Legacy entry point
└── uv.lock                     # Dependency lock file
```

## 🚀 Key Improvements

### 1. **Proper Python Package Structure**
- Follows the `src/` layout pattern
- Clear separation of concerns
- Importable as a proper Python package

### 2. **Configuration Management**
- Environment-specific configurations
- Centralized settings management
- Secure environment variable handling

### 3. **Service Layer Architecture**
- Business logic separated from routes
- Modular service components
- Easier testing and maintenance

### 4. **Enhanced Development Workflow**
- CLI entry point (`mygpt` command)
- Development setup scripts
- Environment templates

### 5. **Production Readiness**
- Deployment configurations
- Security best practices
- Scalable architecture

## 📋 Migration Guide

### Old vs New Structure

| Old Location | New Location | Purpose |
|--------------|--------------|---------|
| `app.py` | `src/mygpt/app.py` | Application factory |
| `models.py` | `src/mygpt/models.py` | Database models |
| `routes.py` | `src/mygpt/routes.py` | Route handlers |
| `schemas.py` | `src/mygpt/schemas/validation_schemas.py` | Data validation |
| `*_handler.py` | `src/mygpt/services/` | Business services |
| `*.md` | `docs/` | Documentation |
| `db_*.py` | `scripts/` | Database scripts |
| `replit.*` | `deployment/` | Deployment files |

### Import Changes

**Old imports:**
```python
from app import app, db
from models import User, Chat
from chat_handler import generate_summary
```

**New imports:**
```python
from mygpt.app import create_app, db
from mygpt.models import User, Chat
from mygpt.services.chat_handler import generate_summary
```

## 🏃‍♂️ Getting Started

### 1. Install the Package
```bash
pip install -e ".[dev]"
```

### 2. Set Up Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run the Application

**Using the new CLI:**
```bash
mygpt --help
mygpt --debug
```

**Legacy method:**
```bash
python main.py
```

### 4. Development Setup
```bash
./scripts/setup-dev.sh
```

## 🧪 Testing

Run tests with the new structure:
```bash
pytest
pytest --cov=src/mygpt
```

## 📦 Package Management

The project now supports proper Python packaging:

```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Build package
python -m build
```

## 🔒 Security Enhancements

- Environment-specific configurations
- Secure secret management
- Production security settings
- CSRF protection
- Input validation

## 📈 Performance Improvements

- Optimized static file serving
- Database connection pooling
- Caching strategies
- Production middleware

## 🛠️ Development Tools

- Pre-commit hooks
- Code formatting (Black, isort)
- Linting (flake8)
- Type checking (mypy)
- Test coverage reporting

## 🚀 Deployment

### Development
```bash
mygpt --env development --debug
```

### Production
```bash
mygpt --env production --host 0.0.0.0 --port 5000
```

### Replit
Uses deployment configurations in `deployment/` directory.

---

This restructured codebase provides a solid foundation for scaling and maintaining the MyGPT application in production environments while following Python best practices and industry standards.