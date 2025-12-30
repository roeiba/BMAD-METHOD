"""
BMAD Web Dashboard - Main Routes
"""
from flask import Blueprint, render_template, current_app
from ..services import AgentService, WorkflowService, ModuleService
from ..models import Project, Activity
from ..extensions import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def dashboard():
    """Main dashboard view."""
    # Get statistics
    agents = AgentService.get_all_agents()
    workflows = WorkflowService.get_all_workflows()
    modules = AgentService.get_modules()
    phases = WorkflowService.get_phases()
    
    # Get workflow stats by phase
    workflow_stats = WorkflowService.get_workflow_stats()
    
    # Get recent activities
    activities = Activity.query.order_by(Activity.created_at.desc()).limit(10).all()
    
    # Get projects
    projects = Project.query.order_by(Project.updated_at.desc()).limit(5).all()
    
    return render_template('dashboard.html',
        agents=agents,
        workflows=workflows,
        modules=modules,
        phases=phases,
        workflow_stats=workflow_stats,
        activities=activities,
        projects=projects,
        agent_count=len(agents),
        workflow_count=len(workflows),
        module_count=len(modules),
    )


@main_bp.route('/agents')
def agents():
    """Agents browser view."""
    agents = AgentService.get_all_agents()
    modules = AgentService.get_modules()
    
    # Group agents by module
    agents_by_module = {}
    for agent in agents:
        module = agent['module']
        if module not in agents_by_module:
            agents_by_module[module] = []
        agents_by_module[module].append(agent)
    
    return render_template('agents.html',
        agents=agents,
        modules=modules,
        agents_by_module=agents_by_module,
    )


@main_bp.route('/agents/<module>/<agent_id>')
def agent_detail(module, agent_id):
    """Agent detail view."""
    agent = AgentService.get_agent_by_id(module, agent_id)
    if not agent:
        return render_template('404.html'), 404
    
    return render_template('agent_detail.html', agent=agent)


@main_bp.route('/workflows')
def workflows():
    """Workflows browser view."""
    all_workflows = WorkflowService.get_all_workflows()
    phases = WorkflowService.get_phases()
    modules = AgentService.get_modules()
    
    # Group workflows by phase
    workflows_by_phase = {1: [], 2: [], 3: [], 4: []}
    for wf in all_workflows:
        phase = wf.get('phase', 2)
        if phase in workflows_by_phase:
            workflows_by_phase[phase].append(wf)
    
    return render_template('workflows.html',
        workflows=all_workflows,
        workflows_by_phase=workflows_by_phase,
        phases=phases,
        modules=modules,
    )


@main_bp.route('/modules')
def modules():
    """Modules browser view."""
    modules = ModuleService.get_all_modules_detailed()
    
    return render_template('modules.html', modules=modules)


@main_bp.route('/modules/<module_code>')
def module_detail(module_code):
    """Module detail view."""
    modules = ModuleService.get_all_modules_detailed()
    module = next((m for m in modules if m['code'] == module_code), None)
    
    if not module:
        return render_template('404.html'), 404
    
    readme = ModuleService.get_module_readme(module_code)
    
    return render_template('module_detail.html', module=module, readme=readme)


@main_bp.route('/projects')
def projects():
    """Projects view."""
    all_projects = Project.query.order_by(Project.updated_at.desc()).all()
    
    return render_template('projects.html', projects=all_projects)


@main_bp.route('/analytics')
def analytics():
    """Analytics view."""
    agents = AgentService.get_all_agents()
    workflows = WorkflowService.get_all_workflows()
    modules = AgentService.get_modules()
    workflow_stats = WorkflowService.get_workflow_stats()
    phases = WorkflowService.get_phases()
    
    return render_template('analytics.html',
        agents=agents,
        workflows=workflows,
        modules=modules,
        workflow_stats=workflow_stats,
        phases=phases,
    )
