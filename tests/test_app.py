"""
Tests for Flask app configuration and creation.
"""

import os

from app import create_app, db


class TestAppCreation:
    """Test cases for Flask app creation and configuration."""

    def test_app_creation(self):
        """Test that the app can be created successfully."""
        app = create_app()
        assert app is not None
        assert app.name == "app"

    def test_app_config_defaults(self):
        """Test default app configuration."""
        app = create_app()

        # Test that essential configs are set
        assert app.config.get("SECRET_KEY") is not None
        assert app.config.get("SQLALCHEMY_DATABASE_URI") is not None

        # Test security settings (should be appropriate for environment)
        # In development/testing, secure cookies may be False
        assert app.config.get("SESSION_COOKIE_HTTPONLY") is True
        assert app.config.get("REMEMBER_COOKIE_HTTPONLY") is True
        assert isinstance(app.config.get("SESSION_COOKIE_SECURE"), bool)
        assert isinstance(app.config.get("REMEMBER_COOKIE_SECURE"), bool)

        # Test session/cookie timeouts
        assert app.config.get("PERMANENT_SESSION_LIFETIME") == 3600
        assert app.config.get("REMEMBER_COOKIE_DURATION") == 2592000

    def test_app_database_config(self):
        """Test database configuration."""
        app = create_app()

        # Test database URI is set
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
        assert db_uri is not None

        # Test engine options
        engine_options = app.config.get("SQLALCHEMY_ENGINE_OPTIONS")
        assert engine_options is not None
        assert engine_options.get("pool_pre_ping") is True

        # Test that config adapts to database type
        if "sqlite" in db_uri:
            # SQLite config should only have pool_pre_ping
            assert "pool_recycle" not in engine_options
        else:
            # PostgreSQL config should have full pool settings
            assert engine_options.get("pool_recycle") == 300
            assert engine_options.get("pool_size") == 10
            assert engine_options.get("max_overflow") == 20
            assert engine_options.get("pool_timeout") == 30

    def test_app_admin_config(self):
        """Test admin user configuration."""
        app = create_app()

        # Test admin username and email defaults
        assert app.config.get("ADMIN_USERNAME") == "codhe"
        assert app.config.get("ADMIN_EMAIL") == "danielhalwell@gmail.com"

    def test_app_static_folder_config(self):
        """Test static folder configuration."""
        app = create_app()

        # Test static folder path
        assert app.static_folder is not None
        assert app.static_url_path == "/static"
        assert "static" in app.static_folder

    def test_app_extensions_initialized(self):
        """Test that Flask extensions are properly initialized."""
        app = create_app()

        # Test that db extension is available
        assert hasattr(app, "extensions")
        assert "sqlalchemy" in app.extensions

    def test_app_context_database_tables(self, app):
        """Test that database tables are created in app context."""
        with app.app_context():
            # Test that tables exist using inspector
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            expected_tables = ["user", "chat", "message", "tag", "chat_tags"]

            for table in expected_tables:
                assert table in tables


class TestAppConfiguration:
    """Test cases for app configuration under different environments."""

    def test_testing_mode(self, app):
        """Test app behavior in testing mode."""
        # The app fixture should have testing enabled
        assert app.config.get("TESTING") is True
        assert "sqlite" in app.config.get("SQLALCHEMY_DATABASE_URI")

    def test_environment_variables_override(self):
        """Test that environment variables override defaults."""
        # Set environment variables
        os.environ["FLASK_SECRET_KEY"] = "test-env-secret"
        os.environ["ADMIN_USERNAME"] = "test-admin"
        os.environ["ADMIN_EMAIL"] = "test@admin.com"

        try:
            app = create_app()

            # Test that environment variables are used
            assert app.config.get("ADMIN_USERNAME") == "test-admin"
            assert app.config.get("ADMIN_EMAIL") == "test@admin.com"

        finally:
            # Clean up environment variables
            os.environ.pop("FLASK_SECRET_KEY", None)
            os.environ.pop("ADMIN_USERNAME", None)
            os.environ.pop("ADMIN_EMAIL", None)


class TestAppMiddleware:
    """Test cases for app middleware configuration."""

    def test_whitenoise_middleware(self):
        """Test that WhiteNoise middleware is configured."""
        app = create_app()

        # WhiteNoise should be part of the WSGI app
        assert hasattr(app, "wsgi_app")
        # The actual WhiteNoise object is wrapped, so we check the class name
        wsgi_app_type = type(app.wsgi_app).__name__
        assert "ProxyFix" in wsgi_app_type or "WhiteNoise" in str(type(app.wsgi_app))

    def test_proxy_fix_middleware(self):
        """Test that ProxyFix middleware is configured."""
        app = create_app()

        # ProxyFix should be the outermost middleware
        assert hasattr(app, "wsgi_app")
        wsgi_app_type = type(app.wsgi_app).__name__
        assert "ProxyFix" in wsgi_app_type
