"""
BMAD Web Dashboard - Project Service
File-based service for reading and managing BMAD project files.
"""
import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from flask import current_app


class BmadProjectService:
    """Service for managing BMAD project files."""
    
    # Common BMAD output folder names
    OUTPUT_FOLDERS = ['_bmad-output', 'docs', '_docs', 'bmad-output']
    
    # Document type mappings
    DOC_TYPES = {
        'prd': {'patterns': ['prd.md', 'PRD.md', 'product-requirements.md'], 'icon': '📋', 'phase': 1},
        'architecture': {'patterns': ['architecture.md', 'Architecture.md', 'arch.md'], 'icon': '🏗️', 'phase': 2},
        'tech-spec': {'patterns': ['tech-spec.md', 'technical-spec.md', 'spec.md'], 'icon': '⚙️', 'phase': 1},
        'ux-design': {'patterns': ['ux-design.md', 'ux.md', 'design.md'], 'icon': '🎨', 'phase': 1},
        'product-brief': {'patterns': ['product-brief.md', 'brief.md'], 'icon': '📝', 'phase': 0},
        'epics': {'patterns': ['epics.md', 'epic-breakdown.md', 'stories.md'], 'icon': '📦', 'phase': 2},
        'project-context': {'patterns': ['project-context.md'], 'icon': '📖', 'phase': 0},
    }
    
    @classmethod
    def scan_project(cls, project_path: str) -> Dict:
        """Scan a project directory and return its BMAD structure."""
        path = Path(project_path)
        
        if not path.exists():
            return {'error': f'Project path does not exist: {project_path}'}
        
        result = {
            'path': str(path.absolute()),
            'name': path.name,
            'has_bmad': False,
            'bmad_folder': None,
            'output_folder': None,
            'workflow_status': None,
            'sprint_status': None,
            'documents': [],
            'epics': [],
            'stories': [],
            'current_phase': 0,
            'track': None,
        }
        
        # Check for _bmad installation folder
        bmad_folder = path / '_bmad'
        if bmad_folder.exists():
            result['has_bmad'] = True
            result['bmad_folder'] = str(bmad_folder)
        
        # Find output folder
        for folder_name in cls.OUTPUT_FOLDERS:
            output_folder = path / folder_name
            if output_folder.exists():
                result['output_folder'] = str(output_folder)
                break
        
        # If no output folder, use project root for docs
        if not result['output_folder']:
            result['output_folder'] = str(path)
        
        output_path = Path(result['output_folder'])
        
        # Find workflow status file
        workflow_status = cls._find_workflow_status(path)
        if workflow_status:
            result['workflow_status'] = workflow_status
            result['track'] = workflow_status.get('selected_track')
            result['current_phase'] = cls._determine_current_phase(workflow_status)
        
        # Find sprint status file
        sprint_status = cls._find_sprint_status(path)
        if sprint_status:
            result['sprint_status'] = sprint_status
        
        # Scan for documents
        result['documents'] = cls._scan_documents(output_path)
        
        # Parse epics from epics file or individual files
        result['epics'] = cls._parse_epics(output_path, sprint_status)
        
        return result
    
    @classmethod
    def _find_workflow_status(cls, project_path: Path) -> Optional[Dict]:
        """Find and parse the workflow status YAML file."""
        # Common locations for workflow status
        search_paths = [
            project_path / '_bmad-output' / 'bmm-workflow-status.yaml',
            project_path / 'docs' / 'bmm-workflow-status.yaml',
            project_path / 'bmm-workflow-status.yaml',
            project_path / '_bmad-output' / 'workflow-status.yaml',
        ]
        
        for status_path in search_paths:
            if status_path.exists():
                try:
                    with open(status_path, 'r', encoding='utf-8') as f:
                        content = yaml.safe_load(f)
                    if content:
                        content['_file_path'] = str(status_path)
                        return content
                except Exception as e:
                    current_app.logger.error(f"Error reading workflow status: {e}")
        
        return None
    
    @classmethod
    def _find_sprint_status(cls, project_path: Path) -> Optional[Dict]:
        """Find and parse the sprint status YAML file."""
        search_paths = [
            project_path / '_bmad-output' / 'sprint-status.yaml',
            project_path / 'docs' / 'sprint-status.yaml',
            project_path / 'sprint-status.yaml',
        ]
        
        for status_path in search_paths:
            if status_path.exists():
                try:
                    with open(status_path, 'r', encoding='utf-8') as f:
                        content = yaml.safe_load(f)
                    if content:
                        content['_file_path'] = str(status_path)
                        return content
                except Exception as e:
                    current_app.logger.error(f"Error reading sprint status: {e}")
        
        return None
    
    @classmethod
    def _determine_current_phase(cls, workflow_status: Dict) -> int:
        """Determine current phase from workflow status."""
        status = workflow_status.get('workflow_status', {})
        
        if isinstance(status, str):
            return 0
        
        # Check what's completed
        completed_workflows = []
        for wf_id, wf_status in status.items() if isinstance(status, dict) else []:
            if wf_status not in ['required', 'optional', 'recommended', 'conditional']:
                completed_workflows.append(wf_id)
        
        # Determine phase based on completed workflows
        if 'sprint-planning' in completed_workflows:
            return 3  # Implementation
        elif 'create-epics-and-stories' in completed_workflows or 'create-architecture' in completed_workflows:
            return 2  # Solutioning
        elif 'prd' in completed_workflows:
            return 1  # Planning
        
        return 0  # Discovery
    
    @classmethod
    def _scan_documents(cls, output_path: Path) -> List[Dict]:
        """Scan for BMAD documents in the output folder."""
        documents = []
        
        for doc_type, info in cls.DOC_TYPES.items():
            for pattern in info['patterns']:
                # Search in output folder and subdirectories
                for doc_path in output_path.rglob(pattern):
                    doc_data = cls._parse_document(doc_path, doc_type, info)
                    if doc_data:
                        documents.append(doc_data)
                        break  # Only take first match per type
        
        # Sort by phase
        documents.sort(key=lambda x: x.get('phase', 99))
        
        return documents
    
    @classmethod
    def _parse_document(cls, doc_path: Path, doc_type: str, info: Dict) -> Optional[Dict]:
        """Parse a BMAD document file."""
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract frontmatter if present
            frontmatter = {}
            body = content
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                    except:
                        pass
                    body = parts[2].strip()
            
            # Extract title from first heading
            title = doc_type.replace('-', ' ').title()
            for line in body.split('\n'):
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            
            # Get file stats
            stat = doc_path.stat()
            
            return {
                'type': doc_type,
                'title': title,
                'icon': info['icon'],
                'phase': info['phase'],
                'path': str(doc_path),
                'filename': doc_path.name,
                'content': content,
                'body': body,
                'frontmatter': frontmatter,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'word_count': len(body.split()),
            }
        except Exception as e:
            current_app.logger.error(f"Error parsing document {doc_path}: {e}")
            return None
    
    @classmethod
    def _parse_epics(cls, output_path: Path, sprint_status: Optional[Dict]) -> List[Dict]:
        """Parse epics from files or sprint status."""
        epics = []
        
        # Try to find epics.md file
        epics_file = None
        for pattern in ['epics.md', 'epic-breakdown.md', 'stories.md']:
            matches = list(output_path.rglob(pattern))
            if matches:
                epics_file = matches[0]
                break
        
        if epics_file:
            epics = cls._parse_epics_from_file(epics_file)
        
        # Enhance with sprint status if available
        if sprint_status:
            dev_status = sprint_status.get('development_status', {})
            for epic in epics:
                epic_key = f"epic-{epic['number']}"
                if epic_key in dev_status:
                    epic['status'] = dev_status[epic_key]
                
                for story in epic.get('stories', []):
                    story_key = story.get('key', '').lower().replace('.', '-')
                    # Try various key formats
                    for key_format in [story_key, f"{epic['number']}-{story['number']}-{story.get('slug', '')}"]:
                        if key_format in dev_status:
                            story['status'] = dev_status[key_format]
                            break
        
        return epics
    
    @classmethod
    def _parse_epics_from_file(cls, epics_file: Path) -> List[Dict]:
        """Parse epics from an epics.md file."""
        epics = []
        
        try:
            with open(epics_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse epic sections
            epic_pattern = r'##\s*Epic\s*(\d+):\s*(.+?)(?=##\s*Epic\s*\d+:|$)'
            epic_matches = re.findall(epic_pattern, content, re.DOTALL | re.IGNORECASE)
            
            for epic_num, epic_content in epic_matches:
                epic_title = epic_content.split('\n')[0].strip()
                
                epic = {
                    'number': int(epic_num),
                    'key': f'E{epic_num}',
                    'title': epic_title,
                    'content': epic_content.strip(),
                    'status': 'backlog',
                    'stories': [],
                }
                
                # Parse stories within this epic
                story_pattern = r'###\s*Story\s*(\d+)\.(\d+):\s*(.+?)(?=###\s*Story|##\s*Epic|$)'
                story_matches = re.findall(story_pattern, epic_content, re.DOTALL | re.IGNORECASE)
                
                for epic_n, story_n, story_content in story_matches:
                    story_title = story_content.split('\n')[0].strip()
                    
                    # Extract user story
                    user_story_match = re.search(r'As a (.+?),\s*I want (.+?),\s*[Ss]o that (.+?)\.', 
                                                  story_content, re.DOTALL)
                    
                    story = {
                        'number': int(story_n),
                        'key': f'S{epic_n}.{story_n}',
                        'title': story_title,
                        'content': story_content.strip(),
                        'status': 'backlog',
                        'user_story': {
                            'role': user_story_match.group(1).strip() if user_story_match else '',
                            'action': user_story_match.group(2).strip() if user_story_match else '',
                            'benefit': user_story_match.group(3).strip() if user_story_match else '',
                        } if user_story_match else None,
                    }
                    
                    # Extract acceptance criteria
                    ac_match = re.search(r'\*\*Acceptance Criteria[:\*]*\**(.*?)(?=\*\*[A-Z]|\Z)', 
                                         story_content, re.DOTALL | re.IGNORECASE)
                    if ac_match:
                        story['acceptance_criteria'] = ac_match.group(1).strip()
                    
                    epic['stories'].append(story)
                
                epics.append(epic)
        
        except Exception as e:
            current_app.logger.error(f"Error parsing epics file: {e}")
        
        return epics
    
    @classmethod
    def get_document(cls, project_path: str, doc_type: str) -> Optional[Dict]:
        """Get a specific document from a project."""
        project = cls.scan_project(project_path)
        
        for doc in project.get('documents', []):
            if doc['type'] == doc_type:
                return doc
        
        return None
    
    @classmethod
    def save_document(cls, doc_path: str, content: str) -> Dict:
        """Save content to a document file."""
        try:
            path = Path(doc_path)
            
            # Create backup
            if path.exists():
                backup_path = path.with_suffix(f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak')
                path.rename(backup_path)
                backup_path.rename(path)  # Rename back for now, backup exists
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {'success': True, 'path': str(path)}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def update_sprint_status(cls, project_path: str, updates: Dict) -> Dict:
        """Update sprint status file."""
        project = cls.scan_project(project_path)
        sprint_status = project.get('sprint_status')
        
        if not sprint_status:
            return {'success': False, 'error': 'Sprint status file not found'}
        
        file_path = sprint_status.get('_file_path')
        
        try:
            # Update the development_status
            dev_status = sprint_status.get('development_status', {})
            dev_status.update(updates)
            sprint_status['development_status'] = dev_status
            
            # Remove internal fields before saving
            save_data = {k: v for k, v in sprint_status.items() if not k.startswith('_')}
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(save_data, f, default_flow_style=False, sort_keys=False)
            
            return {'success': True, 'path': file_path}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def create_story_file(cls, project_path: str, epic_num: int, story_num: int, 
                          story_data: Dict) -> Dict:
        """Create a new story file from template."""
        path = Path(project_path)
        
        # Find stories folder or create in output folder
        output_folder = None
        for folder_name in cls.OUTPUT_FOLDERS:
            if (path / folder_name).exists():
                output_folder = path / folder_name
                break
        
        if not output_folder:
            output_folder = path / '_bmad-output'
            output_folder.mkdir(exist_ok=True)
        
        stories_folder = output_folder / 'stories'
        stories_folder.mkdir(exist_ok=True)
        
        # Generate filename
        title_slug = re.sub(r'[^a-z0-9]+', '-', story_data.get('title', 'story').lower()).strip('-')
        filename = f"{epic_num}-{story_num}-{title_slug}.md"
        story_path = stories_folder / filename
        
        # Generate story content
        content = f"""# Story {epic_num}.{story_num}: {story_data.get('title', 'New Story')}

Status: ready-for-dev

## Story

As a {story_data.get('role', '[user role]')},
I want {story_data.get('action', '[action]')},
so that {story_data.get('benefit', '[benefit]')}.

## Acceptance Criteria

{story_data.get('acceptance_criteria', '1. [Add acceptance criteria]')}

## Tasks / Subtasks

- [ ] Task 1
  - [ ] Subtask 1.1
- [ ] Task 2
  - [ ] Subtask 2.1

## Dev Notes

{story_data.get('technical_notes', '- Technical implementation notes here')}

## Dev Agent Record

### Agent Model Used

### Completion Notes List

### File List
"""
        
        try:
            with open(story_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {'success': True, 'path': str(story_path), 'filename': filename}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @classmethod  
    def get_story_files(cls, project_path: str) -> List[Dict]:
        """Get all story files from a project."""
        path = Path(project_path)
        stories = []
        
        # Search for story files
        for output_folder in cls.OUTPUT_FOLDERS:
            stories_path = path / output_folder / 'stories'
            if stories_path.exists():
                for story_file in stories_path.glob('*.md'):
                    story_data = cls._parse_story_file(story_file)
                    if story_data:
                        stories.append(story_data)
        
        return stories
    
    @classmethod
    def _parse_story_file(cls, story_path: Path) -> Optional[Dict]:
        """Parse a story markdown file."""
        try:
            with open(story_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title
            title_match = re.search(r'^#\s*Story\s*[\d.]+:\s*(.+)$', content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else story_path.stem
            
            # Extract status
            status_match = re.search(r'^Status:\s*(.+)$', content, re.MULTILINE)
            status = status_match.group(1).strip() if status_match else 'backlog'
            
            # Extract story key from filename
            key_match = re.match(r'(\d+)-(\d+)', story_path.stem)
            
            return {
                'path': str(story_path),
                'filename': story_path.name,
                'title': title,
                'status': status,
                'epic_num': int(key_match.group(1)) if key_match else None,
                'story_num': int(key_match.group(2)) if key_match else None,
                'key': f"S{key_match.group(1)}.{key_match.group(2)}" if key_match else story_path.stem,
                'content': content,
                'modified': datetime.fromtimestamp(story_path.stat().st_mtime).isoformat(),
            }
        
        except Exception as e:
            current_app.logger.error(f"Error parsing story file {story_path}: {e}")
            return None
    
    @classmethod
    def initialize_project(cls, project_path: str, project_name: str, track: str = 'bmad-method',
                           project_type: str = 'greenfield') -> Dict:
        """Initialize a new BMAD project structure."""
        path = Path(project_path)
        
        if not path.exists():
            return {'success': False, 'error': 'Project path does not exist'}
        
        try:
            # Create output folder
            output_folder = path / '_bmad-output'
            output_folder.mkdir(exist_ok=True)
            
            # Create workflow status file
            workflow_status = {
                'generated': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'project': project_name,
                'project_type': project_type,
                'selected_track': track,
                'field_type': project_type,
                'workflow_path': f'paths/{track}-{project_type}.yaml',
                'workflow_status': {
                    'brainstorm-project': 'optional',
                    'research': 'optional', 
                    'product-brief': 'optional' if track == 'quick-flow' else 'recommended',
                    'prd': 'required' if track != 'quick-flow' else 'optional',
                    'tech-spec': 'required' if track == 'quick-flow' else 'optional',
                    'create-ux-design': 'conditional',
                    'create-architecture': 'required' if track != 'quick-flow' else 'optional',
                    'create-epics-and-stories': 'required' if track != 'quick-flow' else 'optional',
                    'implementation-readiness': 'required' if track != 'quick-flow' else 'optional',
                    'sprint-planning': 'required',
                }
            }
            
            status_path = output_folder / 'bmm-workflow-status.yaml'
            with open(status_path, 'w', encoding='utf-8') as f:
                yaml.dump(workflow_status, f, default_flow_style=False, sort_keys=False)
            
            # Create subfolders
            (output_folder / 'stories').mkdir(exist_ok=True)
            
            return {
                'success': True, 
                'path': str(output_folder),
                'workflow_status_path': str(status_path),
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
