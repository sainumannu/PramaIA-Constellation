print('[IMPORT] backend/routers/workflow_router.py loaded')
import httpx
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
import logging

from backend.db.database import get_db
from backend.auth.dependencies import get_current_user
from backend.db.models import User
from backend.crud.workflow_crud import WorkflowCRUD
from backend.schemas.workflow_schemas import WorkflowCreate, WorkflowUpdate
from backend.schemas.user_schemas import UserInToken

# Importa il logger migrato
from backend.utils.logger_migration import get_logger

# Ottieni logger per questo modulo
logger = get_logger()

router = APIRouter(
    prefix="/api/workflows",
    tags=["workflows"],
    responses={404: {"description": "Not found"}},
)

# Endpoint per ottenere tutti i workflow
@router.get("/")
async def get_workflows(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Ottiene la lista di tutti i workflow dal database
    """
    logger.info(
        f"Getting workflows for user: {current_user.username}",
        details={"user_id": str(current_user.username)}
    )
    
    try:
        # Usa il CRUD per ottenere i workflow dal database
        workflows = WorkflowCRUD.get_workflows(db, user_id=str(current_user.username))
        
        # Trasforma i workflow per la risposta API
        workflows_list = []
        for workflow in workflows:
            workflow_summary = {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description or "",
                "is_active": workflow.is_active,
                "is_public": workflow.is_public,
                "created_at": workflow.created_at.isoformat() if workflow.created_at is not None else "",
                "updated_at": workflow.updated_at.isoformat() if workflow.updated_at is not None else "",
                "created_by": workflow.created_by,
                "nodes_count": len(workflow.nodes) if workflow.nodes else 0,
                "tags": workflow.tags or [],
                "category": workflow.category or "General",
                "color": workflow.color or "#3B82F6"
            }
            workflows_list.append(workflow_summary)
        
        logger.info(f"Returning {len(workflows_list)} workflows from database")
        return workflows_list
        
    except Exception as e:
        logger.error(f"Error getting workflows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving workflows from database"
        )

# Endpoint per creare un nuovo workflow
@router.post("/")
async def create_workflow(
    workflow_data: dict, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crea un nuovo workflow nel database
    """
    logger.info(f"Creating new workflow for user: {current_user.username}")
    
    try:
        # Prepara i dati per il CRUD
        workflow_name = workflow_data.get("name", "Nuovo Workflow")
        
        # Verifica se esiste gi├á un workflow con lo stesso nome
        from backend.db.workflow_models import Workflow
        
        # Log dei nomi esistenti per debug
        existing_names = db.query(Workflow.name).filter(
            Workflow.created_by == current_user.username
        ).all()
        logger.info(f"Existing workflow names for user {current_user.username}: {[name[0] for name in existing_names]}")
        
        existing_workflow = db.query(Workflow).filter(
            Workflow.name == workflow_name,
            Workflow.created_by == current_user.username
        ).first()
        
        if existing_workflow:
            logger.warning(f"Workflow with name '{workflow_name}' already exists - returning existing workflow (idempotent behavior)")
            # Restituisci il workflow esistente invece di un errore
            # Questo rende l'operazione idempotente
            response_workflow = {
                "workflow_id": existing_workflow.workflow_id,
                "name": existing_workflow.name,
                "description": existing_workflow.description,
                "is_active": existing_workflow.is_active,
                "is_public": existing_workflow.is_public,
                "created_at": existing_workflow.created_at.isoformat(),
                "updated_at": existing_workflow.updated_at.isoformat(),
                "created_by": existing_workflow.created_by,
                "assigned_groups": existing_workflow.assigned_groups,
                "tags": existing_workflow.tags,
                "category": existing_workflow.category,
                "color": existing_workflow.color,
                "view_state": existing_workflow.view_state or {},
                "nodes": [
                    {
                        "node_id": node.node_id,
                        "node_type": node.node_type,
                        "name": node.name,
                        "description": node.description,
                        "config": node.config or {},
                        "position": node.position or {},
                        "width": node.width,
                        "height": node.height,
                        "resizable": node.resizable,
                        "icon": getattr(node, 'icon', ''),
                        "color": getattr(node, 'color', '#ffffff')
                    } for node in existing_workflow.nodes
                ],
                "connections": [
                    {
                        "source_node": conn.from_node_id,
                        "target_node": conn.to_node_id,
                        "source_output": conn.from_port,
                        "target_input": conn.to_port,
                        "from_node_id": conn.from_node_id,
                        "to_node_id": conn.to_node_id,
                        "from_port": conn.from_port,
                        "to_port": conn.to_port
                    } for conn in existing_workflow.connections
                ]
            }
            logger.info(f"Returning existing workflow with {len(response_workflow['nodes'])} nodes")
            return response_workflow
        
        workflow_create_data = {
            "name": workflow_name,
            "description": workflow_data.get("description", ""),
            "is_active": workflow_data.get("is_active", True),
            "is_public": workflow_data.get("is_public", False),
            "assigned_groups": workflow_data.get("assigned_groups", []),
            "tags": workflow_data.get("tags", []),
            "category": workflow_data.get("category", "General"),
            "color": workflow_data.get("color", "#3B82F6"),
            "view_state": workflow_data.get("view_state", {}),
            "nodes": workflow_data.get("nodes", []),
            "connections": workflow_data.get("connections", [])
        }
        
        # Crea il workflow tramite CRUD (che gestisce automaticamente nodi e connessioni)
        # Per ora creiamo manualmente il workflow base
        from backend.db.workflow_models import Workflow
        from datetime import datetime
        import uuid
        
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        current_time = datetime.utcnow()
        
        new_workflow = Workflow(
            workflow_id=workflow_id,
            name=workflow_create_data["name"],
            description=workflow_create_data["description"],
            created_by=current_user.username,
            created_at=current_time,
            updated_at=current_time,
            is_active=workflow_create_data["is_active"],
            is_public=workflow_create_data["is_public"],
            assigned_groups=workflow_create_data["assigned_groups"],
            tags=workflow_create_data["tags"],
            category=workflow_create_data["category"],
            color=workflow_create_data["color"],
            view_state=workflow_create_data.get("view_state", {})
        )
        
        db.add(new_workflow)
        db.flush()  # Flush solo per ottenere l'ID, senza commit
        
        # Aggiungi nodi e connessioni (se presenti)
        if workflow_create_data["nodes"]:
            logger.info(f"Adding {len(workflow_create_data['nodes'])} nodes to new workflow {workflow_id}")
            from backend.db.workflow_models import WorkflowNode
            
            for node_data in workflow_create_data["nodes"]:
                # DEBUG: Log dei dati del nodo per vedere se icon/color arrivano dal frontend
                print(f"­ƒÜ¿ [BACKEND] Node data received: {node_data}")
                print(f"­ƒÜ¿ [BACKEND] Node icon: '{node_data.get('icon', 'NOT_FOUND')}'")
                print(f"­ƒÜ¿ [BACKEND] Node color: '{node_data.get('color', 'NOT_FOUND')}'")
                print(f"­ƒÜ¿ [BACKEND] Node data keys: {list(node_data.keys())}")
                
                new_node = WorkflowNode(
                    node_id=node_data.get("node_id", f"node_{uuid.uuid4().hex[:8]}"),
                    workflow_id=workflow_id,
                    node_type=node_data.get("node_type", "default"),
                    name=node_data.get("name", "Nodo"),
                    description=node_data.get("description", ""),
                    config=node_data.get("config", {}),
                    position=node_data.get("position", {"x": 0, "y": 0}),
                    icon=node_data.get("icon", ""),
                    color=node_data.get("color", "#ffffff")
                )
                db.add(new_node)
                
        if workflow_create_data["connections"]:
            logger.info(f"Adding {len(workflow_create_data['connections'])} connections to new workflow {workflow_id}")
            from backend.db.workflow_models import WorkflowConnection
            
            for conn_data in workflow_create_data["connections"]:
                # Determina i nomi dei campi corretti (supporta sia source_node che from_node_id)
                from_node = conn_data.get("from_node_id") or conn_data.get("source_node", "")
                to_node = conn_data.get("to_node_id") or conn_data.get("target_node", "")
                from_port = conn_data.get("from_port") or conn_data.get("source_output", "output")
                to_port = conn_data.get("to_port") or conn_data.get("target_input", "input")
                
                if not from_node or not to_node:
                    logger.warning(f"Skipping invalid connection, missing node IDs: {conn_data}")
                    continue
                
                new_conn = WorkflowConnection(
                    workflow_id=workflow_id,
                    from_node_id=from_node,
                    to_node_id=to_node,
                    from_port=from_port,
                    to_port=to_port
                )
                db.add(new_conn)
        
        # Singolo commit alla fine per garantire atomicità
        db.commit()
        db.refresh(new_workflow)
        
        # Trasforma per la risposta
        response_workflow = {
            "workflow_id": new_workflow.workflow_id,
            "name": new_workflow.name,
            "description": new_workflow.description,
            "is_active": new_workflow.is_active,
            "is_public": new_workflow.is_public,
            "created_at": new_workflow.created_at.isoformat(),
            "updated_at": new_workflow.updated_at.isoformat(),
            "created_by": new_workflow.created_by,
            "assigned_groups": new_workflow.assigned_groups,
            "tags": new_workflow.tags,
            "category": new_workflow.category,
            "color": new_workflow.color,
            "view_state": new_workflow.view_state or {},
            "nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "name": node.name,
                    "description": node.description,
                    "config": node.config or {},
                    "position": node.position or {},
                    "width": node.width,
                    "height": node.height,
                    "resizable": node.resizable,
                    "icon": getattr(node, 'icon', ''),
                    "color": getattr(node, 'color', '#ffffff')
                } for node in new_workflow.nodes
            ],
            "connections": [
                {
                    "source_node": conn.from_node_id,
                    "target_node": conn.to_node_id,
                    "source_output": conn.from_port,
                    "target_input": conn.to_port,
                    # Aggiungiamo anche i campi originali per compatibilit├á
                    "from_node_id": conn.from_node_id,
                    "to_node_id": conn.to_node_id,
                    "from_port": conn.from_port,
                    "to_port": conn.to_port
                } for conn in new_workflow.connections
            ]
        }
        
        logger.info(f"Workflow created with ID: {workflow_id}")
        logger.info(f"Returning {len(response_workflow['nodes'])} nodes and {len(response_workflow['connections'])} connections")
        return response_workflow
        
    except HTTPException:
        # Rilancia l'errore HTTP se ├¿ gi├á stato generato
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating workflow in database"
        )

