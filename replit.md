# Overview

This is an AI Chat Assistant application built with Flask that provides users with a conversational interface to interact with OpenAI's GPT models. The application features user authentication with admin approval, chat history management, tag-based organization, and email notifications. Users can create multiple chat sessions, organize them with colored tags, and interact with different AI models through a modern web interface.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The frontend uses a traditional server-side rendered approach with Flask templates and Jinja2. The UI is built with Bootstrap 5 (dark theme) for responsive design and modern styling. JavaScript handles dynamic chat functionality, including real-time message streaming, chat management, and interactive elements. The application uses highlight.js for code syntax highlighting and Bootstrap Icons for visual elements.

## Backend Architecture
The application follows the MVC pattern with Flask as the web framework. The backend is structured with clear separation of concerns:
- **Routes**: Handle HTTP requests and responses in `routes.py`
- **Models**: Define database schemas using SQLAlchemy ORM in `models.py`
- **Services**: Business logic separated into specialized handlers (`chat_handler.py`, `email_handler.py`)
- **Configuration**: Application setup and middleware configuration in `app.py`

The application uses Flask-Login for session management and includes middleware for production deployment (WhiteNoise for static files, ProxyFix for proper header handling).

## Data Storage
The application uses SQLAlchemy with a relational database structure:
- **User management**: Users, authentication, and admin approval system
- **Chat system**: Chats, messages with role-based storage (user/assistant)
- **Organization**: Tags with many-to-many relationships to chats
- **Security**: Password reset tokens with expiry timestamps

Database migrations are handled through custom scripts, with support for schema updates without data loss.

## Authentication & Authorization
The system implements a multi-layered security approach:
- **Registration**: New users require admin approval before accessing the system
- **Password management**: Secure hashing with Werkzeug and password reset functionality
- **Session management**: Flask-Login handles user sessions and login state
- **Role-based access**: Admin users have additional privileges for user management

## AI Integration
The chat system integrates with OpenAI's API through a custom handler that:
- **Model selection**: Supports multiple GPT models with custom mapping
- **Streaming responses**: Real-time message streaming for better user experience
- **Context management**: Maintains conversation history for coherent interactions
- **Error handling**: Graceful degradation when AI services are unavailable

# External Dependencies

## Third-Party Services
- **OpenAI API**: Core AI functionality for chat responses using GPT models
- **SendGrid**: Email service for user notifications, registration confirmations, and password reset emails

## Production Infrastructure
- **Replit**: Hosting platform with specific configurations for proxy handling and static file serving
- **Waitress**: WSGI server for production deployment with proper threading support

## Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme customization
- **Bootstrap Icons**: Icon library for user interface elements
- **Highlight.js**: Code syntax highlighting in chat messages

## Backend Dependencies
- **Flask ecosystem**: Core web framework with SQLAlchemy ORM, Login management, and template rendering
- **WhiteNoise**: Static file serving middleware optimized for production
- **ProxyFix**: Middleware for proper header handling behind reverse proxies

## Database
The application is database-agnostic through SQLAlchemy but is configured to work with PostgreSQL in production environments. The schema includes proper indexing and relationship management for optimal performance.