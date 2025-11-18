from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Depends, Form
from pydantic import BaseModel
from fastapi.responses import FileResponse # Importa FileResponse
# from fastapi.responses import JSONResponse
from typing import List
import shutil
import math # Importa il modulo math

from backend.services import document_service # Servizio per la logica di business
from backend.core.rag_engine import remove_pdf as rag_remove_pdf, get_index_status # Funzioni RAG
from backend.core.config import DATA_DIR, INDEXES_DIR, DATA_INDEX_PATH
from backend.auth.dependencies import get_current_user, get_current_admin_user # Non importare User da qui
from backend.schemas.user_schemas import UserInToken # Importa il modello Pydantic corretto per l'utente
# Rimosso import rag_vectorstore
from backend.app.clients.vectorstore_client import VectorstoreServiceClient
from backend.utils import get_logger # Importa il logger unificato


router = APIRouter()
logger = get_logger() # Usa il logger unificato che invia al LogService


@router.get("/vectorstore/list", summary="Elenco documenti indicizzati nel vectorstore")
async def list_vectorstore_documents(current_user: UserInToken = Depends(get_current_user)):
    """
    Restituisce la lista dei metadati di tutti i documenti indicizzati nel vectorstore.
    """
    try:
        # Usa VectorstoreService per recuperare i documenti
        client = VectorstoreServiceClient()
        collection_name = "pdf_documents"
        
        # Ottieni la lista dei documenti dal servizio
        response = client.list_documents(collection_name)
        if not response or "documents" not in response:
            logger.error(
                "Nessun documento trovato o risposta non valida dal VectorstoreService",
                details={"response": str(response), "collection": collection_name}
            )
            return {"count": 0, "documents": []}
        
        # Formatta i risultati
        docs = []
        for doc in response.get("documents", []):
            doc_item = {
                "id": doc.get("id"),
                "metadata": doc.get("metadata", {}),
                "content": doc.get("document", "")
            }
            docs.append(doc_item)
        
        count = len(docs)
        logger.debug(
            f"Trovati {count} documenti nel vectorstore", 
            details={"count": count, "collection": collection_name}
        )
        return {"count": count, "documents": docs}
    except Exception as e:
        logger.error(f"[VECTORSTORE_LIST] Errore: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 5

@router.post("/semantic-search/")
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Ricerca semantica diretta nel vectorstore.
    Restituisce i documenti più simili alla query.
    """
    try:
        logger.debug(f"[SEMANTIC_SEARCH] Richiesta ricevuta: query='{request.query}', top_k={request.top_k}, user_id={getattr(current_user, 'user_id', None)}")
        
        # Usa VectorstoreService per la ricerca semantica
        client = VectorstoreServiceClient()
        collection_name = "pdf_documents"
        
        # Esegui la query
        response = client.query(collection_name, request.query, request.top_k)
        
        # Formatta i risultati
        results = []
        for match in response.get("matches", []):
            result = {
                "content": match.get("document", ""),
                "metadata": match.get("metadata", {}),
                "score": match.get("similarity_score", 0)
            }
            results.append(result)
        
        logger.debug(f"[SEMANTIC_SEARCH] Trovati {len(results)} risultati")
        return {"results": results}
    except Exception as e:
        logger.error(f"[SEMANTIC_SEARCH] Errore: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def format_file_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

@router.post("/upload/")
async def upload_pdfs(
    files: List[UploadFile] = File(..., description="Lista di file PDF da caricare."),
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Carica uno o più file PDF, li processa e salva i metadati.
    """
    logger.info(f"Upload request received from user: {current_user.user_id}, role: {current_user.role}")
    user_id = current_user.user_id
    if not user_id:
        logger.error("user_id è None durante upload_pdfs")
        raise HTTPException(status_code=400, detail="user_id mancante nel token utente")
    try:
        processed_files = []
        errors = []
        for file in files:
            try:
                content = await file.read()
                if not file.filename:
                    logger.error("filename è None durante upload_pdfs")
                    raise HTTPException(status_code=400, detail="filename mancante")
                logger.info(f"Processing file {file.filename} for user {user_id}")
                await document_service.process_uploaded_file(content, file.filename, user_id)
                processed_files.append(file.filename)
                logger.info(f"File '{file.filename}' uploaded and processed successfully by user '{user_id}'.")
            except Exception as e_file:
                logger.error(f"Error processing file '{getattr(file, 'filename', None)}' for user '{user_id}': {e_file}", exc_info=True)
                errors.append({"filename": getattr(file, 'filename', None), "error": str(e_file)})
        
        if errors:
            return {"message": f"{len(processed_files)} file(s) processed. {len(errors)} file(s) failed.", "processed_files": processed_files, "errors": errors}
        return {"message": f"{len(files)} file(s) uploaded and processed successfully.", "uploaded_files": processed_files}
    except Exception as e:
        logger.error(f"Error during PDF upload for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")

@router.post("/upload-with-visibility/")
async def upload_pdfs_with_visibility(
    files: List[UploadFile] = File(..., description="Lista di file PDF da caricare."),
    is_public: bool = Form(False, description="Se true, i documenti saranno visibili a tutti gli utenti"),
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Carica uno o più file PDF con opzione di visibilità, li processa e salva i metadati.
    """
    logger.info(f"Upload with visibility request from user: {current_user.user_id}, is_public: {is_public}")
    user_id = current_user.user_id
    if not user_id:
        logger.error("user_id è None durante upload_pdfs_with_visibility")
        raise HTTPException(status_code=400, detail="user_id mancante nel token utente")
    try:
        processed_files = []
        errors = []
        for file in files:
            try:
                content = await file.read()
                if not file.filename:
                    logger.error("filename è None durante upload_pdfs_with_visibility")
                    raise HTTPException(status_code=400, detail="filename mancante")
                logger.info(f"Processing file {file.filename} for user {user_id} (public: {is_public})")
                await document_service.process_uploaded_file(content, file.filename, user_id, is_public)
                processed_files.append({
                    "filename": file.filename,
                    "is_public": is_public,
                    "owner": user_id
                })
                logger.info(f"File '{file.filename}' uploaded and processed successfully by user '{user_id}' (public: {is_public}).")
            except Exception as e_file:
                logger.error(f"Error processing file '{getattr(file, 'filename', None)}' for user '{user_id}': {e_file}", exc_info=True)
                errors.append({"filename": getattr(file, 'filename', None), "error": str(e_file)})
        
        if errors:
            return {"message": f"{len(processed_files)} file(s) processed. {len(errors)} file(s) failed.", "processed_files": processed_files, "errors": errors}
        return {"message": f"{len(files)} file(s) uploaded and processed successfully.", "uploaded_files": processed_files}
    except Exception as e:
        logger.error(f"Error during PDF upload for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")

@router.get("/")
async def get_documents(current_user: UserInToken = Depends(get_current_user)):
    """
    Recupera la lista dei metadati dei documenti per l'utente corrente.
    Gli amministratori vedono tutti i documenti.
    """
    user_id = current_user.user_id
    if not user_id:
        logger.error("user_id è None durante get_documents")
        raise HTTPException(status_code=400, detail="user_id mancante nel token utente")
    try:
        files_metadata = document_service.load_file_metadata(user_id, current_user.role)

        files_with_formatted_size = []
        total_size_bytes = 0

        for file_meta in files_metadata:
            size_bytes = file_meta.get("size", 0)
            total_size_bytes += size_bytes
            files_with_formatted_size.append({
                **file_meta,
                "size_human": format_file_size(size_bytes)
            })

        if current_user.role == "admin":
            return {
                "files": files_with_formatted_size,
                "total_files": len(files_with_formatted_size),
                "total_size_bytes": total_size_bytes,
                "total_size_human": format_file_size(total_size_bytes)
            }
        else:
            return {"files": files_with_formatted_size}
    except Exception as e:
        logger.error(f"Error fetching documents for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_document(filename: str, current_user: UserInToken = Depends(get_current_user)):
    """
    Permette il download di un documento specificato.
    Solo il proprietario del documento o un amministratore possono scaricarlo.
    """
    file_details = document_service.get_file_details(filename)

    if not file_details:
        logger.warning(f"Attempt to download non-existent file metadata for '{filename}' by user '{current_user.user_id}'.")
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found in metadata.")

    file_owner_id = file_details.get("owner")
    user_is_admin = current_user.role == "admin"

    if not user_is_admin and file_owner_id != current_user.user_id:
        logger.warning(f"User '{current_user.user_id}' (not admin) attempted to download file '{filename}' owned by '{file_owner_id}'. Access denied.")
        raise HTTPException(status_code=403, detail="Not authorized to download this file.")

    file_path_on_disk = DATA_DIR / filename
    if not file_path_on_disk.exists():
        logger.error(f"File '{filename}' found in metadata but not on disk at {file_path_on_disk} for download by user '{current_user.user_id}'.")
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found on disk.")

    # Per i file PDF, puoi specificare il media_type. Per altri tipi, potresti ometterlo o usare 'application/octet-stream'.
    media_type = 'application/pdf' if filename.lower().endswith(".pdf") else 'application/octet-stream'
    logger.info(f"User '{current_user.user_id}' downloading file '{filename}'.")
    return FileResponse(path=file_path_on_disk, filename=filename, media_type=media_type)

@router.delete("/{filename}")
async def delete_document(filename: str, current_user: UserInToken = Depends(get_current_user)):
    """
    Elimina un documento specificato.
    Solo il proprietario del documento o un amministratore possono eliminarlo.
    L'eliminazione comprende la rimozione dall'indice RAG, dal disco e dai metadati.
    """
    requesting_user_id = current_user.user_id
    user_is_admin = current_user.role == "admin"

    # Recupera i dettagli del file specifico dal servizio
    # Si presume che document_service.get_file_details(filename) restituisca un dict con 'owner' o None
    file_details = document_service.get_file_details(filename)

    if not file_details:
        logger.warning(f"Attempt to delete non-existent file metadata for '{filename}' by user '{requesting_user_id}'.")
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found in metadata.")

    file_owner_id = file_details.get("owner")

    # Autorizzazione: solo l'owner o un admin possono eliminare
    if not user_is_admin and file_owner_id != requesting_user_id:
        logger.warning(f"User '{requesting_user_id}' (not admin) attempted to delete file '{filename}' owned by '{file_owner_id}'. Access denied.")
        raise HTTPException(status_code=403, detail="Not authorized to delete this file.")

    try:
        # 1. Rimuovi dal RAG engine
        success_rag = rag_remove_pdf(filename) # rag_remove_pdf dovrebbe usare percorsi da config
        if success_rag:
            logger.info(f"File '{filename}' removed from RAG index by user '{requesting_user_id}'.")
        else:
            # Potrebbe essere un'inconsistenza se il file è nei metadati ma non nell'indice RAG.
            logger.warning(f"File '{filename}' not found in RAG index or error during RAG removal by user '{requesting_user_id}'. Proceeding with other deletions.")

        # 2. Rimuovi il file fisico
        file_path_on_disk = DATA_DIR / filename
        if file_path_on_disk.exists():
            file_path_on_disk.unlink()
            logger.info(f"File '{filename}' deleted from disk at {file_path_on_disk} by user '{requesting_user_id}'.")
        else:
            logger.warning(f"File '{filename}' not found on disk at {file_path_on_disk} during deletion attempt by user '{requesting_user_id}'.")

        # 3. Rimuovi dai metadati
        document_service.delete_file_metadata(filename)
        logger.info(f"Metadata for file '{filename}' deleted by user '{requesting_user_id}'.")

        return {"message": f"File '{filename}' and its metadata deleted successfully."}
    except HTTPException:
        raise # Rilancia le HTTPException specifiche
    except Exception as e:
        logger.error(f"Unexpected error deleting document '{filename}' for user '{requesting_user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while deleting document: {str(e)}")

@router.post("/reset_index/")
async def reset_index(_: UserInToken = Depends(get_current_admin_user)): # Usa get_current_admin_user per proteggere l'endpoint
    """
    Resetta completamente l'indice RAG, i file PDF caricati e i metadati dei documenti.
    Richiede privilegi di amministratore.
    """
    if INDEXES_DIR.exists() and INDEXES_DIR.is_dir():
        shutil.rmtree(INDEXES_DIR)
        logger.info(f"Admin reset: RAG indexes directory '{INDEXES_DIR}' removed.")
    if DATA_DIR.exists():
        for f in DATA_DIR.glob("*.pdf"): # Usa DATA_DIR da config
            try:
                f.unlink()
            except Exception as e_file:
                logger.error(f"Admin reset: Error deleting file {f} during index reset: {e_file}", exc_info=True)
        logger.info(f"Admin reset: PDF files from data directory '{DATA_DIR}' removed.")
    if DATA_INDEX_PATH.exists(): # Usa DATA_INDEX_PATH da config
        DATA_INDEX_PATH.unlink()
        logger.info(f"Admin reset: Data index file '{DATA_INDEX_PATH}' removed.")
    
    # Azzera anche le collezioni nel VectorstoreService
    try:
        client = VectorstoreServiceClient()
        collections = client.list_collections()
        
        for collection_name in collections:
            client.delete_collection(collection_name)
            logger.info(f"Admin reset: Collection '{collection_name}' removed from VectorstoreService.")
            
        # Ricrea la collezione principale
        client.create_collection("pdf_documents")
        logger.info(f"Admin reset: Collection 'pdf_documents' recreated in VectorstoreService.")
    except Exception as e:
        logger.error(f"Admin reset: Error resetting VectorstoreService collections: {e}", exc_info=True)
    
    return {"status": "Index, data files, and metadata reset successfully."}

@router.get("/status/", summary="Get RAG Index Status")
async def get_rag_index_status(_: UserInToken = Depends(get_current_user)): # O admin_required se solo admin
    """
    Restituisce lo stato dell'indice RAG (es. se esiste, numero documenti).
    """
    try:
        status = get_index_status() # Assicurati che get_index_status sia aggiornato per usare config
        return status
    except Exception as e:
        logger.error(f"Error fetching RAG index status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get RAG index status.")

@router.patch("/{filename}/visibility")
async def update_document_visibility(
    filename: str,
    is_public: bool = Form(..., description="Nuova visibilità del documento"),
    current_user: UserInToken = Depends(get_current_user)
):
    """
    Aggiorna la visibilità di un documento esistente.
    Solo il proprietario o l'admin possono modificare la visibilità.
    """
    logger.info(f"Update visibility request for '{filename}' to is_public={is_public} by user {current_user.user_id}")
    
    user_id = current_user.user_id
    if not user_id:
        logger.error("user_id è None durante update_document_visibility")
        raise HTTPException(status_code=400, detail="user_id mancante nel token utente")
    if not filename:
        logger.error("filename è None durante update_document_visibility")
        raise HTTPException(status_code=400, detail="filename mancante")
    success, message = document_service.update_file_visibility(
        filename, is_public, user_id, current_user.role
    )
    
    if not success:
        if "Non autorizzato" in message:
            raise HTTPException(status_code=403, detail=message)
        elif "non trovato" in message:
            raise HTTPException(status_code=404, detail=message)
        else:
            raise HTTPException(status_code=500, detail=message)
    
    return {
        "message": message,
        "filename": filename,
        "is_public": is_public,
        "updated_by": user_id
    }
