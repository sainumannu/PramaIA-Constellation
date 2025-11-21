# PramaIA Copilot Instructions

## 🏗️ Architecture Overview

**PramaIA** is a modular AI document processing platform built on a plugin-based architecture (PDK - Plugin Development Kit). The system is organized as:

- **PramaIAServer** (FastAPI): Main backend API + React frontend
- **PramaIA-PDK** (Node.js): Plugin ecosystem & workflow engine (port 3001)
- **PramaIA-LogService** (FastAPI): Centralized logging microservice (port 8081)
- **PramaIA-VectorstoreService** (FastAPI): Vector storage with ChromaDB + SQLite (port 8090)
- **PramaIA-Reconciliation** (FastAPI): Data sync & integrity service (port 8091)
- **PramaIA-Agents** (FastAPI): Autonomous agents like document monitoring (port 8001)

All services communicate via REST APIs and must be started together for the system to function.

## 🔄 Key Data Flows

### Document Upload → Workflow Execution
1. **Upload**: Client → `POST /documents/upload-with-visibility/` → DocumentService saves file
2. **Trigger**: TriggerService detects `file_upload` event, queries database for matching triggers
3. **Workflow**: WorkflowEngine executes linked workflow with document data
4. **Output**: Results stored in database/vectorstore via output nodes

### Event-Driven Trigger System
- Event fires → TriggerService pattern-matches against configured triggers
- Triggers contain conditions (filters) and link to workflows
- Multiple triggers can activate for same event; workflows execute independently
- See `FLUSSO_SISTEMA_TRIGGER_MODERNO.md` for detailed flow

### Microservice Communication
- All services expose `/health` and `/status` endpoints
- Reconciliation service periodically syncs state across services
- VectorStore maintains SQLite metadata + ChromaDB embeddings consistency
- LogService collects logs from all services

## 💾 Database Models

**Key entities** (in `backend.models` + `backend.db`):
- **Workflow**: DAG structure with nodes/connections
- **Trigger**: Event type, conditions, linked workflow_id
- **Document**: File metadata, vectorstore references
- **User**: Auth/authorization with roles
- **Session**: Chat/conversation state
- **NodeType**: Database-based node registry with legacy mapping
- **NodeTypeMapping**: Legacy → modern node type mappings
- **PluginRegistry**: PDK plugin registration and status

Use `backend.crud.*` for CRUD operations; they handle database sessions and validation.

### Plugin System (PDK)

**Plugins** live in `PramaIA-PDK/plugins/`:
- Each plugin is a directory with `package.json` + `nodes.json`
- `nodes.json` defines node schemas (inputs/outputs, types, validation)
- Plugins expose REST endpoints via PDK Server
- Core plugins: `core-input-plugin`, `core-output-plugin`, `core-data-plugin`, `core-llm-plugin`, `core-rag-plugin`
- Custom plugins: `pdf-monitor-plugin`, `document-semantic-complete-plugin`, `workflow-scheduler-plugin`

**Node structure**: Each node has inputs (with type validation), outputs, and a resolver function. DatabaseNodeRegistry orchestrates node execution with automatic legacy mapping.

**DatabaseNodeRegistry**: Complete database-driven node management system:
- SQLite tables: `node_types`, `node_type_mappings`, `plugin_registry`, `node_execution_logs`
- Auto-discovery of PDK plugins with runtime registration
- Automatic legacy→modern node mapping (e.g., `PDFInput` → `document_input_node`)
- Runtime analytics and performance tracking
- Plugin health monitoring and lifecycle management

## 🏃 Development Workflows

### Starting the Full System
```powershell
# Windows PowerShell - from PramaIA root
.\start-all.ps1 -PDKLogLevel DEBUG

# Or start individual services:
# PramaIA-LogService → cd PramaIA-LogService; python main.py
# PDK Server → cd PramaIA-PDK/server; node plugin-api-server.js
# Backend → cd PramaIAServer; python -m uvicorn backend.main:app --reload --port 8000
# Frontend → cd PramaIAServer/frontend/client; npm start
```

### Testing Services
- `test_service.py` in root tests reconciliation API
- `test_triggers_endpoint.py` validates trigger system
- `debug_workflow_engine.py` tests workflow execution

### Debugging with Logs
- Backend outputs all logs to LogService at `POST /api/logs`
- Configure `PDK_LOG_LEVEL` (ERROR/INFO/DEBUG/TRACE) via env or script parameter
- Access logs via LogService UI or check local files in `logs/` directories

## 🎯 Code Patterns & Conventions

### FastAPI Services
- **Router structure**: `backend/routers/` for endpoint groups
- **Services layer**: `backend/services/` for business logic
- **CRUD operations**: Always use `backend.crud.*` classes, never raw SQLAlchemy
- **Error handling**: Use HTTPException with specific status codes
- **Logging**: Import `from backend.utils import get_logger` and use structured logging
- **Node Management**: Use `from backend.engine.db_node_registry import db_node_registry` for node operations

