"""
BMAD Web Dashboard - API Blueprint
"""
from flask import Blueprint, jsonify, request
from ..services import AgentService, WorkflowService, ModuleService
from ..models import Project, WorkflowStatus, Activity
from ..extensions import db
from datetime import datetime

api_bp = Blueprint('api', __name__)

# Import and register BMAD API
from .bmad_api import bmad_api
api_bp.register_blueprint(bmad_api, url_prefix='/bmad')


# ============================================================================
# Agent Endpoints
# ============================================================================

@api_bp.route('/agents')
def get_agents():
    """Get all agents."""
    module = request.args.get('module')
    
    if module:
        agents = AgentService.get_agents_from_module(module)
    else:
        agents = AgentService.get_all_agents()
    
    return jsonify({
        'success': True,
        'data': agents,
        'count': len(agents)
    })


@api_bp.route('/agents/<module>/<agent_id>')
def get_agent(module, agent_id):
    """Get a specific agent."""
    agent = AgentService.get_agent_by_id(module, agent_id)
    
    if not agent:
        return jsonify({'success': False, 'error': 'Agent not found'}), 404
    
    return jsonify({'success': True, 'data': agent})


# ============================================================================
# Workflow Endpoints
# ============================================================================

@api_bp.route('/workflows')
def get_workflows():
    """Get all workflows."""
    module = request.args.get('module')
    phase = request.args.get('phase', type=int)
    
    if module:
        workflows = WorkflowService.get_workflows_from_module(module)
    else:
        workflows = WorkflowService.get_all_workflows()
    
    if phase:
        workflows = [w for w in workflows if w.get('phase') == phase]
    
    return jsonify({
        'success': True,
        'data': workflows,
        'count': len(workflows)
    })


@api_bp.route('/workflows/stats')
def get_workflow_stats():
    """Get workflow statistics."""
    stats = WorkflowService.get_workflow_stats()
    return jsonify({'success': True, 'data': stats})


@api_bp.route('/workflows/phases')
def get_phases():
    """Get workflow phases."""
    phases = WorkflowService.get_phases()
    return jsonify({'success': True, 'data': phases})


# ============================================================================
# Module Endpoints
# ============================================================================

@api_bp.route('/modules')
def get_modules():
    """Get all modules."""
    modules = AgentService.get_modules()
    return jsonify({
        'success': True,
        'data': modules,
        'count': len(modules)
    })


@api_bp.route('/modules/<module_code>')
def get_module(module_code):
    """Get a specific module with details."""
    modules = ModuleService.get_all_modules_detailed()
    module = next((m for m in modules if m['code'] == module_code), None)
    
    if not module:
        return jsonify({'success': False, 'error': 'Module not found'}), 404
    
    return jsonify({'success': True, 'data': module})


# ============================================================================
# Project Endpoints
# ============================================================================

@api_bp.route('/projects', methods=['GET'])
def get_projects():
    """Get all projects."""
    projects = Project.query.order_by(Project.updated_at.desc()).all()
    return jsonify({
        'success': True,
        'data': [p.to_dict() for p in projects],
        'count': len(projects)
    })


@api_bp.route('/projects', methods=['POST'])
def create_project():
    """Create a new project."""
    data = request.get_json()
    
    if not data or 'name' not in data or 'path' not in data:
        return jsonify({'success': False, 'error': 'Name and path are required'}), 400
    
    project = Project(
        name=data['name'],
        description=data.get('description'),
        path=data['path'],
        track=data.get('track', 'bmad-method'),
    )
    
    db.session.add(project)
    db.session.commit()
    
    # Log activity
    activity = Activity(
        project_id=project.id,
        activity_type='project',
        title='Project Created',
        description=f'Project "{project.name}" was created',
        icon='🆕',
    )
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'success': True, 'data': project.to_dict()}), 201


@api_bp.route('/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project."""
    project = Project.query.get_or_404(project_id)
    return jsonify({'success': True, 'data': project.to_dict()})


@api_bp.route('/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update a project."""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    if 'name' in data:
        project.name = data['name']
    if 'description' in data:
        project.description = data['description']
    if 'track' in data:
        project.track = data['track']
    if 'current_phase' in data:
        project.current_phase = data['current_phase']
    if 'status' in data:
        project.status = data['status']
    
    db.session.commit()
    
    return jsonify({'success': True, 'data': project.to_dict()})


@api_bp.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project."""
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Project deleted'})


# ============================================================================
# Activity Endpoints
# ============================================================================

@api_bp.route('/activities')
def get_activities():
    """Get recent activities."""
    limit = request.args.get('limit', 20, type=int)
    project_id = request.args.get('project_id', type=int)
    
    query = Activity.query.order_by(Activity.created_at.desc())
    
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    activities = query.limit(limit).all()
    
    return jsonify({
        'success': True,
        'data': [a.to_dict() for a in activities],
        'count': len(activities)
    })


# ============================================================================
# Dashboard Stats
# ============================================================================

@api_bp.route('/stats')
def get_stats():
    """Get dashboard statistics."""
    agents = AgentService.get_all_agents()
    workflows = WorkflowService.get_all_workflows()
    modules = AgentService.get_modules()
    workflow_stats = WorkflowService.get_workflow_stats()
    
    project_count = Project.query.count()
    active_projects = Project.query.filter_by(status='active').count()
    
    return jsonify({
        'success': True,
        'data': {
            'agents': len(agents),
            'workflows': len(workflows),
            'modules': len(modules),
            'projects': project_count,
            'active_projects': active_projects,
            'workflow_stats': workflow_stats,
        }
    })
