"""
BMAD Web Dashboard - Project Workflow API
Full CRUD and workflow management for projects, documents, epics, stories, tasks
"""
from flask import Blueprint, jsonify, request
from ..models import Project, Document, Epic, Story, Task, Sprint, WorkflowExecution, Activity
from ..extensions import db
from datetime import datetime

project_api = Blueprint('project_api', __name__)


# ============================================================================
# Project Setup & Configuration
# ============================================================================

@project_api.route('/projects/<int:project_id>/setup', methods=['POST'])
def setup_project(project_id):
    """Initialize project with track and configuration."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    # Update project configuration
    if 'track' in data:
        project.track = data['track']
    if 'project_type' in data:
        project.project_type = data['project_type']
    if 'tech_stack' in data:
        project.tech_stack = data['tech_stack']
    if 'team_size' in data:
        project.team_size = data['team_size']
    if 'description' in data:
        project.description = data['description']
    
    project.status = 'planning'
    project.current_phase = 1
    
    db.session.commit()
    
    # Log activity
    _log_activity(project.id, 'setup', 'Project Initialized', 
                  f'Project configured with {project.track} track', '🚀')
    
    return jsonify({'success': True, 'data': project.to_dict()})


@project_api.route('/projects/<int:project_id>/phase', methods=['PUT'])
def update_phase(project_id):
    """Update project phase."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    new_phase = data.get('phase')
    if new_phase:
        project.current_phase = new_phase
        
        # Update status based on phase
        if new_phase == 1:
            project.status = 'planning'
        elif new_phase == 2:
            project.status = 'planning'
        elif new_phase == 3:
            project.status = 'solutioning'
        elif new_phase == 4:
            project.status = 'implementation'
        
        db.session.commit()
        
        _log_activity(project.id, 'phase', f'Moved to Phase {new_phase}',
                      f'Project advanced to phase {new_phase}', '📈')
    
    return jsonify({'success': True, 'data': project.to_dict()})


@project_api.route('/projects/<int:project_id>/complete-phase', methods=['POST'])
def complete_phase(project_id):
    """Mark a phase as completed."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    phase = data.get('phase')
    if phase == 1:
        project.phase1_completed = True
    elif phase == 2:
        project.phase2_completed = True
    elif phase == 3:
        project.phase3_completed = True
    elif phase == 4:
        project.phase4_completed = True
        project.status = 'completed'
    
    db.session.commit()
    
    _log_activity(project.id, 'phase', f'Phase {phase} Completed',
                  f'Successfully completed phase {phase}', '✅')
    
    return jsonify({'success': True, 'data': project.to_dict()})


# ============================================================================
# Document Management (PRD, Architecture, etc.)
# ============================================================================

@project_api.route('/projects/<int:project_id>/documents', methods=['GET'])
def get_documents(project_id):
    """Get all documents for a project."""
    project = Project.query.get_or_404(project_id)
    doc_type = request.args.get('type')
    
    query = Document.query.filter_by(project_id=project_id)
    if doc_type:
        query = query.filter_by(doc_type=doc_type)
    
    documents = query.order_by(Document.created_at.desc()).all()
    return jsonify({'success': True, 'data': [d.to_dict() for d in documents]})


@project_api.route('/projects/<int:project_id>/documents', methods=['POST'])
def create_document(project_id):
    """Create a new document."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    doc = Document(
        project_id=project_id,
        doc_type=data.get('doc_type', 'general'),
        title=data.get('title', 'Untitled Document'),
        content=data.get('content', ''),
        status=data.get('status', 'draft'),
    )
    
    db.session.add(doc)
    db.session.commit()
    
    # Link to project if it's a key document
    if doc.doc_type == 'prd':
        project.prd_id = doc.id
    elif doc.doc_type == 'architecture':
        project.architecture_id = doc.id
    elif doc.doc_type == 'tech-spec':
        project.tech_spec_id = doc.id
    
    db.session.commit()
    
    _log_activity(project_id, 'document', f'{doc.doc_type.upper()} Created',
                  f'Document "{doc.title}" created', '📄')
    
    return jsonify({'success': True, 'data': doc.to_dict()}), 201


@project_api.route('/documents/<int:doc_id>', methods=['GET'])
def get_document(doc_id):
    """Get a specific document."""
    doc = Document.query.get_or_404(doc_id)
    return jsonify({'success': True, 'data': doc.to_dict()})


