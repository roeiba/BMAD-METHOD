"""
BMAD Web Dashboard - Activity Log Model
"""
from datetime import datetime
from ..extensions import db


class Activity(db.Model):
    """Activity log for tracking project events."""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    activity_type = db.Column(db.String(50), nullable=False)  # workflow, agent, story, system
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    extra_data = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'activity_type': self.activity_type,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
