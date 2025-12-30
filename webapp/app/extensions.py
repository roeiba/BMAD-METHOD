"""
BMAD Web Dashboard - Flask Extensions
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Database
db = SQLAlchemy()
migrate = Migrate()
