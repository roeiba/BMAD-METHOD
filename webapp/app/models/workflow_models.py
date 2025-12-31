"""
BMAD Web Dashboard - Workflow-Related Models
Models for PRD, Epics, Stories, Tasks, and Documents
"""
from datetime import datetime
from ..extensions import db
import json


class Document(db.Model):
    """Generated documents (PRD, Architecture, etc.)"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    doc_type = db.Column(db.String(50), nullable=False)  # prd, architecture, tech-spec, ux-design, etc.
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    version = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), default='draft')  # draft, review, approved, archived
    file_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'doc_type': self.doc_type,
            'title': self.title,
            'content': self.content,
            'version': self.version,
            'status': self.status,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Epic(db.Model):
    """Epics - large bodies of work broken into stories"""
    __tablename__ = 'epics'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    epic_key = db.Column(db.String(20), nullable=False)  # E1, E2, etc.
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    acceptance_criteria = db.Column(db.Text)
    priority = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='backlog')  # backlog, in_progress, done
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stories = db.relationship('Story', backref='epic', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def story_count(self):
        return self.stories.count()
    
    @property
    def completed_stories(self):
        return self.stories.filter_by(status='done').count()
    
    @property
    def progress(self):
        total = self.story_count
        if total == 0:
            return 0
        return int((self.completed_stories / total) * 100)
    
    def to_dict(self, include_stories=False):
        data = {
            'id': self.id,
            'project_id': self.project_id,
            'epic_key': self.epic_key,
            'title': self.title,
            'description': self.description,
            'acceptance_criteria': self.acceptance_criteria,
            'priority': self.priority,
            'status': self.status,
            'order': self.order,
            'story_count': self.story_count,
            'completed_stories': self.completed_stories,
            'progress': self.progress,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_stories:
            data['stories'] = [s.to_dict() for s in self.stories.order_by(Story.order).all()]
        return data


class Story(db.Model):
    """User Stories within epics"""
    __tablename__ = 'stories'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    epic_id = db.Column(db.Integer, db.ForeignKey('epics.id'), nullable=False)
    story_key = db.Column(db.String(20), nullable=False)  # S1.1, S1.2, etc.
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    user_story = db.Column(db.Text)  # As a [user], I want to [action], so that [benefit]
    acceptance_criteria = db.Column(db.Text)
    technical_notes = db.Column(db.Text)
    priority = db.Column(db.String(20), default='medium')  # critical, high, medium, low
    story_points = db.Column(db.Integer)
    status = db.Column(db.String(50), default='backlog')  # backlog, ready, in_progress, review, done
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprints.id'))
    order = db.Column(db.Integer, default=0)
    assigned_agent = db.Column(db.String(50))  # DEV, SM, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = db.relationship('Task', backref='story', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def task_count(self):
        return self.tasks.count()
    
    @property
    def completed_tasks(self):
        return self.tasks.filter_by(status='done').count()
    
    def to_dict(self, include_tasks=False):
        data = {
            'id': self.id,
            'project_id': self.project_id,
            'epic_id': self.epic_id,
            'story_key': self.story_key,
            'title': self.title,
            'description': self.description,
            'user_story': self.user_story,
            'acceptance_criteria': self.acceptance_criteria,
            'technical_notes': self.technical_notes,
            'priority': self.priority,
            'story_points': self.story_points,
            'status': self.status,
            'sprint_id': self.sprint_id,
            'order': self.order,
            'assigned_agent': self.assigned_agent,
            'task_count': self.task_count,
            'completed_tasks': self.completed_tasks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_tasks:
            data['tasks'] = [t.to_dict() for t in self.tasks.order_by(Task.order).all()]
        return data


class Task(db.Model):
    """Implementation tasks within stories"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)
    task_key = db.Column(db.String(30))  # T1.1.1, T1.1.2, etc.
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    task_type = db.Column(db.String(50), default='implementation')  # implementation, testing, documentation, review
    status = db.Column(db.String(50), default='todo')  # todo, in_progress, done
    order = db.Column(db.Integer, default=0)
    estimated_hours = db.Column(db.Float)
    actual_hours = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'story_id': self.story_id,
            'task_key': self.task_key,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type,
            'status': self.status,
            'order': self.order,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Sprint(db.Model):
    """Sprints for organizing work"""
    __tablename__ = 'sprints'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    sprint_number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100))
    goal = db.Column(db.Text)
    status = db.Column(db.String(50), default='planning')  # planning, active, completed
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    velocity = db.Column(db.Integer)  # Story points completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stories = db.relationship('Story', backref='sprint', lazy='dynamic')
    
    @property
    def total_points(self):
        return sum(s.story_points or 0 for s in self.stories.all())
    
    @property
    def completed_points(self):
        return sum(s.story_points or 0 for s in self.stories.filter_by(status='done').all())
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'sprint_number': self.sprint_number,
            'name': self.name or f'Sprint {self.sprint_number}',
            'goal': self.goal,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'velocity': self.velocity,
            'total_points': self.total_points,
            'completed_points': self.completed_points,
            'story_count': self.stories.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class WorkflowExecution(db.Model):
    """Track workflow execution progress"""
    __tablename__ = 'workflow_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    workflow_id = db.Column(db.String(100), nullable=False)
    workflow_name = db.Column(db.String(255))
    phase = db.Column(db.Integer)
    current_step = db.Column(db.Integer, default=0)
    total_steps = db.Column(db.Integer)
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed, failed
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    step_data = db.Column(db.JSON, default=dict)  # Store step inputs/outputs
    output_document_id = db.Column(db.Integer, db.ForeignKey('documents.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'workflow_id': self.workflow_id,
            'workflow_name': self.workflow_name,
            'phase': self.phase,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'status': self.status,
            'progress': int((self.current_step / self.total_steps * 100)) if self.total_steps else 0,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'step_data': self.step_data,
            'output_document_id': self.output_document_id,
        }
