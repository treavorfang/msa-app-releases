# Flag-Based Configuration Guide

## Overview

The MSA application now supports **flag-based configuration**, enabling the "One Binary, Many Configs" pattern. This allows you to run the same application binary with different configurations for development, staging, and production environments.

## Quick Start

### Running with Default Configuration (Development)

```bash
cd /Users/studiotai/PyProject/msa
python3 src/app/main.py
```

### Running with Environment-Specific Configuration

```bash
# Development
python3 src/app/main.py --flagfile=src/app/config/dev.flags

# Staging
python3 src/app/main.py --flagfile=src/app/config/staging.flags

# Production
python3 src/app/main.py --flagfile=src/app/config/production.flags
```

### Running with Custom Flags

```bash
# Override specific flags
python3 src/app/main.py --env=production --debug=true --theme=light

# Combine flagfile with overrides
python3 src/app/main.py --flagfile=src/app/config/production.flags --debug=true
```

## Available Flags

### Environment Configuration

| Flag          | Type   | Default       | Description                                                    |
| ------------- | ------ | ------------- | -------------------------------------------------------------- |
| `--env`       | enum   | `development` | Environment: `development`, `staging`, `production`            |
| `--debug`     | bool   | `false`       | Enable debug mode                                              |
| `--log_level` | string | `INFO`        | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

### Database Configuration

| Flag              | Type   | Default | Description                                      |
| ----------------- | ------ | ------- | ------------------------------------------------ |
| `--db_path`       | string | `None`  | Custom database path (auto-generated if not set) |
| `--db_debug`      | bool   | `false` | Enable database query debugging                  |
| `--cache_size_mb` | int    | `64`    | Database cache size in MB                        |

### UI Configuration

| Flag         | Type   | Default | Description                           |
| ------------ | ------ | ------- | ------------------------------------- |
| `--theme`    | string | `dark`  | Application theme: `dark`, `light`    |
| `--language` | string | `en`    | Application language: `en`, `burmese` |

### Business Configuration

| Flag             | Type   | Default | Description                       |
| ---------------- | ------ | ------- | --------------------------------- |
| `--company_name` | string | `None`  | Company name override             |
| `--currency`     | string | `MMK`   | Currency code: `MMK`, `USD`, etc. |

### Feature Flags

| Flag                 | Type | Default | Description                                 |
| -------------------- | ---- | ------- | ------------------------------------------- |
| `--enable_analytics` | bool | `true`  | Enable analytics dashboard                  |
| `--enable_reports`   | bool | `true`  | Enable reports functionality                |
| `--enable_eventbus`  | bool | `true`  | Enable EventBus (disable to use Qt signals) |

### Performance Configuration

| Flag            | Type | Default | Description                                 |
| --------------- | ---- | ------- | ------------------------------------------- |
| `--port`        | int  | `8000`  | Application port (for future web interface) |
| `--max_workers` | int  | `4`     | Maximum number of worker threads            |

## Environment-Specific Configurations

### Development (`dev.flags`)

```
--env=development
--debug=true
--db_debug=true
--log_level=DEBUG
--theme=dark
--language=en
--cache_size_mb=64
--max_workers=2
```

**Use Case**: Local development, debugging, testing new features

**Database**: `src/app/database/msa_dev.db`

### Staging (`staging.flags`)

```
--env=staging
--debug=false
--db_debug=false
--log_level=INFO
--theme=dark
--language=en
--cache_size_mb=128
--max_workers=4
```

**Use Case**: Pre-production testing, QA, user acceptance testing

**Database**: `src/app/database/msa_staging.db`

### Production (`production.flags`)

```
--env=production
--debug=false
--db_debug=false
--log_level=WARNING
--theme=dark
--language=burmese
--cache_size_mb=256
--max_workers=8
```

**Use Case**: Live production environment

**Database**: `src/app/database/msa.db`

## Usage Examples

### Example 1: Development with Debug Logging

```bash
python3 src/app/main.py --env=development --log_level=DEBUG
```

### Example 2: Production with Custom Database

```bash
python3 src/app/main.py \
  --flagfile=src/app/config/production.flags \
  --db_path=/data/msa_production.db
```

### Example 3: Testing with Light Theme

```bash
python3 src/app/main.py --env=development --theme=light
```

### Example 4: Disable EventBus (Use Qt Signals)

```bash
python3 src/app/main.py --enable_eventbus=false
```

### Example 5: High-Performance Production

```bash
python3 src/app/main.py \
  --flagfile=src/app/config/production.flags \
  --cache_size_mb=512 \
  --max_workers=16
```

## Programmatic Access

### In Python Code

