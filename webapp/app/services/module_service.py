"""
BMAD Web Dashboard - Module Service
Handles parsing and management of BMAD modules.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from flask import current_app


class ModuleService:
    """Service for managing BMAD modules."""
    
    @classmethod
    def get_module_config(cls, module_code: str) -> Optional[Dict]:
        """Get module configuration from module.yaml."""
        if module_code == 'core':
            module_path = Path(current_app.config['BMAD_CORE_PATH'])
        else:
            module_path = Path(current_app.config['BMAD_MODULES_PATH']) / module_code
        
        config_file = module_path / 'module.yaml'
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            current_app.logger.error(f"Error reading module config {config_file}: {e}")
            return None
    
    @classmethod
    def get_all_modules_detailed(cls) -> List[Dict]:
        """Get detailed information about all modules."""
        from .agent_service import AgentService
        from .workflow_service import WorkflowService
        
        modules = []
        
        # Core module
        core_path = Path(current_app.config['BMAD_CORE_PATH'])
        if core_path.exists():
            core_config = cls.get_module_config('core') or {}
            modules.append({
                'code': 'core',
                'name': core_config.get('name', 'BMad Core'),
                'description': 'Core BMAD functionality and orchestration',
                'color': '#6366f1',
                'icon': '⚡',
                'agents': AgentService.get_agents_from_module('core'),
                'workflows': WorkflowService.get_workflows_from_module('core'),
                'config': core_config,
            })
        
        # Other modules
        modules_path = Path(current_app.config['BMAD_MODULES_PATH'])
        if modules_path.exists():
            for module_dir in sorted(modules_path.iterdir()):
                if module_dir.is_dir():
                    module_code = module_dir.name
                    module_config = cls.get_module_config(module_code) or {}
                    
                    module_info = AgentService.MODULE_INFO.get(module_code, {
                        'name': module_code.upper(),
                        'description': f'{module_code} module',
                        'color': '#6b7280',
                        'icon': '📦'
                    })
                    
                    modules.append({
                        'code': module_code,
                        'name': module_config.get('name', module_info['name']),
                        'description': module_info['description'],
                        'color': module_info['color'],
                        'icon': module_info['icon'],
                        'agents': AgentService.get_agents_from_module(module_code),
                        'workflows': WorkflowService.get_workflows_from_module(module_code),
                        'config': module_config,
                    })
        
        return modules
    
    @classmethod
    def get_module_readme(cls, module_code: str) -> Optional[str]:
        """Get the README content for a module."""
        if module_code == 'core':
            module_path = Path(current_app.config['BMAD_CORE_PATH'])
        else:
            module_path = Path(current_app.config['BMAD_MODULES_PATH']) / module_code
        
        # Try different README filenames
        for readme_name in ['README.md', 'readme.md', 'Readme.md']:
            readme_file = module_path / readme_name
            if readme_file.exists():
                try:
                    with open(readme_file, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception:
                    pass
        
        return None
