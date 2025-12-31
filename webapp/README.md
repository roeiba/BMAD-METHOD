# 🚀 BMAD Web Dashboard

A professional Flask-based web dashboard for the BMAD Method (Breakthrough Method of Agile AI-driven Development). **Full support for the complete BMAD workflow** - from project initialization through PRD creation, epic/story breakdown, and sprint management.

![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-green?style=flat-square&logo=flask)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-06B6D4?style=flat-square&logo=tailwindcss)

## ✨ Features

### 📊 Dashboard & Exploration
- **Dashboard** - Beautiful overview of your BMAD installation with stats and quick actions
- **Agents Browser** - Explore all 25+ AI agents across 5 modules with full persona details
- **Workflows Viewer** - Browse 70+ workflows organized by development phases
- **Modules Explorer** - Deep dive into BMM, BMB, CIS, BMGD, and Core modules
- **Analytics** - Visual insights with charts showing agent and workflow distribution

### 🎯 Full BMAD Workflow Support
- **Project Workspace** - Comprehensive interface for managing BMAD projects
- **Workflow Status Tracking** - Visual checklist of all workflow phases from `bmm-workflow-status.yaml`
- **Document Management** - View and edit PRD, Architecture, Tech-Spec, and other BMAD documents
- **Epic & Story Browser** - Parse and display epics/stories from your `epics.md` file
- **Sprint Board** - Kanban-style board for tracking story status from `sprint-status.yaml`
- **File-Based Sync** - All data reads/writes directly to BMAD project files (no separate database for project data)

### 🔌 REST API
- Full API for integration with other tools
- Scan projects, read/write documents, manage workflow status
- Update sprint status and story states

## 🏗️ Architecture

```
webapp/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration settings
│   ├── extensions.py        # Flask extensions
│   ├── api/                  # REST API endpoints
│   ├── models/               # Database models
│   ├── routes/               # Page routes
│   ├── services/             # Business logic (agent/workflow parsing)
│   ├── templates/            # Jinja2 templates with TailwindCSS
│   └── static/               # Static assets
├── requirements.txt          # Python dependencies
├── run.py                    # Application entry point
└── .env                      # Environment configuration
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd webapp
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env if needed
```

### 3. Run the Dashboard

```bash
python3 run.py
```

### 4. Open in Browser

Navigate to [http://localhost:5000](http://localhost:5000)

## 📸 Screenshots

### Dashboard
- Welcome banner with version info
- Stats cards (agents, workflows, modules, projects)
- Phase progress visualization
- Featured agents and modules
- Quick start guide

### Agents Browser
- Grid view with filtering by module
- Search functionality
- Agent cards with persona preview
- Detailed agent view with commands

### Workflows
- Phase-based organization
- Visual flow diagram
- Workflow cards with step counts

### Analytics
- Doughnut chart for workflows by phase
- Bar chart for agents by module
- Detailed statistics tables

## 🔌 API Endpoints

### Agents
- `GET /api/agents` - List all agents
- `GET /api/agents?module=bmm` - Filter by module
- `GET /api/agents/{module}/{id}` - Get agent details

### Workflows
- `GET /api/workflows` - List all workflows
- `GET /api/workflows?phase=2` - Filter by phase
- `GET /api/workflows/stats` - Get statistics
- `GET /api/workflows/phases` - Get phase definitions

### Modules
- `GET /api/modules` - List all modules
- `GET /api/modules/{code}` - Get module details

### Projects
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/{id}` - Get project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Stats
- `GET /api/stats` - Dashboard statistics

## 🛠️ Tech Stack

### Backend
- **Flask 3.1** - Modern Python web framework
- **SQLAlchemy 2.0** - Database ORM
- **PyYAML** - YAML parsing for agents/workflows
- **Flask-CORS** - Cross-origin resource sharing

### Frontend
- **TailwindCSS** - Utility-first CSS framework (via CDN)
- **Alpine.js** - Lightweight JavaScript framework
- **Chart.js** - Beautiful charts for analytics

### Database
- **SQLite** - Development database (easily swappable to PostgreSQL)

## 📁 Project Structure

The dashboard reads directly from the BMAD source files:

- **Agents**: `src/core/agents/` and `src/modules/{module}/agents/`
- **Workflows**: `src/core/workflows/` and `src/modules/{module}/workflows/`
- **Module configs**: `src/modules/{module}/module.yaml`

## 🎨 UI Design

The UI follows modern design principles:

- **Clean & Professional** - White backgrounds with subtle shadows
- **Color-coded Modules** - Each module has a distinct color identity
- **Responsive** - Works on desktop, tablet, and mobile
- **Dark Sidebar** - Elegant navigation with collapsible design
- **Card-based Layout** - Organized information display
- **Hover Effects** - Smooth transitions and feedback

## 📝 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (development/production) | development |
| `FLASK_DEBUG` | Enable debug mode | 1 |
| `SECRET_KEY` | Flask secret key | (auto-generated) |
| `DATABASE_URL` | Database connection string | sqlite:///bmad.db |
| `BMAD_SOURCE_PATH` | Path to BMAD source | ../src |

## 🚧 Future Enhancements

- [ ] Real-time workflow execution tracking
- [ ] Sprint board with drag-and-drop
- [ ] Integration with IDE plugins
- [ ] User authentication
- [ ] Project templates
- [ ] Activity timeline
- [ ] Export/Import functionality

## 🤝 Contributing

This dashboard is part of the BMAD Method project. Contributions welcome!

## 📄 License

MIT License - See the main BMAD-METHOD repository for details.

---

Built with ❤️ for the BMAD community
