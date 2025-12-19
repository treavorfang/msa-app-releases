"""
Tests for flag-based configuration system.
"""

import pytest
from absl.testing import flagsaver, absltest
from absl import flags
import sys
import os

# Add src/app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'app'))

from config.flags import FLAGS, get_config, get_db_path, is_production, is_development, is_staging

# Parse flags once at module level
try:
    FLAGS(['test'])  # Parse with dummy argv
except flags.IllegalFlagValueError:
    pass  # Flags already parsed


class TestFlagsBasic:
    """Test basic flag functionality"""
    
    @flagsaver.flagsaver(env='development')
    def test_default_environment(self):
        """Test default environment is development"""
        assert FLAGS.env == 'development'
        assert is_development()
        assert not is_production()
        assert not is_staging()
    
    @flagsaver.flagsaver(env='production')
    def test_production_environment(self):
        """Test production environment detection"""
        assert FLAGS.env == 'production'
        assert is_production()
        assert not is_development()
        assert not is_staging()
    
    @flagsaver.flagsaver(env='staging')
    def test_staging_environment(self):
        """Test staging environment detection"""
        assert FLAGS.env == 'staging'
        assert is_staging()
        assert not is_development()
        assert not is_production()


class TestFlagsConfiguration:
    """Test configuration retrieval"""
    
    @flagsaver.flagsaver(env='development', debug=True, theme='dark')
    def test_get_config(self):
        """Test get_config returns correct configuration"""
        config = get_config()
        
        assert config['env'] == 'development'
        assert config['debug'] == True
        assert config['theme'] == 'dark'
        assert 'db_path' in config
        assert 'log_level' in config
    
    @flagsaver.flagsaver(debug=True)
    def test_debug_flag(self):
        """Test debug flag"""
        assert FLAGS.debug == True
        config = get_config()
        assert config['debug'] == True
    
    @flagsaver.flagsaver(theme='light')
    def test_theme_flag(self):
        """Test theme flag"""
        assert FLAGS.theme == 'light'
        config = get_config()
        assert config['theme'] == 'light'
    
    @flagsaver.flagsaver(language='burmese')
    def test_language_flag(self):
        """Test language flag"""
        assert FLAGS.language == 'burmese'
        config = get_config()
        assert config['language'] == 'burmese'


class TestDatabasePath:
    """Test database path generation"""
    
    @flagsaver.flagsaver(env='development', db_path=None)
    def test_dev_db_path(self):
        """Test development database path"""
        db_path = get_db_path()
        assert 'msa_dev.db' in db_path
    
    @flagsaver.flagsaver(env='staging', db_path=None)
    def test_staging_db_path(self):
        """Test staging database path"""
        db_path = get_db_path()
        assert 'msa_staging.db' in db_path
    
    @flagsaver.flagsaver(env='production', db_path=None)
    def test_production_db_path(self):
        """Test production database path"""
        db_path = get_db_path()
        assert 'msa.db' in db_path
        assert 'msa_dev' not in db_path
        assert 'msa_staging' not in db_path
    
    @flagsaver.flagsaver(db_path='/custom/path/db.db')
    def test_custom_db_path(self):
        """Test custom database path override"""
        db_path = get_db_path()
        assert db_path == '/custom/path/db.db'


class TestFeatureFlags:
    """Test feature flags"""
    
    @flagsaver.flagsaver(enable_analytics=True)
    def test_analytics_enabled(self):
        """Test analytics feature flag"""
        assert FLAGS.enable_analytics == True
        config = get_config()
        assert config['enable_analytics'] == True
    
    @flagsaver.flagsaver(enable_analytics=False)
    def test_analytics_disabled(self):
        """Test analytics can be disabled"""
        assert FLAGS.enable_analytics == False
        config = get_config()
        assert config['enable_analytics'] == False
    
    @flagsaver.flagsaver(enable_eventbus=True)
    def test_eventbus_enabled(self):
        """Test EventBus feature flag"""
        assert FLAGS.enable_eventbus == True
    
    @flagsaver.flagsaver(enable_eventbus=False)
    def test_eventbus_disabled(self):
        """Test EventBus can be disabled"""
        assert FLAGS.enable_eventbus == False


class TestPerformanceFlags:
    """Test performance-related flags"""
    
    @flagsaver.flagsaver(cache_size_mb=128)
    def test_cache_size(self):
        """Test cache size configuration"""
        assert FLAGS.cache_size_mb == 128
        config = get_config()
        assert config['cache_size_mb'] == 128
    
    @flagsaver.flagsaver(max_workers=8)
    def test_max_workers(self):
        """Test max workers configuration"""
        assert FLAGS.max_workers == 8
        config = get_config()
        assert config['max_workers'] == 8


class TestFlagCombinations:
    """Test combinations of flags"""
    
    @flagsaver.flagsaver(
        env='production',
        debug=False,
        theme='dark',
        language='burmese',
        enable_analytics=True,
        cache_size_mb=256
    )
    def test_production_configuration(self):
        """Test typical production configuration"""
        config = get_config()
        
        assert config['env'] == 'production'
        assert config['debug'] == False
        assert config['theme'] == 'dark'
        assert config['language'] == 'burmese'
        assert config['enable_analytics'] == True
        assert config['cache_size_mb'] == 256
        
        assert is_production()
    
    @flagsaver.flagsaver(
        env='development',
        debug=True,
        db_debug=True,
        log_level='DEBUG'
    )
    def test_development_configuration(self):
        """Test typical development configuration"""
        config = get_config()
        
        assert config['env'] == 'development'
        assert config['debug'] == True
        assert config['db_debug'] == True
        assert config['log_level'] == 'DEBUG'
        
        assert is_development()


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