@project_api.route('/documents/<int:doc_id>', methods=['PUT'])
def update_document(doc_id):
    """Update a document."""
    doc = Document.query.get_or_404(doc_id)
    data = request.get_json()
    
    if 'title' in data:
        doc.title = data['title']
    if 'content' in data:
        doc.content = data['content']
        doc.version += 1
    if 'status' in data:
        doc.status = data['status']
    
    db.session.commit()
    
    return jsonify({'success': True, 'data': doc.to_dict()})


# ============================================================================
# Epic Management
# ============================================================================

@project_api.route('/projects/<int:project_id>/epics', methods=['GET'])
def get_epics(project_id):
    """Get all epics for a project."""
    project = Project.query.get_or_404(project_id)
    epics = Epic.query.filter_by(project_id=project_id).order_by(Epic.order).all()
    
    include_stories = request.args.get('include_stories', 'false').lower() == 'true'
    return jsonify({
        'success': True, 
        'data': [e.to_dict(include_stories=include_stories) for e in epics]
    })


@project_api.route('/projects/<int:project_id>/epics', methods=['POST'])
def create_epic(project_id):
    """Create a new epic."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    # Auto-generate epic key
    existing_count = Epic.query.filter_by(project_id=project_id).count()
    epic_key = data.get('epic_key', f'E{existing_count + 1}')
    
    epic = Epic(
        project_id=project_id,
        epic_key=epic_key,
        title=data.get('title', 'New Epic'),
        description=data.get('description'),
        acceptance_criteria=data.get('acceptance_criteria'),
        priority=data.get('priority', 0),
        order=existing_count,
    )
    
    db.session.add(epic)
    db.session.commit()
    
    _log_activity(project_id, 'epic', f'Epic {epic_key} Created',
                  f'Epic "{epic.title}" added to backlog', '📦')
    
    return jsonify({'success': True, 'data': epic.to_dict()}), 201


@project_api.route('/epics/<int:epic_id>', methods=['GET'])
def get_epic(epic_id):
    """Get a specific epic with stories."""
    epic = Epic.query.get_or_404(epic_id)
    return jsonify({'success': True, 'data': epic.to_dict(include_stories=True)})


@project_api.route('/epics/<int:epic_id>', methods=['PUT'])
def update_epic(epic_id):
    """Update an epic."""
    epic = Epic.query.get_or_404(epic_id)
    data = request.get_json()
    
    for field in ['title', 'description', 'acceptance_criteria', 'priority', 'status', 'order']:
        if field in data:
            setattr(epic, field, data[field])
    
    db.session.commit()
    return jsonify({'success': True, 'data': epic.to_dict()})


@project_api.route('/epics/<int:epic_id>', methods=['DELETE'])
def delete_epic(epic_id):
    """Delete an epic and its stories."""
    epic = Epic.query.get_or_404(epic_id)
    db.session.delete(epic)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Epic deleted'})


# ============================================================================
# Story Management
# ============================================================================

@project_api.route('/epics/<int:epic_id>/stories', methods=['GET'])
def get_stories(epic_id):
    """Get all stories for an epic."""
    epic = Epic.query.get_or_404(epic_id)
    stories = Story.query.filter_by(epic_id=epic_id).order_by(Story.order).all()
    
    include_tasks = request.args.get('include_tasks', 'false').lower() == 'true'
    return jsonify({
        'success': True,
        'data': [s.to_dict(include_tasks=include_tasks) for s in stories]
    })


@project_api.route('/epics/<int:epic_id>/stories', methods=['POST'])
def create_story(epic_id):
    """Create a new story."""
    epic = Epic.query.get_or_404(epic_id)
    data = request.get_json()
    
    # Auto-generate story key
    existing_count = Story.query.filter_by(epic_id=epic_id).count()
    story_key = data.get('story_key', f'S{epic.epic_key[1:]}.{existing_count + 1}')
    
    story = Story(
        project_id=epic.project_id,
        epic_id=epic_id,
        story_key=story_key,
        title=data.get('title', 'New Story'),
        description=data.get('description'),
        user_story=data.get('user_story'),
        acceptance_criteria=data.get('acceptance_criteria'),
        technical_notes=data.get('technical_notes'),
        priority=data.get('priority', 'medium'),
        story_points=data.get('story_points'),
        order=existing_count,
    )
    
    db.session.add(story)
    db.session.commit()
    
    _log_activity(epic.project_id, 'story', f'Story {story_key} Created',
                  f'Story "{story.title}" added to {epic.epic_key}', '📝')
    
    return jsonify({'success': True, 'data': story.to_dict()}), 201


@project_api.route('/stories/<int:story_id>', methods=['GET'])
def get_story(story_id):
    """Get a specific story with tasks."""
    story = Story.query.get_or_404(story_id)
    return jsonify({'success': True, 'data': story.to_dict(include_tasks=True)})


@project_api.route('/stories/<int:story_id>', methods=['PUT'])
def update_story(story_id):
    """Update a story."""
    story = Story.query.get_or_404(story_id)
    data = request.get_json()
    
    for field in ['title', 'description', 'user_story', 'acceptance_criteria', 
                  'technical_notes', 'priority', 'story_points', 'status', 
                  'sprint_id', 'order', 'assigned_agent']:
        if field in data:
            setattr(story, field, data[field])
    
    # Log status changes
    if 'status' in data:
        _log_activity(story.project_id, 'story', f'Story {story.story_key} → {data["status"]}',
                      f'Story status updated', '🔄')
    
    db.session.commit()
    return jsonify({'success': True, 'data': story.to_dict()})


@project_api.route('/stories/<int:story_id>', methods=['DELETE'])
def delete_story(story_id):
    """Delete a story and its tasks."""
    story = Story.query.get_or_404(story_id)
    db.session.delete(story)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Story deleted'})


# ============================================================================
# Task Management
# ============================================================================

@project_api.route('/stories/<int:story_id>/tasks', methods=['GET'])
def get_tasks(story_id):
    """Get all tasks for a story."""
    story = Story.query.get_or_404(story_id)
    tasks = Task.query.filter_by(story_id=story_id).order_by(Task.order).all()
    return jsonify({'success': True, 'data': [t.to_dict() for t in tasks]})


@project_api.route('/stories/<int:story_id>/tasks', methods=['POST'])
def create_task(story_id):
    """Create a new task."""
    story = Story.query.get_or_404(story_id)
    data = request.get_json()
    
    # Auto-generate task key
    existing_count = Task.query.filter_by(story_id=story_id).count()
    task_key = data.get('task_key', f'T{story.story_key[1:]}.{existing_count + 1}')
    
    task = Task(
        story_id=story_id,
        task_key=task_key,
        title=data.get('title', 'New Task'),
        description=data.get('description'),
        task_type=data.get('task_type', 'implementation'),
        estimated_hours=data.get('estimated_hours'),
        order=existing_count,
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify({'success': True, 'data': task.to_dict()}), 201


@project_api.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task."""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    for field in ['title', 'description', 'task_type', 'status', 'order',
                  'estimated_hours', 'actual_hours']:
        if field in data:
            setattr(task, field, data[field])
    
    db.session.commit()
    return jsonify({'success': True, 'data': task.to_dict()})