```python
from config.flags import FLAGS, get_config, is_production

# Get current environment
if is_production():
    print("Running in production mode")

# Get specific flag value
theme = FLAGS.theme
debug_mode = FLAGS.debug

# Get all configuration as dictionary
config = get_config()
print(config)
```

### Environment Detection

```python
from config.flags import is_development, is_staging, is_production

if is_development():
    # Development-specific code
    enable_debug_toolbar()

elif is_staging():
    # Staging-specific code
    enable_analytics()

elif is_production():
    # Production-specific code
    enable_monitoring()
```

## Best Practices

### 1. Use Flagfiles for Environments

✅ **Good**: Use flagfiles for consistent environment configurations

```bash
python3 src/app/main.py --flagfile=src/app/config/production.flags
```

❌ **Bad**: Manually specify all flags every time

```bash
python3 src/app/main.py --env=production --debug=false --db_debug=false ...
```

### 2. Override Specific Flags When Needed

✅ **Good**: Use flagfile as base, override specific flags

```bash
python3 src/app/main.py --flagfile=src/app/config/production.flags --debug=true
```

### 3. Keep Sensitive Data Out of Flagfiles

✅ **Good**: Use environment variables or secure config for secrets

```bash
export DB_PASSWORD="secret"
python3 src/app/main.py --flagfile=src/app/config/production.flags
```

❌ **Bad**: Store passwords in flagfiles

```
--db_password=mysecretpassword  # DON'T DO THIS
```

### 4. Version Control Flagfiles

✅ **Good**: Commit flagfiles to version control

- Provides configuration history
- Easy to track changes
- Team members have consistent configs

### 5. Document Custom Configurations

✅ **Good**: Create custom flagfiles for specific use cases

```bash
# config/demo.flags - For product demonstrations
--env=staging
--theme=light
--language=en
--enable_analytics=false
```

## Troubleshooting

### Issue: Flags Not Being Applied

**Solution**: Make sure you're using `--flagfile` with the correct path:

```bash
python3 src/app/main.py --flagfile=src/app/config/production.flags
```

### Issue: Database Not Found

**Solution**: Check the database path for your environment:

```bash
python3 src/app/main.py --env=development --db_debug=true
```

### Issue: Configuration Not Persisting

**Note**: Flags are runtime configuration only. For persistent settings, use QSettings:

```python
from PySide6.QtCore import QSettings
settings = QSettings("MSA", "MSA")
settings.setValue("theme", "dark")
```

## Migration from Old Configuration

### Before (Hardcoded)

```python
# config.py
DEBUG = True
DATABASE_PATH = "database/msa.db"
THEME = "dark"
```

### After (Flag-Based)

```bash
# Run with flags
python3 src/app/main.py --debug=true --theme=dark
```

```python
# Access in code
from config.flags import FLAGS
debug = FLAGS.debug
theme = FLAGS.theme
```

## Advanced Usage

### Creating Custom Flagfiles

Create a new flagfile for your specific use case:

```bash
# config/custom.flags
--env=development
--debug=true
--theme=light
--language=burmese
--enable_analytics=false
--cache_size_mb=128
```

Run with:

```bash
python3 src/app/main.py --flagfile=src/app/config/custom.flags
```

### Combining Multiple Flagfiles

```bash
# Load base config, then override with custom
python3 src/app/main.py \
  --flagfile=src/app/config/production.flags \
  --flagfile=src/app/config/custom_overrides.flags
```

### Environment Variable Integration

```bash
# Set environment-specific flags via environment variables
export MSA_ENV=production
export MSA_DEBUG=false

python3 src/app/main.py --env=$MSA_ENV --debug=$MSA_DEBUG
```

## Testing with Different Configurations

### Unit Tests

```python
from absl.testing import flagsaver

@flagsaver.flagsaver(env='development', debug=True)
def test_with_dev_config():
    # Test runs with development configuration
    assert FLAGS.env == 'development'
    assert FLAGS.debug == True
```

### Integration Tests

```bash
# Test with staging configuration
python3 -m pytest tests/ --flagfile=src/app/config/staging.flags
```

## Summary

Flag-based configuration provides:

- ✅ **One Binary, Many Configs**: Same application, different environments
- ✅ **Easy Deployment**: Just change the flagfile
- ✅ **Testability**: Easy to test with different configurations
- ✅ **Flexibility**: Override any flag at runtime
- ✅ **Documentation**: Self-documenting configuration options

For more information, see:

- `src/app/config/flags.py` - Flag definitions
- `src/app/config/*.flags` - Environment configurations
- `src/app/main.py` - Flag integration

---

**Last Updated**: 2025-12-05  
**Version**: 1.0.0
