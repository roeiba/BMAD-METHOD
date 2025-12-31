"""
BMAD Web Dashboard - Agent Service
Handles parsing and management of BMAD agents.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from flask import current_app


class AgentService:
    """Service for managing BMAD agents."""
    
    # Module metadata with colors and descriptions
    MODULE_INFO = {
        'core': {
            'name': 'Core',
            'description': 'Core BMAD functionality and orchestration',
            'color': '#6366f1',  # Indigo
            'icon': '⚡'
        },
        'bmm': {
            'name': 'BMad Method',
            'description': 'Software & game development workflows',
            'color': '#10b981',  # Emerald
            'icon': '🚀'
        },
        'bmb': {
            'name': 'BMad Builder',
            'description': 'Create custom agents and workflows',
            'color': '#f59e0b',  # Amber
            'icon': '🔧'
        },
        'cis': {
            'name': 'Creative Intelligence',
            'description': 'Innovation and creative thinking',
            'color': '#ec4899',  # Pink
            'icon': '💡'
        },
        'bmgd': {
            'name': 'Game Development',
            'description': 'Specialized game development workflows',
            'color': '#8b5cf6',  # Violet
            'icon': '🎮'
        }
    }
    
    @classmethod
    def get_all_agents(cls) -> List[Dict]:
        """Get all agents from all modules."""
        agents = []
        
        # Get core agents
        core_agents = cls.get_agents_from_module('core')
        agents.extend(core_agents)
        
        # Get module agents
        modules_path = Path(current_app.config['BMAD_MODULES_PATH'])
        if modules_path.exists():
            for module_dir in modules_path.iterdir():
                if module_dir.is_dir():
                    module_agents = cls.get_agents_from_module(module_dir.name)
                    agents.extend(module_agents)
        
        return agents
    
    @classmethod
    def get_agents_from_module(cls, module_code: str) -> List[Dict]:
        """Get all agents from a specific module."""
        agents = []
        
        if module_code == 'core':
            agents_path = Path(current_app.config['BMAD_CORE_PATH']) / 'agents'
        else:
            agents_path = Path(current_app.config['BMAD_MODULES_PATH']) / module_code / 'agents'
        
        if not agents_path.exists():
            return agents
        
        # Find all .agent.yaml files
        for agent_file in agents_path.rglob('*.agent.yaml'):
            agent_data = cls.parse_agent_file(agent_file, module_code)
            if agent_data:
                agents.append(agent_data)
        
        return agents
    
    @classmethod
    def parse_agent_file(cls, file_path: Path, module_code: str) -> Optional[Dict]:
        """Parse a single agent YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
            
            if not content or 'agent' not in content:
                return None
            
            agent = content['agent']
            metadata = agent.get('metadata', {})
            persona = agent.get('persona', {})
            menu = agent.get('menu', [])
            
            # Get module info
            module_info = cls.MODULE_INFO.get(module_code, {
                'name': module_code.upper(),
                'description': f'{module_code} module',
                'color': '#6b7280',
                'icon': '📦'
            })
            
            return {
                'id': metadata.get('id', file_path.stem),
                'name': metadata.get('name', 'Unknown'),
                'title': metadata.get('title', 'Agent'),
                'icon': metadata.get('icon', '🤖'),
                'module': module_code,
                'module_name': module_info['name'],
                'module_color': module_info['color'],
                'module_icon': module_info['icon'],
                'file_path': str(file_path),
                'persona': {
                    'role': persona.get('role', ''),
                    'identity': persona.get('identity', ''),
                    'communication_style': persona.get('communication_style', ''),
                    'principles': persona.get('principles', [])
                },
                'menu': cls._parse_menu(menu),
                'menu_count': len(menu),
                'has_discussion': agent.get('discussion', False),
            }
        except Exception as e:
            current_app.logger.error(f"Error parsing agent file {file_path}: {e}")
            return None
    
    @classmethod
    def _parse_menu(cls, menu: List) -> List[Dict]:
        """Parse agent menu items."""
        parsed_menu = []
        
        for item in menu:
            if isinstance(item, dict):
                # Handle legacy format
                if 'trigger' in item:
                    parsed_menu.append({
                        'trigger': item.get('trigger', ''),
                        'description': item.get('description', ''),
                        'type': cls._get_command_type(item),
                        'target': cls._get_command_target(item),
                        'ide_only': item.get('ide-only', False),
                        'web_only': item.get('web-only', False),
                    })
                # Handle multi format
                elif 'multi' in item:
                    triggers = item.get('triggers', [])
                    parsed_menu.append({
                        'trigger': item.get('multi', ''),
                        'description': f'Multi-command: {len(triggers)} options',
                        'type': 'multi',
                        'triggers': triggers,
                    })
        
        return parsed_menu
    
    @classmethod
    def _get_command_type(cls, item: Dict) -> str:
        """Determine the command type from menu item."""
        if 'workflow' in item:
            return 'workflow'
        elif 'exec' in item:
            return 'exec'
        elif 'action' in item:
            return 'action'
        elif 'tmpl' in item:
            return 'template'
        elif 'data' in item:
            return 'data'
        return 'unknown'
    
    @classmethod
    def _get_command_target(cls, item: Dict) -> str:
        """Get the command target from menu item."""
        for key in ['workflow', 'exec', 'action', 'tmpl', 'data']:
            if key in item:
                return item[key]
        return ''
    
    @classmethod
    def get_agent_by_id(cls, module_code: str, agent_id: str) -> Optional[Dict]:
        """Get a specific agent by module and ID."""
        agents = cls.get_agents_from_module(module_code)
        for agent in agents:
            if agent['id'] == agent_id or agent['name'].lower() == agent_id.lower():
                return agent
        return None
    
    @classmethod
    def get_modules(cls) -> List[Dict]:
        """Get all available modules with their info."""
        modules = []
        
        # Add core module
        core_path = Path(current_app.config['BMAD_CORE_PATH'])
        if core_path.exists():
            core_info = cls.MODULE_INFO['core'].copy()
            core_info['code'] = 'core'
            core_info['agent_count'] = len(cls.get_agents_from_module('core'))
            modules.append(core_info)
        
        # Add other modules
        modules_path = Path(current_app.config['BMAD_MODULES_PATH'])
        if modules_path.exists():
            for module_dir in modules_path.iterdir():
                if module_dir.is_dir():
                    module_code = module_dir.name
                    module_info = cls.MODULE_INFO.get(module_code, {
                        'name': module_code.upper(),
                        'description': f'{module_code} module',
                        'color': '#6b7280',
                        'icon': '📦'
                    }).copy()
                    module_info['code'] = module_code
                    module_info['agent_count'] = len(cls.get_agents_from_module(module_code))
                    
                    # Try to get workflow count
                    workflows_path = module_dir / 'workflows'
                    if workflows_path.exists():
                        module_info['workflow_count'] = sum(1 for _ in workflows_path.rglob('workflow.md')) + \
                                                        sum(1 for _ in workflows_path.rglob('workflow.yaml'))
                    else:
                        module_info['workflow_count'] = 0
                    
                    modules.append(module_info)
        
        return modules
