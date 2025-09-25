#!/bin/bash
# Development setup script for MyGPT

echo "🚀 Setting up MyGPT development environment..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your API keys."
else
    echo "ℹ️  .env file already exists"
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -e ".[dev]"

# Install pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install

# Create database tables
echo "🗃️  Setting up database..."
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from mygpt.app import create_app
app = create_app()
with app.app_context():
    from mygpt.app import db
    db.create_all()
    print('✅ Database tables created')
"

echo "✅ Development environment setup complete!"
echo ""
echo "🔑 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run 'python main.py' or 'mygpt' to start the application"
echo "3. Visit http://localhost:5000 in your browser"