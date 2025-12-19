# src/app/config/flags.py
"""
Application flags for configuration management.

Enables "One Binary, Many Configs" pattern using absl-py flags.
"""

from absl import flags

# Define application flags
FLAGS = flags.FLAGS

# Environment configuration
flags.DEFINE_enum(
    'env',
    'development',
    ['development', 'staging', 'production'],
    'Application environment'
)

# Database configuration
flags.DEFINE_string(
    'db_path',
    None,
    'Path to SQLite database file. If not set, uses default based on environment.'
)

flags.DEFINE_boolean(
    'db_debug',
    False,
    'Enable database query debugging'
)

# Application configuration
flags.DEFINE_integer(
    'port',
    8000,
    'Application port (for future web interface)'
)

flags.DEFINE_boolean(
    'debug',
    False,
    'Enable debug mode'
)

flags.DEFINE_string(
    'log_level',
    'INFO',
    'Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)'
)

# UI configuration
flags.DEFINE_string(
    'theme',
    'dark',
    'Application theme (dark, light)'
)

flags.DEFINE_string(
    'language',
    'en',
    'Application language (en, burmese)'
)

# Business configuration
flags.DEFINE_string(
    'company_name',
    None,
    'Company name override'
)

flags.DEFINE_string(
    'currency',
    'MMK',
    'Currency code (MMK, USD, etc.)'
)

# Feature flags
flags.DEFINE_boolean(
    'enable_analytics',
    True,
    'Enable analytics dashboard'
)

flags.DEFINE_boolean(
    'enable_reports',
    True,
    'Enable reports functionality'
)

flags.DEFINE_boolean(
    'enable_eventbus',
    True,
    'Enable EventBus for domain events (disable to use Qt signals)'
)

# Performance configuration
flags.DEFINE_integer(
    'cache_size_mb',
    64,
    'Database cache size in MB'
)

flags.DEFINE_integer(
    'max_workers',
    4,
    'Maximum number of worker threads'
)


def get_config():
    """
    Get configuration dictionary based on current flags.
    
    Returns:
        dict: Configuration dictionary
    """
    return {
        'env': FLAGS.env,
        'db_path': FLAGS.db_path,
        'db_debug': FLAGS.db_debug,
        'port': FLAGS.port,
        'debug': FLAGS.debug,
        'log_level': FLAGS.log_level,
        'theme': FLAGS.theme,
        'language': FLAGS.language,
        'company_name': FLAGS.company_name,
        'currency': FLAGS.currency,
        'enable_analytics': FLAGS.enable_analytics,
        'enable_reports': FLAGS.enable_reports,
        'enable_eventbus': FLAGS.enable_eventbus,
        'cache_size_mb': FLAGS.cache_size_mb,
        'max_workers': FLAGS.max_workers,
    }


def get_db_path():
    """
    Get database path based on environment.
    
    Returns:
        str: Database file path
    """
    try:
        if FLAGS.is_parsed() and FLAGS.db_path:
            return FLAGS.db_path
    except AttributeError:
        # Older absl versions might not have is_parsed, or if purely unparsed
        pass
    except Exception:
        pass
    
    from pathlib import Path
    import sys
    import os
    
    app_name = "MSA"
    # Point to project root (msa/) explicitly for development
    # src/app/config/flags.py -> src/app/config -> src/app -> src -> msa
    project_root = Path(__file__).resolve().parents[3]
    
    # User Data Directory (Platform Specific)
    if sys.platform == "win32":
        user_data_dir = Path(os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))) / app_name
    elif sys.platform == "darwin":
        user_data_dir = Path(os.path.expanduser("~/Library/Application Support")) / app_name
    else:
        # Linux/Unix
        user_data_dir = Path(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))) / app_name
        
    # Determine environment safely
    try:
        if FLAGS.is_parsed():
            env = FLAGS.env
        else:
            # Default to production if frozen, else development
            env = 'production' if getattr(sys, 'frozen', False) else 'development'
    except Exception:
        env = 'development'

    # Ensure directory exists for production/staging
    if env in ['production', 'staging']:
        try:
            user_data_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Fallback to local if permission denied
            pass
    
    # Environment-specific database paths
    db_paths = {
        'development': project_root / 'database' / 'msa_dev.db',
        'staging': user_data_dir / 'msa_staging.db',
        'production': user_data_dir / 'msa.db',
    }
    
    return str(db_paths[env])


def is_production():
    """Check if running in production environment."""
    return FLAGS.env == 'production'


def is_development():
    """Check if running in development environment."""
    return FLAGS.env == 'development'


def is_staging():
    """Check if running in staging environment."""
    return FLAGS.env == 'staging'