# Endpoint per ottenere gli utenti assegnabili ai workflow
@router.get("/users")
async def get_workflow_users(current_user: User = Depends(get_current_user)):
    """
    Ottiene la lista degli utenti che possono essere assegnati ai workflow
    """
    logger.info(f"Getting workflow users for: {current_user.username}")
    return {
        "users": [
            {
                "username": current_user.username,
                "name": current_user.name or current_user.username,
                "role": current_user.role
            }
        ]
    }

# Endpoint per ottenere un singolo workflow
@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ottiene un workflow specifico per ID dal database
    """
    logger.info(f"Getting workflow with ID: {workflow_id} for user: {current_user.username}")
    
    try:
        # Usa il CRUD per ottenere il workflow dal database
        workflow = WorkflowCRUD.get_workflow(db, workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow with ID '{workflow_id}' not found"
            )
        
        # Verifica i permessi (admin o proprietario pu├▓ accedere)
        if str(workflow.created_by) != str(current_user.username) and str(current_user.role) != "admin":
            if not bool(workflow.is_public):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this workflow"
                )
        
        # Trasforma per la risposta API
        workflow_data = {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description or "",
            "is_active": workflow.is_active,
            "is_public": workflow.is_public,
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat(),
            "created_by": workflow.created_by,
            "assigned_groups": workflow.assigned_groups or [],
            "tags": workflow.tags or [],
            "category": workflow.category or "General",
            "color": workflow.color or "#3B82F6",
            "view_state": workflow.view_state or {},
            "nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type,
                    "name": node.name,
                    "description": node.description,
                    "config": node.config or {},
                    "position": node.position or {},
                    "width": node.width,
                    "height": node.height,
                    "resizable": node.resizable,
                    "icon": getattr(node, 'icon', ''),
                    "color": getattr(node, 'color', '#ffffff')
                } for node in workflow.nodes
            ],
            "connections": [
                {
                    "source_node": conn.from_node_id,
                    "target_node": conn.to_node_id,
                    "source_output": conn.from_port,
                    "target_input": conn.to_port,
                    # Aggiungiamo anche i campi originali per compatibilit├á
                    "from_node_id": conn.from_node_id,
                    "to_node_id": conn.to_node_id,
                    "from_port": conn.from_port,
                    "to_port": conn.to_port
                } for conn in workflow.connections
            ]
        }
        
        logger.info(f"Found workflow: {workflow.name}")
        logger.info(f"Returning {len(workflow_data['nodes'])} nodes and {len(workflow_data['connections'])} connections")
        return workflow_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving workflow from database"
        )

# Endpoint per aggiornare un workflow esistente
@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str, 
    workflow_data: dict, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aggiorna un workflow esistente nel database
    """
    logger.info(f"Updating workflow with ID: {workflow_id} for user: {current_user.username}")
    
    try:
        # Verifica che il workflow esista
        existing_workflow = WorkflowCRUD.get_workflow(db, workflow_id)
        
        if not existing_workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow with ID '{workflow_id}' not found"
            )
        
        # Verifica i permessi (admin o proprietario pu├▓ modificare)
        if str(existing_workflow.created_by) != str(current_user.username) and str(current_user.role) != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to modify this workflow"
            )
        
        # Aggiorna i campi del workflow
        from datetime import datetime
        
        if "name" in workflow_data:
            existing_workflow.name = workflow_data["name"]
        if "description" in workflow_data:
            existing_workflow.description = workflow_data["description"]
        if "is_active" in workflow_data:
            existing_workflow.is_active = workflow_data["is_active"]
        if "is_public" in workflow_data:
            existing_workflow.is_public = workflow_data["is_public"]
        if "assigned_groups" in workflow_data:
            existing_workflow.assigned_groups = workflow_data["assigned_groups"]
        if "tags" in workflow_data:
            existing_workflow.tags = workflow_data["tags"]
        if "category" in workflow_data:
            existing_workflow.category = workflow_data["category"]
        if "color" in workflow_data:
            existing_workflow.color = workflow_data["color"]
        if "view_state" in workflow_data:
            existing_workflow.view_state = workflow_data["view_state"]
            logger.info(f"Updating view_state: {workflow_data['view_state']}")

        # Gestione nodi e connessioni
        if "nodes" in workflow_data:
            try:
                # Log dettagliato dei nodi ricevuti
                logger.info(f"Received {len(workflow_data['nodes'])} nodes to save")
                for i, node in enumerate(workflow_data['nodes']):
                    logger.info(f"Node {i+1}: ID={node.get('node_id')}, Type={node.get('node_type')}, Pos={node.get('position')}")
                
                # Elimina tutti i nodi esistenti e inserisci quelli nuovi
                from backend.db.workflow_models import WorkflowNode
                logger.info(f"Deleting existing nodes for workflow {workflow_id}")
                db.query(WorkflowNode).filter(
                    WorkflowNode.workflow_id == workflow_id
                ).delete(synchronize_session=False)
                
                # Crea i nuovi nodi
                for node_data in workflow_data["nodes"]:
                    # DEBUG: Log dei dati del nodo per vedere se icon/color arrivano dal frontend
                    print(f"­ƒÜ¿ [BACKEND UPDATE] Node data received: {node_data}")
                    print(f"­ƒÜ¿ [BACKEND UPDATE] Node icon: '{node_data.get('icon', 'NOT_FOUND')}'")
                    print(f"­ƒÜ¿ [BACKEND UPDATE] Node color: '{node_data.get('color', 'NOT_FOUND')}'")
                    print(f"­ƒÜ¿ [BACKEND UPDATE] Node data keys: {list(node_data.keys())}")
                    
                    # Estrae posizione in modo sicuro
                    position = node_data.get("position", {"x": 0, "y": 0})
                    if position is None:
                        position = {"x": 0, "y": 0}
                    
                    logger.info(f"Creating new node: {node_data.get('node_id')} at position {position}")
                    new_node = WorkflowNode(
                        node_id=node_data.get("node_id", f"node_{len(existing_workflow.nodes) + 1}"),
                        workflow_id=workflow_id,
                        node_type=node_data.get("node_type", "default"),
                        name=node_data.get("name", "Nodo"),
                        description=node_data.get("description", ""),
                        config=node_data.get("config", {}),
                        position=position,
                        icon=node_data.get("icon", ""),
                        color=node_data.get("color", "#ffffff")
                    )
                    db.add(new_node)
            except Exception as node_error:
                logger.error(f"Error updating nodes: {node_error}")
                db.rollback()  # Rollback in caso di errore
                raise
        
        if "connections" in workflow_data:
            try:
                # Elimina tutte le connessioni esistenti e inserisci quelle nuove
                from backend.db.workflow_models import WorkflowConnection
                logger.info(f"Deleting existing connections for workflow {workflow_id}")
                db.query(WorkflowConnection).filter(
                    WorkflowConnection.workflow_id == workflow_id
                ).delete(synchronize_session=False)
                
                # Log dettagliato delle connessioni
                logger.info(f"Received {len(workflow_data['connections'])} connections to save")
                logger.info(f"Connection data received: {workflow_data['connections']}")
                
                # Crea le nuove connessioni
                for conn_data in workflow_data["connections"]:
                    # Determina i nomi dei campi corretti (supporta sia source_node che from_node_id)
                    from_node = conn_data.get("from_node_id") or conn_data.get("source_node", "")
                    to_node = conn_data.get("to_node_id") or conn_data.get("target_node", "")
                    from_port = conn_data.get("from_port") or conn_data.get("source_output", "output")
                    to_port = conn_data.get("to_port") or conn_data.get("target_input", "input")
                    
                    logger.info(f"Creating connection: {from_node} ({from_port}) -> {to_node} ({to_port})")
                    
                    if not from_node or not to_node:
                        logger.warning(f"Skipping invalid connection, missing node IDs: {conn_data}")
                        continue
                    
                    new_conn = WorkflowConnection(
                        workflow_id=workflow_id,
                        from_node_id=from_node,
                        to_node_id=to_node,
                        from_port=from_port,
                        to_port=to_port
                    )
                    db.add(new_conn)
            except Exception as conn_error:
                logger.error(f"Error updating connections: {conn_error}")
                db.rollback()  # Rollback in caso di errore
                raise

        # Ensure we are assigning to the mapped attribute, not the Column object
        setattr(existing_workflow, "updated_at", datetime.utcnow())

        # Commit finale di tutte le modifiche
        try:
            db.commit()
            db.refresh(existing_workflow)
            logger.info(f"Successfully committed all changes for workflow {workflow_id}")
        except Exception as commit_error:
            logger.error(f"Error committing changes: {commit_error}")
            db.rollback()
            raise
        
        # Trasforma per la risposta
        try:
            # Prima di preparare la risposta, verifico che i nodi e le connessioni siano stati recuperati correttamente
            logger.info(f"Preparing response for workflow {workflow_id}")
            logger.info(f"Node count in DB: {len(existing_workflow.nodes) if hasattr(existing_workflow, 'nodes') else 0}")
            logger.info(f"Connection count in DB: {len(existing_workflow.connections) if hasattr(existing_workflow, 'connections') else 0}")
            
            updated_workflow = {
                "workflow_id": existing_workflow.workflow_id,
                "name": existing_workflow.name,
                "description": existing_workflow.description or "",
                "is_active": existing_workflow.is_active,
                "is_public": existing_workflow.is_public,
                "created_at": existing_workflow.created_at.isoformat(),
                "updated_at": existing_workflow.updated_at.isoformat(),
                "created_by": existing_workflow.created_by,
                "assigned_groups": existing_workflow.assigned_groups or [],
                "tags": existing_workflow.tags or [],
                "category": existing_workflow.category or "General",
                "color": existing_workflow.color or "#3B82F6",
                "view_state": existing_workflow.view_state or {},
                "nodes": [],
                "connections": []
            }
            
            # Aggiungi nodi solo se esistono
            if hasattr(existing_workflow, 'nodes') and existing_workflow.nodes:
                updated_workflow["nodes"] = [
                    {
                        "node_id": node.node_id,
                        "node_type": node.node_type,
                        "name": node.name,
                        "description": node.description,
                        "config": node.config or {},
                        "position": node.position or {},
                        "width": node.width,
                        "height": node.height,
                        "resizable": node.resizable,
                        "icon": getattr(node, 'icon', ''),
                        "color": getattr(node, 'color', '#ffffff')
                    } for node in existing_workflow.nodes
                ]
                
                # Log per debug
                logger.info(f"Returning {len(updated_workflow['nodes'])} nodes in response")
                for i, node in enumerate(updated_workflow["nodes"]):
                    logger.info(f"Node {i+1}: ID={node['node_id']}, Type={node['node_type']}, Pos={node['position']}")
            else:
                # Se non ci sono nodi, forza un refresh
                logger.warning(f"No nodes found after DB refresh, attempting another refresh")
                db.refresh(existing_workflow)
                
                if hasattr(existing_workflow, 'nodes') and existing_workflow.nodes:
                    updated_workflow["nodes"] = [
                        {
                            "node_id": node.node_id,
                            "node_type": node.node_type,
                            "name": node.name,
                            "description": node.description,
                            "config": node.config or {},
                            "position": node.position or {},
                            "width": node.width,
                            "height": node.height,
                            "resizable": node.resizable,
                            "icon": getattr(node, 'icon', ''),
                            "color": getattr(node, 'color', '#ffffff')
                        } for node in existing_workflow.nodes
                    ]
                    logger.info(f"After second refresh: {len(updated_workflow['nodes'])} nodes")
                else:
                    logger.error(f"Still no nodes after second refresh!")
            
            # Aggiungi connessioni solo se esistono
            if hasattr(existing_workflow, 'connections') and existing_workflow.connections:
                updated_workflow["connections"] = [
                    {
                        "source_node": conn.from_node_id,
                        "target_node": conn.to_node_id,
                        "source_output": conn.from_port,
                        "target_input": conn.to_port,
                        # Aggiungiamo anche i campi originali per compatibilit├á
                        "from_node_id": conn.from_node_id,
                        "to_node_id": conn.to_node_id,
                        "from_port": conn.from_port,
                        "to_port": conn.to_port
                    } for conn in existing_workflow.connections
                ]
                
                # Log per debug
                logger.info(f"Returning {len(updated_workflow['connections'])} connections in response")
                for i, conn in enumerate(updated_workflow["connections"]):
                    logger.info(f"Connection {i+1}: {conn['source_node']} -> {conn['target_node']}")
        except Exception as response_error:
            logger.error(f"Error preparing response: {response_error}")
            # Restituisci almeno i dati di base del workflow senza nodi/connessioni
            updated_workflow = {
                "workflow_id": existing_workflow.workflow_id,
                "name": existing_workflow.name,
                "description": existing_workflow.description or "",
                "created_by": existing_workflow.created_by,
                "category": existing_workflow.category or "General",
                "nodes": [],
                "connections": []
            }
        
        logger.info(f"Workflow {workflow_id} updated successfully")
        logger.info(f"Final response - Nodes: {len(updated_workflow['nodes'])}, Connections: {len(updated_workflow['connections'])}")
        return updated_workflow
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {e}")
        logger.error(f"Exception details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating workflow in database"
        )

