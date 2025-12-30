"""
BMAD Web Dashboard - Project Models
"""
from datetime import datetime
from ..extensions import db


class Project(db.Model):
    """Project model for tracking BMAD projects."""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    path = db.Column(db.String(500), nullable=False, unique=True)
    track = db.Column(db.String(50), default='bmad-method')  # quick-flow, bmad-method, enterprise
    current_phase = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), default='active')  # active, completed, archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workflow_statuses = db.relationship('WorkflowStatus', backref='project', lazy='dynamic')
    sprint_statuses = db.relationship('SprintStatus', backref='project', lazy='dynamic')
    activities = db.relationship('Activity', backref='project', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'path': self.path,
            'track': self.track,
            'current_phase': self.current_phase,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class WorkflowStatus(db.Model):
    """Workflow status tracking for projects."""
    __tablename__ = 'workflow_statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    workflow_name = db.Column(db.String(255), nullable=False)
    phase = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed, skipped
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    output_files = db.Column(db.JSON, default=list)
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'workflow_name': self.workflow_name,
            'phase': self.phase,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'output_files': self.output_files,
            'notes': self.notes,
        }


class SprintStatus(db.Model):
    """Sprint and story tracking."""
    __tablename__ = 'sprint_statuses'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    sprint_number = db.Column(db.Integer, nullable=False)
    epic_id = db.Column(db.String(50))
    epic_name = db.Column(db.String(255))
    story_id = db.Column(db.String(50))
    story_name = db.Column(db.String(255))
    status = db.Column(db.String(50), default='backlog')  # backlog, ready, in_progress, review, done
    priority = db.Column(db.Integer, default=0)
    estimated_points = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'sprint_number': self.sprint_number,
            'epic_id': self.epic_id,
            'epic_name': self.epic_name,
            'story_id': self.story_id,
            'story_name': self.story_name,
            'status': self.status,
            'priority': self.priority,
            'estimated_points': self.estimated_points,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
