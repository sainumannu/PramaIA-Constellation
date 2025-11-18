"""
CRUD operations per la gestione dei gruppi utenti
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from backend.db.group_models import UserGroup, UserGroupMember, GroupPermission
import uuid
from datetime import datetime

class GroupCRUD:
    """
    Operazioni CRUD per la gestione dei gruppi
    """
    
    @staticmethod
    def create_group(
        db: Session, 
        group_data: Dict[str, Any], 
        created_by: str
    ) -> UserGroup:
        """
        Crea un nuovo gruppo
        """
        # Genera ID univoco se non fornito
        group_id = group_data.get("group_id") or f"group_{uuid.uuid4().hex[:8]}"
        
        db_group = UserGroup(
            group_id=group_id,
            name=group_data["name"],
            description=group_data.get("description"),
            created_by=created_by,
            color=group_data.get("color", "#3B82F6"),
            metadata_info=group_data.get("metadata_info", {})
        )
        
        db.add(db_group)
        db.commit()
        db.refresh(db_group)
        return db_group
    
    @staticmethod
    def get_groups(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[UserGroup]:
        """
        Ottiene la lista dei gruppi
        """
        query = db.query(UserGroup)
        
        if is_active is not None:
            query = query.filter(UserGroup.is_active == is_active)
            
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_group(db: Session, group_id: str) -> Optional[UserGroup]:
        """
        Ottiene un gruppo specifico
        """
        return db.query(UserGroup).filter(UserGroup.group_id == group_id).first()
    
    @staticmethod
    def update_group(
        db: Session, 
        group_id: str, 
        group_data: Dict[str, Any]
    ) -> Optional[UserGroup]:
        """
        Aggiorna un gruppo
        """
        db_group = GroupCRUD.get_group(db, group_id)
        if not db_group:
            return None
            
        # Aggiorna campi
        for field, value in group_data.items():
            if hasattr(db_group, field):
                setattr(db_group, field, value)
        
        db_group.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_group)
        return db_group
    
    @staticmethod
    def delete_group(db: Session, group_id: str) -> bool:
        """
        Elimina un gruppo (soft delete)
        """
        db_group = GroupCRUD.get_group(db, group_id)
        if not db_group:
            return False
            
        db_group.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def add_user_to_group(
        db: Session,
        group_id: str,
        user_id: str,
        role_in_group: str = "member",
        added_by: str = "system"
    ) -> Optional[UserGroupMember]:
        """
        Aggiunge un utente a un gruppo
        """
        # Verifica che il gruppo esista
        group = GroupCRUD.get_group(db, group_id)
        if not group:
            return None
        
        # Verifica se l'utente è già nel gruppo
        existing = db.query(UserGroupMember).filter(
            UserGroupMember.group_id == group_id,
            UserGroupMember.user_id == user_id,
            UserGroupMember.is_active == True
        ).first()
        
        if existing:
            return existing
        
        # Crea nuova membership
        membership = UserGroupMember(
            group_id=group_id,
            user_id=user_id,
            role_in_group=role_in_group,
            added_by=added_by
        )
        
        db.add(membership)
        db.commit()
        db.refresh(membership)
        return membership
    
    @staticmethod
    def remove_user_from_group(
        db: Session,
        group_id: str,
        user_id: str
    ) -> bool:
        """
        Rimuove un utente da un gruppo
        """
        membership = db.query(UserGroupMember).filter(
            UserGroupMember.group_id == group_id,
            UserGroupMember.user_id == user_id,
            UserGroupMember.is_active == True
        ).first()
        
        if not membership:
            return False
        
        membership.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def get_group_members(db: Session, group_id: str) -> List[UserGroupMember]:
        """
        Ottiene i membri di un gruppo
        """
        return db.query(UserGroupMember).filter(
            UserGroupMember.group_id == group_id,
            UserGroupMember.is_active == True
        ).all()
    
    @staticmethod
    def get_user_groups(db: Session, user_id: str) -> List[UserGroup]:
        """
        Ottiene i gruppi di cui un utente fa parte
        """
        return db.query(UserGroup).join(UserGroupMember).filter(
            UserGroupMember.user_id == user_id,
            UserGroupMember.is_active == True,
            UserGroup.is_active == True
        ).all()
    
    @staticmethod
    def bulk_add_users_to_group(
        db: Session,
        group_id: str,
        user_ids: List[str],
        added_by: str = "system"
    ) -> List[UserGroupMember]:
        """
        Aggiunge più utenti a un gruppo in batch
        """
        memberships = []
        
        for user_id in user_ids:
            membership = GroupCRUD.add_user_to_group(
                db, group_id, user_id, added_by=added_by
            )
            if membership:
                memberships.append(membership)
        
        return memberships