@project_api.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task."""
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Task deleted'})


# ============================================================================
# Sprint Management
# ============================================================================

@project_api.route('/projects/<int:project_id>/sprints', methods=['GET'])
def get_sprints(project_id):
    """Get all sprints for a project."""
    project = Project.query.get_or_404(project_id)
    sprints = Sprint.query.filter_by(project_id=project_id).order_by(Sprint.sprint_number).all()
    return jsonify({'success': True, 'data': [s.to_dict() for s in sprints]})


@project_api.route('/projects/<int:project_id>/sprints', methods=['POST'])
def create_sprint(project_id):
    """Create a new sprint."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    # Get next sprint number
    last_sprint = Sprint.query.filter_by(project_id=project_id).order_by(Sprint.sprint_number.desc()).first()
    sprint_number = (last_sprint.sprint_number + 1) if last_sprint else 1
    
    sprint = Sprint(
        project_id=project_id,
        sprint_number=sprint_number,
        name=data.get('name', f'Sprint {sprint_number}'),
        goal=data.get('goal'),
        start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
        end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
    )
    
    db.session.add(sprint)
    db.session.commit()
    
    # Set as current sprint
    project.current_sprint_id = sprint.id
    db.session.commit()
    
    _log_activity(project_id, 'sprint', f'Sprint {sprint_number} Created',
                  f'New sprint started: {sprint.name}', '🏃')
    
    return jsonify({'success': True, 'data': sprint.to_dict()}), 201


@project_api.route('/sprints/<int:sprint_id>', methods=['PUT'])
def update_sprint(sprint_id):
    """Update a sprint."""
    sprint = Sprint.query.get_or_404(sprint_id)
    data = request.get_json()
    
    for field in ['name', 'goal', 'status', 'velocity']:
        if field in data:
            setattr(sprint, field, data[field])
    
    if 'start_date' in data:
        sprint.start_date = datetime.fromisoformat(data['start_date']) if data['start_date'] else None
    if 'end_date' in data:
        sprint.end_date = datetime.fromisoformat(data['end_date']) if data['end_date'] else None
    
    db.session.commit()
    return jsonify({'success': True, 'data': sprint.to_dict()})