# Endpoint per eliminare un workflow
@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina un workflow esistente dal database
    """
    logger.info(f"Deleting workflow with ID: {workflow_id} for user: {current_user.username}")
    
    try:
        # Verifica che il workflow esista
        existing_workflow = WorkflowCRUD.get_workflow(db, workflow_id)
        
        if not existing_workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow with ID '{workflow_id}' not found"
            )
        
        # Verifica i permessi (admin o proprietario pu├▓ eliminare)
        if str(existing_workflow.created_by) != str(current_user.username) and str(current_user.role) != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to delete this workflow"
            )
        
        workflow_name = existing_workflow.name
        
        # Elimina il workflow (le foreign key cascade elimineranno automaticamente nodi e connessioni)
        db.delete(existing_workflow)
        db.commit()
        
        logger.info(f"Workflow {workflow_id} deleted successfully")
        
        return {
            "status": "success",
            "message": f"Workflow '{workflow_name}' has been deleted",
            "workflow_id": workflow_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting workflow from database"
        )


@router.get("/{workflow_id}/input-nodes")
async def get_workflow_input_nodes(
    workflow_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ottiene i nodi di input disponibili per un workflow specifico.
    Utile per configurare i trigger e sapere dove indirizzare i dati.
    """
    # Decodifica l'URL se necessario
    from urllib.parse import unquote
    decoded_workflow_id = unquote(workflow_id)
    logger.info(f"Getting input nodes for workflow: {workflow_id} -> decoded: {decoded_workflow_id}")
    
    try:
        # Ottieni il workflow
        workflow = WorkflowCRUD.get_workflow(db, decoded_workflow_id)
        if not workflow:
            logger.warning(f"Workflow non trovato con ID: {decoded_workflow_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow con ID '{decoded_workflow_id}' non trovato"
            )
        
        # Inizializza il workflow engine per analizzare i nodi
        from backend.engine.workflow_engine import WorkflowEngine
        engine = WorkflowEngine()
        
        # Trova i nodi di input candidati
        input_nodes = engine._find_input_nodes(workflow)
        
        # Prepara la risposta con informazioni dettagliate sui nodi
        input_nodes_info = []
        for node in input_nodes:
            # Ottieni lo schema del nodo per informazioni sui tipi supportati
            node_schema = engine.schema_registry.get_schema(node.node_type)
            input_ports = node_schema.get("input_ports", []) if node_schema else []
            
            # Raccogli i tipi di dati supportati
            supported_types = []
            for port in input_ports:
                port_type = port.get("type", "any")
                supported_types.append({
                    "port_name": port.get("name", "input"),
                    "type": port_type,
                    "required": port.get("required", False),
                    "description": port.get("description", "")
                })
            
            input_nodes_info.append({
                "node_id": node.node_id,
                "node_type": node.node_type,
                "name": node.name,
                "description": node.description,
                "supported_input_types": supported_types,
                "is_recommended_for": _get_recommended_event_types(node.node_type)
            })
        
         
        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.name,
            "input_nodes": input_nodes_info,
            "count": len(input_nodes_info)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting input nodes for workflow {workflow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing workflow input nodes"
        )


def _get_recommended_event_types(node_type: str) -> list:
    """
    Suggerisce i tipi di eventi pi├╣ appropriati per un tipo di nodo.
    """
    recommendations = {
        "pdf_input_node": ["pdf_upload", "file_created"],
        "query_input_node": ["query_request", "search_request"],
        "file_input_node": ["file_upload", "file_created"],
        "text_input_node": ["text_input", "message_received"],
        "image_input_node": ["image_upload", "image_processed"],
        "data_input_node": ["data_received", "api_call"],
    }
    
    return recommendations.get(node_type, ["generic_input"])