### Workflow/Trigger Processing
- Workflows are defined as JSON with node references and connections
- WorkflowEngine validates DAG before execution via DatabaseNodeRegistry
- Node inputs are type-checked; mismatches cause execution failures
- Triggers use event pattern matching (event_type + optional conditions)
- DatabaseNodeRegistry handles:
  - Automatic legacy→modern node mapping with transparent fallback
  - Runtime node type resolution from database
  - PDK plugin auto-discovery and registration
  - Execution analytics and performance logging

### Configuration Management
- Use `.env` files (checked into certain services)
- Environment variables override defaults
- Service URLs configured via `*_URL` env vars (BACKEND_URL, PDK_SERVER_BASE_URL, etc.)
- Database connections use SQLAlchemy ORM with context managers
- Node types and plugin registry stored in database with automatic discovery
- Legacy node compatibility via database mappings

## 🔍 Critical Cross-Component Integration Points

1. **Backend → PDK Server**: Backend calls `/api/nodes` to fetch available nodes and schemas
2. **Backend → LogService**: All services POST logs with API key authentication
3. **Backend → VectorStore**: Document embeddings stored/retrieved for RAG workflows
4. **Backend → Reconciliation**: Periodic sync of document state and integrity checks
5. **PDK Plugins → Workflow Execution**: WorkflowEngine instantiates nodes via DatabaseNodeRegistry
6. **DatabaseNodeRegistry → Node Mapping**: Automatic legacy→modern node type resolution
7. **Plugin Auto-Discovery**: Runtime plugin registration and node type updates

## ⚠️ Common Pitfalls

- **Service startup order matters**: LogService and PDK Server should start before Backend (dependencies on health checks)
- **Database migrations**: Backend uses SQLAlchemy models; check `backend/db/*.py` before running new migrations
- **Type mismatches in workflows**: Node input types must exactly match output types from previous nodes
- **CORS issues**: All services have CORS enabled for `*` origins—check headers if cross-origin requests fail
- **Unresolved plugin dependencies**: Ensure plugin directories exist before PDK Server starts; missing plugins cause route failures

## 📋 Script Management Policy

**BEFORE creating any new script:**

1. **Check existing scripts first** - Search in `scripts/` subdirectories:
   - `scripts/maintenance/` - System checks and verification
   - `scripts/debug/` - Debugging and troubleshooting  
   - `scripts/workflows/` - Workflow management
   - `scripts/utilities/` - General utilities
   - `scripts/testing/` - E2E tests and validation
   - `scripts/migration/` - Database migration

2. **Adapt existing scripts** if possible rather than creating duplicates

3. **Script lifecycle management**:
   - If script has **ongoing utility** → Move to appropriate `scripts/` subdirectory
   - If script is **temporary/one-time** → Delete after use
   - If script is **obsolete/duplicate** → Delete immediately

4. **Keep root directory clean** - NO `.py` scripts in root directory

5. **Naming conventions**:
   - `check_*.py` → `scripts/maintenance/`
   - `debug_*.py` → `scripts/debug/`  
   - `test_*.py` → `scripts/testing/`
   - Workflow management → `scripts/workflows/`
   - General utilities → `scripts/utilities/`

## 📝 File Creation Policy

**NO REPORT FILES**: Do NOT create analysis reports, documentation files, or summary files in the project directory. All analysis results and findings should be communicated directly in chat responses only. The user prefers receiving information through conversation rather than generated files.

## 📚 Key File Reference

| Path | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app initialization, route registration |
| `backend/engine/workflow_engine.py` | Workflow DAG execution orchestration |
| `backend/engine/db_node_registry.py` | DatabaseNodeRegistry implementation |
| `backend/db/node_registry_models.py` | Node registry database models |
| `PramaIA-PDK/server/plugin-api-server.js` | Plugin REST API server |
| `PramaIA-PDK/plugins/*/nodes.json` | Node schema definitions |
| `backend/services/trigger_service.py` | Event → trigger → workflow routing |
| `backend/models/` + `backend/db/` | SQLAlchemy ORM models |
| `backend/routers/` | FastAPI endpoint definitions |
| `.env` files per service | Configuration (check .gitignore for template) |

## 🚀 Extending the System

- **New workflow node**: Add to existing plugin's `nodes.json` and implement resolver
- **New microservice**: Follow FastAPI pattern (main.py, routers/, services/), register health endpoint
- **New trigger type**: Add event_type pattern matching in `TriggerService`, register in database
- **Database schema changes**: Use SQLAlchemy models in `backend/db/`; services handle migration via ORM

For complex additions, reference existing implementations (e.g., `document-semantic-complete-plugin` for plugin patterns, `PramaIA-LogService` for new service structure).

