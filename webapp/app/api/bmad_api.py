"""
BMAD Web Dashboard - BMAD Project API
File-based API for managing BMAD projects, documents, epics, stories.
"""
from flask import Blueprint, jsonify, request
from ..services import BmadProjectService
from ..models import Project, Activity
from ..extensions import db
from datetime import datetime

bmad_api = Blueprint('bmad_api', __name__)


# ============================================================================
# Project Scanning & Management
# ============================================================================

@bmad_api.route('/scan', methods=['POST'])
def scan_project():
    """Scan a directory for BMAD project structure."""
    data = request.get_json()
    project_path = data.get('path')
    
    if not project_path:
        return jsonify({'success': False, 'error': 'Path is required'}), 400
    
    result = BmadProjectService.scan_project(project_path)
    
    if 'error' in result:
        return jsonify({'success': False, 'error': result['error']}), 400
    
    return jsonify({'success': True, 'data': result})


@bmad_api.route('/projects/<int:project_id>/scan', methods=['GET'])
def scan_saved_project(project_id):
    """Scan a saved project's directory."""
    project = Project.query.get_or_404(project_id)
    
    result = BmadProjectService.scan_project(project.path)
    
    if 'error' in result:
        return jsonify({'success': False, 'error': result['error']}), 400
    
    # Update project with scanned data
    if result.get('track'):
        project.track = result['track']
    project.current_phase = result.get('current_phase', 0)
    db.session.commit()
    
    return jsonify({'success': True, 'data': result})


@bmad_api.route('/projects/<int:project_id>/initialize', methods=['POST'])
def initialize_project(project_id):
    """Initialize BMAD structure in a project directory."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    
    result = BmadProjectService.initialize_project(
        project.path,
        project.name,
        track=data.get('track', project.track or 'bmad-method'),
        project_type=data.get('project_type', 'greenfield')
    )
    
    if not result.get('success'):
        return jsonify(result), 400
    
    # Update project status
    project.status = 'planning'
    project.current_phase = 0
    db.session.commit()
    
    # Log activity
    activity = Activity(
        project_id=project.id,
        activity_type='setup',
        title='Project Initialized',
        description=f'BMAD structure created with {data.get("track", "bmad-method")} track',
        icon='🚀'
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify(result)


# ============================================================================
# Document Management
# ============================================================================

@bmad_api.route('/projects/<int:project_id>/documents', methods=['GET'])
def get_project_documents(project_id):
    """Get all documents for a project."""
    project = Project.query.get_or_404(project_id)
    
    scan = BmadProjectService.scan_project(project.path)
    documents = scan.get('documents', [])
    
    return jsonify({'success': True, 'data': documents})


@bmad_api.route('/projects/<int:project_id>/documents/<doc_type>', methods=['GET'])
def get_document(project_id, doc_type):
    """Get a specific document."""
    project = Project.query.get_or_404(project_id)
    
    doc = BmadProjectService.get_document(project.path, doc_type)
    
    if not doc:
        return jsonify({'success': False, 'error': f'Document {doc_type} not found'}), 404
    
    return jsonify({'success': True, 'data': doc})


@bmad_api.route('/documents/save', methods=['POST'])
def save_document():
    """Save document content to file."""
    data = request.get_json()
    doc_path = data.get('path')
    content = data.get('content')
    
    if not doc_path or content is None:
        return jsonify({'success': False, 'error': 'Path and content are required'}), 400
    
    result = BmadProjectService.save_document(doc_path, content)
    return jsonify(result)


@bmad_api.route('/projects/<int:project_id>/documents', methods=['POST'])
def create_document(project_id):
    """Create a new document from template."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    doc_type = data.get('type')
    title = data.get('title', 'New Document')
    
    # Get output folder
    scan = BmadProjectService.scan_project(project.path)
    output_folder = scan.get('output_folder', project.path)
    
    # Generate filename
    import re
    filename = f"{doc_type or 'document'}.md"
    doc_path = f"{output_folder}/{filename}"
    
    # Generate initial content based on type
    templates = {
        'prd': f"""---
stepsCompleted: []
workflowType: 'prd'
---

# Product Requirements Document - {title}

**Author:** User
**Date:** {datetime.now().strftime('%Y-%m-%d')}

## Overview

[Describe the product vision and goals]

## Functional Requirements

### FR-1: [Requirement Name]
[Description]

## Non-Functional Requirements

### NFR-1: [Requirement Name]
[Description]

## Success Metrics

[Define measurable success criteria]
""",
        'architecture': f"""---
stepsCompleted: []
workflowType: 'architecture'
---

# Architecture Document - {title}

**Author:** User
**Date:** {datetime.now().strftime('%Y-%m-%d')}

## Overview

[High-level system overview]

## Tech Stack

[List technologies and frameworks]

## System Components

[Describe main components]

## Data Model

[Database schema and relationships]

## API Design

[API endpoints and contracts]
""",
        'tech-spec': f"""# Technical Specification - {title}

**Date:** {datetime.now().strftime('%Y-%m-%d')}

## Overview

[Brief technical overview]

## Implementation Details

[Technical implementation approach]

## API/Interface Definitions

[Detailed specifications]
""",
        'epics': f"""---
stepsCompleted: []
---

# {title} - Epic Breakdown

## Overview

This document provides the epic and story breakdown.

## Epic 1: [Epic Title]

[Epic description and goals]

### Story 1.1: [Story Title]

As a [user type],
I want [capability],
So that [value/benefit].

**Acceptance Criteria:**

**Given** [precondition]
**When** [action]
**Then** [expected outcome]
"""
    }
    
    content = templates.get(doc_type, f"# {title}\n\nCreated: {datetime.now().strftime('%Y-%m-%d')}\n")
    
    result = BmadProjectService.save_document(doc_path, content)
    
    if result.get('success'):
        # Log activity
        activity = Activity(
            project_id=project.id,
            activity_type='document',
            title=f'{doc_type.upper()} Created',
            description=f'Created {filename}',
            icon='📄'
        )
        db.session.add(activity)
        db.session.commit()
    
    return jsonify(result)


