"""
BMAD Web Dashboard - Workflow Service
Handles parsing and management of BMAD workflows.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from flask import current_app


class WorkflowService:
    """Service for managing BMAD workflows."""
    
    # Phase definitions
    PHASES = {
        1: {
            'name': 'Analysis',
            'description': 'Brainstorming, research, and product brief',
            'color': '#3b82f6',  # Blue
            'icon': '🔍',
            'optional': True
        },
        2: {
            'name': 'Planning',
            'description': 'PRD, tech-spec, and UX design',
            'color': '#10b981',  # Green
            'icon': '📋',
            'optional': False
        },
        3: {
            'name': 'Solutioning',
            'description': 'Architecture and implementation readiness',
            'color': '#f59e0b',  # Amber
            'icon': '🏗️',
            'optional': False  # Required for BMad Method and Enterprise tracks
        },
        4: {
            'name': 'Implementation',
            'description': 'Sprint planning, story development, and code review',
            'color': '#8b5cf6',  # Purple
            'icon': '💻',
            'optional': False
        }
    }
    
    @classmethod
    def get_all_workflows(cls) -> List[Dict]:
        """Get all workflows from all modules."""
        workflows = []
        
        # Get core workflows
        core_workflows = cls.get_workflows_from_module('core')
        workflows.extend(core_workflows)
        
        # Get module workflows
        modules_path = Path(current_app.config['BMAD_MODULES_PATH'])
        if modules_path.exists():
            for module_dir in modules_path.iterdir():
                if module_dir.is_dir():
                    module_workflows = cls.get_workflows_from_module(module_dir.name)
                    workflows.extend(module_workflows)
        
        return workflows
    
    @classmethod
    def get_workflows_from_module(cls, module_code: str) -> List[Dict]:
        """Get all workflows from a specific module."""
        workflows = []
        
        if module_code == 'core':
            workflows_path = Path(current_app.config['BMAD_CORE_PATH']) / 'workflows'
        else:
            workflows_path = Path(current_app.config['BMAD_MODULES_PATH']) / module_code / 'workflows'
        
        if not workflows_path.exists():
            return workflows
        
        # Find all workflow.md and workflow.yaml files
        for workflow_file in workflows_path.rglob('workflow.md'):
            workflow_data = cls.parse_workflow_file(workflow_file, module_code)
            if workflow_data:
                workflows.append(workflow_data)
        
        for workflow_file in workflows_path.rglob('workflow.yaml'):
            workflow_data = cls.parse_workflow_yaml(workflow_file, module_code)
            if workflow_data:
                workflows.append(workflow_data)
        
        return workflows
    
    @classmethod
    def parse_workflow_file(cls, file_path: Path, module_code: str) -> Optional[Dict]:
        """Parse a workflow markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract workflow name from directory
            workflow_name = file_path.parent.name
            
            # Try to extract title from markdown
            title = workflow_name.replace('-', ' ').title()
            lines = content.split('\n')
            for line in lines[:10]:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            
            # Determine phase from path
            phase = cls._determine_phase(file_path)
            
            # Count steps
            steps_dir = file_path.parent / 'steps'
            step_count = 0
            if steps_dir.exists():
                step_count = len(list(steps_dir.glob('step-*.md')))
            
            return {
                'id': workflow_name,
                'name': workflow_name,
                'title': title,
                'module': module_code,
                'phase': phase,
                'phase_info': cls.PHASES.get(phase, {}),
                'file_path': str(file_path),
                'type': 'markdown',
                'step_count': step_count,
                'has_template': (file_path.parent / 'template.md').exists(),
            }
        except Exception as e:
            current_app.logger.error(f"Error parsing workflow file {file_path}: {e}")
            return None
    
    @classmethod
    def parse_workflow_yaml(cls, file_path: Path, module_code: str) -> Optional[Dict]:
        """Parse a workflow YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
            
            workflow_name = file_path.parent.name
            
            # Determine phase from path
            phase = cls._determine_phase(file_path)
            
            return {
                'id': workflow_name,
                'name': workflow_name,
                'title': content.get('title', workflow_name.replace('-', ' ').title()),
                'module': module_code,
                'phase': phase,
                'phase_info': cls.PHASES.get(phase, {}),
                'file_path': str(file_path),
                'type': 'yaml',
                'step_count': len(content.get('steps', [])),
                'has_template': (file_path.parent / 'template.md').exists(),
            }
        except Exception as e:
            current_app.logger.error(f"Error parsing workflow YAML {file_path}: {e}")
            return None
    
    @classmethod
    def _determine_phase(cls, file_path: Path) -> int:
        """Determine workflow phase from file path."""
        path_str = str(file_path).lower()
        
        # Check for explicit phase markers in path
        if '1-analysis' in path_str or 'phase-1' in path_str or '/analysis/' in path_str:
            return 1
        elif '2-plan' in path_str or 'phase-2' in path_str or '/planning/' in path_str:
            return 2
        elif '3-solution' in path_str or 'phase-3' in path_str or '/solutioning/' in path_str:
            return 3
        elif '4-implement' in path_str or 'phase-4' in path_str or '/implementation/' in path_str:
            return 4
        elif 'testarch' in path_str or '/test' in path_str:
            return 4  # Testing is part of implementation
        
        # Default to phase 2 for planning workflows
        return 2
    
    @classmethod
    def get_phases(cls) -> Dict:
        """Get all phase definitions."""
        return cls.PHASES
    
    @classmethod
    def get_workflow_by_id(cls, module_code: str, workflow_id: str) -> Optional[Dict]:
        """Get a specific workflow by module and ID."""
        workflows = cls.get_workflows_from_module(module_code)
        for workflow in workflows:
            if workflow['id'] == workflow_id:
                return workflow
        return None
    
    @classmethod
    def get_workflow_stats(cls) -> Dict:
        """Get workflow statistics."""
        all_workflows = cls.get_all_workflows()
        
        # Count by phase
        by_phase = {1: 0, 2: 0, 3: 0, 4: 0}
        for wf in all_workflows:
            phase = wf.get('phase', 2)
            if phase in by_phase:
                by_phase[phase] += 1
        
        # Count by module
        by_module = {}
        for wf in all_workflows:
            module = wf.get('module', 'unknown')
            by_module[module] = by_module.get(module, 0) + 1
        
        return {
            'total': len(all_workflows),
            'by_phase': by_phase,
            'by_module': by_module,
        }