@project_api.route('/sprints/<int:sprint_id>/stories', methods=['POST'])
def add_stories_to_sprint(sprint_id):
    """Add stories to a sprint."""
    sprint = Sprint.query.get_or_404(sprint_id)
    data = request.get_json()
    
    story_ids = data.get('story_ids', [])
    for story_id in story_ids:
        story = Story.query.get(story_id)
        if story:
            story.sprint_id = sprint_id
            story.status = 'ready'
    
    db.session.commit()
    return jsonify({'success': True, 'data': sprint.to_dict()})


# ============================================================================
# Board Views
# ============================================================================

@project_api.route('/projects/<int:project_id>/board', methods=['GET'])
def get_board(project_id):
    """Get Kanban board data for a project."""
    project = Project.query.get_or_404(project_id)
    sprint_id = request.args.get('sprint_id', type=int)
    
    # Get stories, optionally filtered by sprint
    query = Story.query.filter_by(project_id=project_id)
    if sprint_id:
        query = query.filter_by(sprint_id=sprint_id)
    
    stories = query.all()
    
    # Group by status
    board = {
        'backlog': [],
        'ready': [],
        'in_progress': [],
        'review': [],
        'done': []
    }
    
    for story in stories:
        status = story.status if story.status in board else 'backlog'
        board[status].append(story.to_dict(include_tasks=True))
    
    return jsonify({'success': True, 'data': board})


@project_api.route('/projects/<int:project_id>/summary', methods=['GET'])
def get_project_summary(project_id):
    """Get comprehensive project summary."""
    project = Project.query.get_or_404(project_id)
    
    # Get documents
    documents = Document.query.filter_by(project_id=project_id).all()
    
    # Get epics with stories
    epics = Epic.query.filter_by(project_id=project_id).order_by(Epic.order).all()
    
    # Get current sprint
    current_sprint = Sprint.query.get(project.current_sprint_id) if project.current_sprint_id else None
    
    # Calculate stats
    total_stories = Story.query.filter_by(project_id=project_id).count()
    done_stories = Story.query.filter_by(project_id=project_id, status='done').count()
    in_progress_stories = Story.query.filter_by(project_id=project_id, status='in_progress').count()
    
    return jsonify({
        'success': True,
        'data': {
            'project': project.to_dict(),
            'documents': [d.to_dict() for d in documents],
            'epics': [e.to_dict(include_stories=True) for e in epics],
            'current_sprint': current_sprint.to_dict() if current_sprint else None,
            'stats': {
                'total_epics': len(epics),
                'total_stories': total_stories,
                'done_stories': done_stories,
                'in_progress_stories': in_progress_stories,
                'completion_rate': int((done_stories / total_stories * 100)) if total_stories > 0 else 0,
            }
        }
    })


# ============================================================================
# Bulk Operations
# ============================================================================

@project_api.route('/projects/<int:project_id>/import-epics', methods=['POST'])
def import_epics(project_id):
    """Bulk import epics and stories from structured data."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    epics_data = data.get('epics', [])
    created_epics = []
    
    for i, epic_data in enumerate(epics_data):
        epic = Epic(
            project_id=project_id,
            epic_key=epic_data.get('epic_key', f'E{i + 1}'),
            title=epic_data.get('title'),
            description=epic_data.get('description'),
            acceptance_criteria=epic_data.get('acceptance_criteria'),
            order=i,
        )
        db.session.add(epic)
        db.session.flush()  # Get the epic ID
        
        # Create stories for this epic
        for j, story_data in enumerate(epic_data.get('stories', [])):
            story = Story(
                project_id=project_id,
                epic_id=epic.id,
                story_key=story_data.get('story_key', f'S{i + 1}.{j + 1}'),
                title=story_data.get('title'),
                description=story_data.get('description'),
                user_story=story_data.get('user_story'),
                acceptance_criteria=story_data.get('acceptance_criteria'),
                priority=story_data.get('priority', 'medium'),
                story_points=story_data.get('story_points'),
                order=j,
            )
            db.session.add(story)
        
        created_epics.append(epic)
    
    db.session.commit()
    
    _log_activity(project_id, 'import', 'Epics Imported',
                  f'Imported {len(created_epics)} epics with stories', '📥')
    
    return jsonify({
        'success': True,
        'data': [e.to_dict(include_stories=True) for e in created_epics]
    }), 201


# ============================================================================
# Helper Functions
# ============================================================================

def _log_activity(project_id, activity_type, title, description, icon):
    """Log an activity."""
    activity = Activity(
        project_id=project_id,
        activity_type=activity_type,
        title=title,
        description=description,
        icon=icon,
    )
    db.session.add(activity)
    db.session.commit()