# ============================================================================
# Workflow Status
# ============================================================================

@bmad_api.route('/projects/<int:project_id>/workflow-status', methods=['GET'])
def get_workflow_status(project_id):
    """Get workflow status for a project."""
    project = Project.query.get_or_404(project_id)
    
    scan = BmadProjectService.scan_project(project.path)
    workflow_status = scan.get('workflow_status')
    
    if not workflow_status:
        return jsonify({'success': False, 'error': 'Workflow status not found'}), 404
    
    return jsonify({'success': True, 'data': workflow_status})


@bmad_api.route('/projects/<int:project_id>/workflow-status', methods=['PUT'])
def update_workflow_status(project_id):
    """Update workflow status."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    scan = BmadProjectService.scan_project(project.path)
    workflow_status = scan.get('workflow_status')
    
    if not workflow_status:
        return jsonify({'success': False, 'error': 'Workflow status not found'}), 404
    
    file_path = workflow_status.get('_file_path')
    
    # Update status
    import yaml
    current_status = workflow_status.get('workflow_status', {})
    if isinstance(current_status, dict):
        current_status.update(data.get('workflow_status', {}))
    
    workflow_status['workflow_status'] = current_status
    
    # Save to file
    save_data = {k: v for k, v in workflow_status.items() if not k.startswith('_')}
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(save_data, f, default_flow_style=False, sort_keys=False)
        
        return jsonify({'success': True, 'data': workflow_status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# Sprint & Story Management
# ============================================================================

@bmad_api.route('/projects/<int:project_id>/sprint-status', methods=['GET'])
def get_sprint_status(project_id):
    """Get sprint status for a project."""
    project = Project.query.get_or_404(project_id)
    
    scan = BmadProjectService.scan_project(project.path)
    sprint_status = scan.get('sprint_status')
    
    if not sprint_status:
        return jsonify({'success': False, 'error': 'Sprint status not found', 'data': None})
    
    return jsonify({'success': True, 'data': sprint_status})


@bmad_api.route('/projects/<int:project_id>/sprint-status', methods=['PUT'])
def update_sprint_status(project_id):
    """Update sprint status (story statuses)."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    updates = data.get('updates', {})
    
    result = BmadProjectService.update_sprint_status(project.path, updates)
    
    if result.get('success'):
        # Log activity
        activity = Activity(
            project_id=project.id,
            activity_type='sprint',
            title='Sprint Status Updated',
            description=f'Updated {len(updates)} items',
            icon='📊'
        )
        db.session.add(activity)
        db.session.commit()
    
    return jsonify(result)


