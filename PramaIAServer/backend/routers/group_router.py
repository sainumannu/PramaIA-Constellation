"""
Router per la gestione dei gruppi utenti
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from backend.db.database import get_db
from backend.auth.dependencies import get_current_user
from backend.db.models import User
from backend.crud.group_crud import GroupCRUD
from pydantic import BaseModel

router = APIRouter()

# Pydantic models per validazione
class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#3B82F6"
    metadata_info: Optional[Dict[str, Any]] = {}

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None

class GroupMemberAdd(BaseModel):
    user_ids: List[str]
    role_in_group: Optional[str] = "member"

# Endpoints
@router.get("/groups")
async def get_groups(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ottiene la lista dei gruppi (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli amministratori possono vedere i gruppi"
        )
    
    groups = GroupCRUD.get_groups(db, skip=skip, limit=limit, is_active=is_active)
    
    # Arricchisci con conteggio membri
    result = []
    for group in groups:
        members = GroupCRUD.get_group_members(db, group.group_id)
        group_data = {
            "group_id": group.group_id,
            "name": group.name,
            "description": group.description,
            "created_by": group.created_by,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "is_active": group.is_active,
            "color": group.color,
            "members_count": len(members),
            "members": [{"user_id": m.user_id, "role_in_group": m.role_in_group} for m in members]
        }
        result.append(group_data)
    
    return result

@router.post("/groups")
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea un nuovo gruppo (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli amministratori possono creare gruppi"
        )
    
    try:
        group = GroupCRUD.create_group(
            db=db,
            group_data=group_data.dict(),
            created_by=current_user.username
        )
        return {
            "status": "success",
            "message": "Gruppo creato con successo",
            "group": {
                "group_id": group.group_id,
                "name": group.name,
                "description": group.description,
                "color": group.color
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nella creazione del gruppo: {str(e)}"
        )

@router.get("/groups/{group_id}")
async def get_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ottiene dettagli di un gruppo specifico
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli amministratori possono vedere i dettagli gruppi"
        )
    
    group = GroupCRUD.get_group(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gruppo non trovato"
        )
    
    members = GroupCRUD.get_group_members(db, group_id)
    
    return {
        "group_id": group.group_id,
        "name": group.name,
        "description": group.description,
        "created_by": group.created_by,
        "created_at": group.created_at,
        "updated_at": group.updated_at,
        "is_active": group.is_active,
        "color": group.color,
        "metadata_info": group.metadata_info,
        "members": [
            {
                "user_id": m.user_id,
                "role_in_group": m.role_in_group,
                "added_by": m.added_by,
                "added_at": m.added_at
            } for m in members
        ]
    }

@router.put("/groups/{group_id}")
async def update_group(
    group_id: str,
    group_data: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aggiorna un gruppo
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli amministratori possono modificare gruppi"
        )
    
    group = GroupCRUD.update_group(db, group_id, group_data.dict(exclude_unset=True))
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gruppo non trovato"
        )
    
    return {"status": "success", "message": "Gruppo aggiornato con successo"}

@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Elimina un gruppo (soft delete)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli amministratori possono eliminare gruppi"
        )
    
    success = GroupCRUD.delete_group(db, group_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gruppo non trovato"
        )
    
    return {"status": "success", "message": "Gruppo eliminato con successo"}

@router.post("/groups/{group_id}/members")
async def add_members_to_group(
    group_id: str,
    member_data: GroupMemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Aggiunge membri a un gruppo
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli amministratori possono gestire membri gruppi"
        )
    
    try:
        memberships = GroupCRUD.bulk_add_users_to_group(
            db=db,
            group_id=group_id,
            user_ids=member_data.user_ids,
            added_by=current_user.username
        )
        
        return {
            "status": "success", 
            "message": f"Aggiunti {len(memberships)} membri al gruppo",
            "added_count": len(memberships)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nell'aggiunta membri: {str(e)}"
        )

@router.delete("/groups/{group_id}/members/{user_id}")
async def remove_member_from_group(
    group_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rimuove un membro da un gruppo
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli amministratori possono rimuovere membri"
        )
    
    success = GroupCRUD.remove_user_from_group(db, group_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membro non trovato nel gruppo"
        )
    
    return {"status": "success", "message": "Membro rimosso dal gruppo"}
