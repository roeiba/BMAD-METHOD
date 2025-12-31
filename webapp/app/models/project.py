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
    status = db.Column(db.String(50), default='setup')  # setup, planning, solutioning, implementation, completed
    
    # Project metadata
    project_type = db.Column(db.String(50), default='greenfield')  # greenfield, brownfield
    tech_stack = db.Column(db.JSON, default=list)
    team_size = db.Column(db.String(20), default='solo')  # solo, small, medium, large
    
    # Phase completion tracking
    phase1_completed = db.Column(db.Boolean, default=False)
    phase2_completed = db.Column(db.Boolean, default=False)
    phase3_completed = db.Column(db.Boolean, default=False)
    phase4_completed = db.Column(db.Boolean, default=False)
    
    # Key document references
    prd_id = db.Column(db.Integer, db.ForeignKey('documents.id'))
    architecture_id = db.Column(db.Integer, db.ForeignKey('documents.id'))
    tech_spec_id = db.Column(db.Integer, db.ForeignKey('documents.id'))
    
    # Current sprint
    current_sprint_id = db.Column(db.Integer, db.ForeignKey('sprints.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workflow_statuses = db.relationship('WorkflowStatus', backref='project', lazy='dynamic')
    activities = db.relationship('Activity', backref='project', lazy='dynamic')
    documents = db.relationship('Document', backref='project', lazy='dynamic', foreign_keys='Document.project_id')
    epics = db.relationship('Epic', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    stories = db.relationship('Story', backref='project', lazy='dynamic')
    sprints = db.relationship('Sprint', backref='project', lazy='dynamic', foreign_keys='Sprint.project_id')
    workflow_executions = db.relationship('WorkflowExecution', backref='project', lazy='dynamic')
    
    @property
    def epic_count(self):
        return self.epics.count()
    
    @property
    def story_count(self):
        return self.stories.count()
    
    @property
    def completed_stories(self):
        return self.stories.filter_by(status='done').count()
    
    @property
    def overall_progress(self):
        """Calculate overall project progress based on phase and stories."""
        phase_weight = {1: 10, 2: 30, 3: 20, 4: 40}
        progress = 0
        
        if self.phase1_completed:
            progress += phase_weight[1]
        if self.phase2_completed:
            progress += phase_weight[2]
        if self.phase3_completed:
            progress += phase_weight[3]
        
        # Phase 4 progress based on stories
        if self.story_count > 0:
            story_progress = (self.completed_stories / self.story_count) * phase_weight[4]
            progress += story_progress
        
        return int(progress)
    
    def to_dict(self, include_stats=True):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'path': self.path,
            'track': self.track,
            'current_phase': self.current_phase,
            'status': self.status,
            'project_type': self.project_type,
            'tech_stack': self.tech_stack,
            'team_size': self.team_size,
            'phase1_completed': self.phase1_completed,
            'phase2_completed': self.phase2_completed,
            'phase3_completed': self.phase3_completed,
            'phase4_completed': self.phase4_completed,
            'prd_id': self.prd_id,
            'architecture_id': self.architecture_id,
            'tech_spec_id': self.tech_spec_id,
            'current_sprint_id': self.current_sprint_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_stats:
            data.update({
                'epic_count': self.epic_count,
                'story_count': self.story_count,
                'completed_stories': self.completed_stories,
                'overall_progress': self.overall_progress,
            })
        
        return data


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


