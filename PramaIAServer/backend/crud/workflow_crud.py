import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from backend.db.workflow_models import Workflow, WorkflowNode, WorkflowConnection, WorkflowExecution
from backend.schemas.workflow_schemas import (
    WorkflowCreate, WorkflowUpdate, WorkflowNodeCreate, WorkflowConnectionCreate,
    WorkflowExecutionCreate, ExecutionStatus
)
from backend.schemas.user_schemas import UserInToken
from backend.auth.dependencies import is_admin_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowCRUD:
    """
    Classe per le operazioni CRUD sui workflow
    """
    
    @staticmethod
    def generate_workflow_id() -> str:
        """Genera un ID univoco per il workflow"""
        return f"wf_{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def generate_execution_id() -> str:
        """Genera un ID univoco per l'esecuzione"""
        return f"exec_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def create_workflow(db: Session, workflow_data: WorkflowCreate, created_by: str) -> Workflow:
        """
        Crea un nuovo workflow con nodi e connessioni
        """
        # Genera ID univoco per il workflow
        workflow_id = WorkflowCRUD.generate_workflow_id()
        
        # Crea il workflow principale
        db_workflow = Workflow(
            workflow_id=workflow_id,
            name=workflow_data.name,
            description=workflow_data.description,
            created_by=created_by,
            is_active=workflow_data.is_active,
            is_public=workflow_data.is_public,
            assigned_groups=workflow_data.assigned_groups
        )
        
        db.add(db_workflow)
        db.flush()  # Per ottenere l'ID
        
        # Crea i nodi
        for node_data in workflow_data.nodes:
            db_node = WorkflowNode(
                node_id=node_data.node_id,
                workflow_id=workflow_id,
                node_type=node_data.node_type,  # Rimosso .value
                name=node_data.name,
                description=node_data.description,
                config=node_data.config,
                position=node_data.position.dict(),
                width=node_data.width or 200,
                height=node_data.height or 80,
                resizable=node_data.resizable if node_data.resizable is not None else True
            )
            db.add(db_node)
        
        # Crea le connessioni
        for conn_data in workflow_data.connections:
            db_conn = WorkflowConnection(
                workflow_id=workflow_id,
                from_node_id=conn_data.from_node_id,
                to_node_id=conn_data.to_node_id,
                from_port=conn_data.from_port,
                to_port=conn_data.to_port
            )
            db.add(db_conn)
        
        db.commit()
        db.refresh(db_workflow)
        return db_workflow

    @staticmethod
    def get_workflow(db: Session, workflow_id: str) -> Optional[Workflow]:
        """
        Ottiene un workflow per ID con tutte le sue relazioni (nodi e connessioni)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"­ƒöì Recupero workflow con ID '{workflow_id}'")
            
            # Utilizziamo joinedload per caricare esplicitamente le relazioni
            from sqlalchemy.orm import joinedload
            
            # Query con joinedload esplicito per caricare nodi e connessioni
            workflow = db.query(Workflow).options(
                joinedload(Workflow.nodes),
                joinedload(Workflow.connections)
            ).filter(Workflow.workflow_id == workflow_id).first()
            
            if workflow:
                logger.info(f"Ô£à Workflow trovato: {workflow.name} (ID: {workflow.workflow_id})")
                logger.info(f"­ƒôè Nodi: {len(workflow.nodes) if workflow.nodes else 0}, Connessioni: {len(workflow.connections) if workflow.connections else 0}")
                
                # Verifica la presenza di nodi e connessioni
                if not workflow.nodes or len(workflow.nodes) == 0:
                    logger.warning(f"ÔÜá´©Å Il workflow {workflow_id} non ha nodi!")
                if not workflow.connections or len(workflow.connections) == 0:
                    logger.warning(f"ÔÜá´©Å Il workflow {workflow_id} non ha connessioni!")
            else:
                logger.warning(f"ÔØî Workflow con ID '{workflow_id}' non trovato")
                
            return workflow
            
        except Exception as e:
            logger.error(f"ÔØî Errore nel recupero del workflow {workflow_id}: {str(e)}")
            # Non catturiamo l'eccezione ma la propaghiamo per gestirla nel chiamante
            raise

    @staticmethod
    def get_workflows(
        db: Session, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100,
        is_public: Optional[bool] = None,
        is_active: Optional[bool] = None
    ) -> List[Workflow]:
        """
        Ottiene lista dei workflow accessibili all'utente
        """
        query = db.query(Workflow)
        
        # Filtro per workflow pubblici o creati dall'utente
        query = query.filter(
            or_(
                Workflow.is_public == True,
                Workflow.created_by == user_id
            )
        )
        
        # Filtri aggiuntivi
        if is_public is not None:
            query = query.filter(Workflow.is_public == is_public)
         
        if is_active is not None:
            query = query.filter(Workflow.is_active == is_active)
        
        # Log della query SQL generata
        logger.info(f"[get_workflows] SQL: {str(query.statement.compile(compile_kwargs={'literal_binds': True}))}")
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_workflow(
        db: Session, 
        workflow_id: str, 
        workflow_data: WorkflowUpdate,
        user: UserInToken
    ) -> Optional[Workflow]:
        """
        Aggiorna un workflow esistente.
        Cancella e ricrea nodi e connessioni per garantire la coerenza.
        Gli admin possono modificare qualsiasi workflow, gli utenti normali solo i propri.
        """
        import logging
        logger = logging.getLogger(__name__)
        db_workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
        if not db_workflow:
            logger.warning(f"Tentativo di aggiornare un workflow non esistente: ID='{workflow_id}'")
            return None
        is_owner = db_workflow.created_by == user.username
        can_edit = is_admin_user(user) or bool(is_owner)
        if not can_edit:
            logger.error(f"Permesso negato per l'utente '{user.username}' su workflow '{workflow_id}'")
            return None
        update_data = workflow_data.model_dump(exclude_unset=True)
        nodes_data = update_data.pop('nodes', None)
        connections_data = update_data.pop('connections', None)
        for field, value in update_data.items():
            setattr(db_workflow, field, value)
        if nodes_data is not None:
            db.query(WorkflowConnection).filter(WorkflowConnection.workflow_id == workflow_id).delete(synchronize_session=False)
            db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow_id).delete(synchronize_session=False)
            db.flush()
            for node_data in nodes_data:
                db_node = WorkflowNode(
                    workflow_id=workflow_id,
                    node_id=node_data.get('node_id'),
                    node_type=node_data.get('node_type'),
                    name=node_data.get('name'),
                    description=node_data.get('description'),
                    config=node_data.get('config', {}),
                    position=node_data.get('position', {}),
                    width=node_data.get('width', 200),
                    height=node_data.get('height', 80),
                    resizable=node_data.get('resizable', True)
                )
                db.add(db_node)
            if connections_data is not None:
                for conn_data in connections_data:
                    db_connection = WorkflowConnection(
                        workflow_id=workflow_id,
                        from_node_id=conn_data.get('from_node_id'),
                        to_node_id=conn_data.get('to_node_id'),
                        from_port=conn_data.get('from_port', 'output'),
                        to_port=conn_data.get('to_port', 'input')
                    )
                    db.add(db_connection)
        setattr(db_workflow, "updated_at", datetime.utcnow())
        try:
            db.commit()
            db.refresh(db_workflow)
            return db_workflow
        except Exception as e:
            logger.error(f"Errore durante il commit per il workflow '{workflow_id}': {e}", exc_info=True)
            db.rollback()
            raise

    @staticmethod
    def delete_workflow(db: Session, workflow_id: str, user: UserInToken) -> bool:
        """
        Elimina un workflow
        Gli admin possono eliminare qualsiasi workflow, gli utenti normali solo i propri
        """
        print(f"[DEBUG] ===== INIZIO DELETE_WORKFLOW =====")
        print(f"[DEBUG] Parametri ricevuti:")
        print(f"  - workflow_id: '{workflow_id}' (tipo: {type(workflow_id)}, lunghezza: {len(workflow_id)})")
        print(f"  - user.username: '{user.username}' (tipo: {type(user.username)})")
        print(f"  - user.role: '{user.role}'")
        print(f"  - is_admin: {is_admin_user(user)}")
        
        # Mostriamo tutti i workflow esistenti per debug
        all_workflows = db.query(Workflow).all()
        print(f"[DEBUG] Workflow esistenti nel database ({len(all_workflows)}):")
        for i, wf in enumerate(all_workflows):
            print(f"  {i+1}. ID='{wf.workflow_id}' Nome='{wf.name}' CreatedBy='{wf.created_by}'")
        
        # Prima cerchiamo il workflow per ID
        db_workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
        
        if not db_workflow:
            print(f"[DEBUG] ÔØî Workflow con ID '{workflow_id}' NON TROVATO nel database")
            print(f"[DEBUG] Query utilizzata: Workflow.workflow_id == '{workflow_id}'")
            return False
        
        print(f"[DEBUG] Ô£à Workflow trovato:")
        print(f"  - Nome: '{db_workflow.name}'")
        print(f"  - CreatedBy: '{db_workflow.created_by}'")
        print(f"  - RequestedBy: '{user.username}'")
        print(f"  - Confronto permessi: '{db_workflow.created_by}' == '{user.username}' ? {db_workflow.created_by == user.username}")
        
        # Verifica permessi: creatore o admin pu├▓ eliminare
        if (not is_admin_user(user)) and (db_workflow.created_by != user.username):
            print(f"[DEBUG] ÔØî Permessi negati")
            print(f"  - Workflow creato da: '{db_workflow.created_by}'")
            print(f"  - Eliminazione richiesta da: '{user.username}'")
            print(f"  - Utente ├¿ admin: {is_admin_user(user)}")
            return False
        
        print(f"[DEBUG] Ô£à Permessi OK, procedo con l'eliminazione")
        try:
            db.delete(db_workflow)
            db.commit()
            print(f"[DEBUG] Ô£à Workflow eliminato con successo")
            print(f"[DEBUG] ===== FINE DELETE_WORKFLOW =====")
            return True
        except Exception as e:
            print(f"[DEBUG] ÔØî Errore durante l'eliminazione: {e}")
            db.rollback()
            print(f"[DEBUG] ===== FINE DELETE_WORKFLOW (ERROR) =====")
            return False

    @staticmethod
    def add_node_to_workflow(
        db: Session, 
        workflow_id: str, 
        node_data: WorkflowNodeCreate,
        user: UserInToken
    ) -> Optional[WorkflowNode]:
        """
        Aggiunge un nodo a un workflow esistente
        Gli admin possono modificare qualsiasi workflow, gli utenti normali solo i propri
        """
        # Verifica che l'utente possa modificare il workflow
        if is_admin_user(user):
            # Admin pu├▓ modificare qualsiasi workflow
            workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
        else:
            # Utente normale pu├▓ modificare solo i propri workflow
            workflow = db.query(Workflow).filter(
                and_(
                    Workflow.workflow_id == workflow_id,
                    Workflow.created_by == user.username
                )
            ).first()
        
        if not workflow:
            return None
        
        db_node = WorkflowNode(
            node_id=node_data.node_id,
            workflow_id=workflow_id,
            node_type=node_data.node_type,
            name=node_data.name,
            description=node_data.description,
            config=node_data.config,
            position=node_data.position.dict(),
            width=node_data.width or 200,
            height=node_data.height or 80,
            resizable=node_data.resizable if node_data.resizable is not None else True
        )
        
        db.add(db_node)
        setattr(workflow, "updated_at", datetime.utcnow())
        db.commit()
        db.refresh(db_node)
        return db_node

    @staticmethod
    def remove_node_from_workflow(
        db: Session, 
        workflow_id: str, 
        node_id: str,
        user: UserInToken
    ) -> bool:
        """
        Rimuove un nodo da un workflow
        Gli admin possono modificare qualsiasi workflow, gli utenti normali solo i propri
        """
        # Verifica permessi
        if is_admin_user(user):
            # Admin pu├▓ modificare qualsiasi workflow
            workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
        else:
            # Utente normale pu├▓ modificare solo i propri workflow
            workflow = db.query(Workflow).filter(
                and_(
                    Workflow.workflow_id == workflow_id,
                    Workflow.created_by == user.username
                )
            ).first()
        
        if not workflow:
            return False
        
        # Rimuove prima le connessioni che coinvolgono questo nodo
        db.query(WorkflowConnection).filter(
            and_(
                WorkflowConnection.workflow_id == workflow_id,
                or_(
                    WorkflowConnection.from_node_id == node_id,
                    WorkflowConnection.to_node_id == node_id
                )
            )
        ).delete()
        
        # Rimuove il nodo
        deleted_count = db.query(WorkflowNode).filter(
            and_(
                WorkflowNode.workflow_id == workflow_id,
                WorkflowNode.node_id == node_id
            )
        ).delete()
        
        if deleted_count > 0:
            setattr(workflow, "updated_at", datetime.utcnow())
            db.commit()
            return True
        
        return False

    @staticmethod
    def add_connection_to_workflow(
        db: Session, 
        workflow_id: str, 
        connection_data: WorkflowConnectionCreate,
        user: UserInToken
    ) -> Optional[WorkflowConnection]:
        """
        Aggiunge una connessione a un workflow
        Gli admin possono modificare qualsiasi workflow, gli utenti normali solo i propri
        """
        # Verifica permessi
        if is_admin_user(user):
            # Admin pu├▓ modificare qualsiasi workflow
            workflow = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
        else:
            # Utente normale pu├▓ modificare solo i propri workflow
            workflow = db.query(Workflow).filter(
                and_(
                    Workflow.workflow_id == workflow_id,
                    Workflow.created_by == user.username
                )
            ).first()
        
        if not workflow:
            return None
        
        # Verifica che i nodi esistano
        from_node_exists = db.query(WorkflowNode).filter(
            and_(
                WorkflowNode.workflow_id == workflow_id,
                WorkflowNode.node_id == connection_data.from_node_id
            )
        ).first()
        
        to_node_exists = db.query(WorkflowNode).filter(
            and_(
                WorkflowNode.workflow_id == workflow_id,
                WorkflowNode.node_id == connection_data.to_node_id
            )
        ).first()
        
        if not from_node_exists or not to_node_exists:
            return None
        
        db_connection = WorkflowConnection(
            workflow_id=workflow_id,
            from_node_id=connection_data.from_node_id,
            to_node_id=connection_data.to_node_id,
            from_port=connection_data.from_port,
            to_port=connection_data.to_port
        )
        
        db.add(db_connection)
        setattr(workflow, "updated_at", datetime.utcnow())
        db.commit()
        db.refresh(db_connection)
        return db_connection

    @staticmethod
    def create_execution(
        db: Session, 
        workflow_id: str, 
        user_id: str,
        input_data: Dict[str, Any]
    ) -> WorkflowExecution:
        """
        Crea una nuova esecuzione per un workflow
        """
        execution_id = WorkflowCRUD.generate_execution_id()
        
        db_execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            user_id=user_id,
            status=ExecutionStatus.RUNNING.value,
            input_data=input_data
        )
        
        db.add(db_execution)
        db.commit()
        db.refresh(db_execution)
        return db_execution

    @staticmethod
    def update_execution_status(
        db: Session,
        execution_id: str,
        status: ExecutionStatus,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[WorkflowExecution]:
        """
        Aggiorna lo status di un'esecuzione
        """
        db_execution = db.query(WorkflowExecution).filter(
            WorkflowExecution.execution_id == execution_id
        ).first()
        
        if not db_execution:
            return None
        
        setattr(db_execution, "status", status.value)
        
        if output_data is not None:
            db_execution.output_data = output_data
        if error_message is not None:
            setattr(db_execution, "error_message", error_message)
        
        if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
            setattr(db_execution, "completed_at", datetime.utcnow())
            
            # Calcola tempo di esecuzione
            if getattr(db_execution, "started_at", None):
                execution_time = (db_execution.completed_at - db_execution.started_at).total_seconds() * 1000
                setattr(db_execution, "execution_time_ms", int(execution_time))
        
        db.commit()
        db.refresh(db_execution)
        return db_execution

    @staticmethod
    def get_execution(db: Session, execution_id: str) -> Optional[WorkflowExecution]:
        """
        Ottiene un'esecuzione per ID
        """
        return db.query(WorkflowExecution).filter(
            WorkflowExecution.execution_id == execution_id
        ).first()

    @staticmethod
    def get_workflow_executions(
        db: Session, 
        workflow_id: str, 
        user_id: str,
        skip: int = 0, 
        limit: int = 50
    ) -> List[WorkflowExecution]:
        """
        Ottiene le esecuzioni di un workflow per un utente
        """
        return db.query(WorkflowExecution).filter(
            and_(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.user_id == user_id
            )
        ).order_by(WorkflowExecution.started_at.desc()).offset(skip).limit(limit).all()