@bmad_api.route('/projects/<int:project_id>/epics', methods=['GET'])
def get_epics(project_id):
    """Get epics from project files."""
    project = Project.query.get_or_404(project_id)
    
    scan = BmadProjectService.scan_project(project.path)
    epics = scan.get('epics', [])
    
    return jsonify({'success': True, 'data': epics})


@bmad_api.route('/projects/<int:project_id>/stories', methods=['GET'])
def get_stories(project_id):
    """Get story files from project."""
    project = Project.query.get_or_404(project_id)
    
    stories = BmadProjectService.get_story_files(project.path)
    
    return jsonify({'success': True, 'data': stories})


@bmad_api.route('/projects/<int:project_id>/stories', methods=['POST'])
def create_story(project_id):
    """Create a new story file."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    epic_num = data.get('epic_num', 1)
    story_num = data.get('story_num', 1)
    story_data = {
        'title': data.get('title', 'New Story'),
        'role': data.get('role', 'user'),
        'action': data.get('action', 'perform an action'),
        'benefit': data.get('benefit', 'achieve a goal'),
        'acceptance_criteria': data.get('acceptance_criteria', ''),
        'technical_notes': data.get('technical_notes', ''),
    }
    
    result = BmadProjectService.create_story_file(
        project.path, epic_num, story_num, story_data
    )
    
    if result.get('success'):
        # Update sprint status if exists
        BmadProjectService.update_sprint_status(
            project.path, 
            {f"{epic_num}-{story_num}-{data.get('slug', 'story')}": 'ready-for-dev'}
        )
        
        # Log activity
        activity = Activity(
            project_id=project.id,
            activity_type='story',
            title=f'Story S{epic_num}.{story_num} Created',
            description=story_data['title'],
            icon='📝'
        )
        db.session.add(activity)
        db.session.commit()
    
    return jsonify(result)


@bmad_api.route('/stories/save', methods=['POST'])
def save_story():
    """Save story content to file."""
    data = request.get_json()
    story_path = data.get('path')
    content = data.get('content')
    
    if not story_path or content is None:
        return jsonify({'success': False, 'error': 'Path and content required'}), 400
    
    result = BmadProjectService.save_document(story_path, content)
    return jsonify(result)


# ============================================================================
# Project Summary
# ============================================================================

@bmad_api.route('/projects/<int:project_id>/summary', methods=['GET'])
def get_project_summary(project_id):
    """Get comprehensive project summary."""
    project = Project.query.get_or_404(project_id)
    
    scan = BmadProjectService.scan_project(project.path)
    
    # Get story files
    story_files = BmadProjectService.get_story_files(project.path)
    
    # Calculate statistics
    total_epics = len(scan.get('epics', []))
    total_stories = sum(len(e.get('stories', [])) for e in scan.get('epics', []))
    story_files_count = len(story_files)
    
    # Count by status from sprint status
    sprint_status = scan.get('sprint_status', {})
    dev_status = sprint_status.get('development_status', {}) if sprint_status else {}
    
    status_counts = {
        'backlog': 0,
        'ready-for-dev': 0,
        'in-progress': 0,
        'review': 0,
        'done': 0
    }
    
    for key, status in dev_status.items():
        if status in status_counts:
            status_counts[status] += 1
    
    return jsonify({
        'success': True,
        'data': {
            'project': project.to_dict(),
            'scan': scan,
            'story_files': story_files,
            'stats': {
                'total_epics': total_epics,
                'total_stories': total_stories,
                'story_files': story_files_count,
                'status_counts': status_counts,
                'completion_rate': int((status_counts['done'] / total_stories * 100)) if total_stories > 0 else 0,
            }
        }
    })
