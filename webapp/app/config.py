"""
BMAD Web Dashboard - Configuration Settings
"""
import os
from pathlib import Path

basedir = Path(__file__).parent.parent.absolute()


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'bmad-dev-secret-key-change-me')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # BMAD Source paths
    BMAD_SOURCE_PATH = os.getenv('BMAD_SOURCE_PATH', str(basedir.parent / 'src'))
    BMAD_MODULES_PATH = os.path.join(BMAD_SOURCE_PATH, 'modules')
    BMAD_CORE_PATH = os.path.join(BMAD_SOURCE_PATH, 'core')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        f'sqlite:///{basedir / "bmad.db"}'
    )


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///bmad.db')


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
