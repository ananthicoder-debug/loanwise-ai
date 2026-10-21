"""
routes/documents.py
---------------------
Document management with real file upload storage.

GET    /api/documents                  -> list user's documents
POST   /api/documents/upload           -> upload actual file (multipart)
POST   /api/documents                  -> add metadata-only entry (legacy support)
DELETE /api/documents/{id}             -> remove a document entry + file
GET    /api/documents/{id}/download    -> download file (user's own docs only)

Admin:
GET    /api/admin/documents            -> list all documents pending/verified
PUT    /api/admin/documents/{id}/verify -> update verification status
GET    /api/admin/documents/{id}/download -> admin download any document
"""

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form
)
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from database.mongodb import collections
from utils.deps import get_current_user, get_current_admin

router = APIRouter(tags=["documents"])

# ??? Config ???????????????????????????????????????????????????????????????????
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "documents"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
MAX_FILE_SIZE_MB = 10
DOCUMENT_TYPES = [
    "Identity Proof", "Address Proof", "Income Proof", "Bank Statement",
    "Employment Proof", "Property Document", "Education Certificate", "Other",
]


# ??? Pydantic models ??????????????????????????????????????????????????????????

class DocumentCreateRequest(BaseModel):
    document_type: str
    file_name: str
    notes: Optional[str] = ""


class DocumentVerifyRequest(BaseModel):
    verification_status: str      # Verified | Rejected | Pending Review
    admin_notes: Optional[str] = ""


# ??? Helpers ??????????????????????????????????????????????????????????????????

def _check_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    return ext


def _serialize(doc: dict) -> dict:
    doc["_id"]     = str(doc["_id"])
    doc["user_id"] = str(doc["user_id"])
    if doc.get("stored_filename"):
        doc["download_url"] = f"/api/documents/{doc['_id']}/download"
    doc.pop("stored_filename", None)   # don't expose server path
    if doc.get("verified_at") and hasattr(doc.get("verified_at"), "isoformat"):
        doc["verified_at"] = doc["verified_at"].isoformat()
    return doc


# ??? User endpoints ???????????????????????????????????????????????????????????

@router.get("/api/documents")
def list_documents(user: dict = Depends(get_current_user)):
    docs = list(
        collections["documents"].find({"user_id": user["_id"]}).sort("created_at", -1)
    )
    return [_serialize(d) for d in docs]


@router.post("/api/documents/upload")
async def upload_document(
    document_type: str = Form(...),
    notes:         str = Form(default=""),
    file:          UploadFile = File(...),
    user:          dict = Depends(get_current_user),
):
    """Upload an actual document file (PDF, JPG, PNG, DOC, DOCX). Max 10 MB."""
    if document_type not in DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document_type. Must be one of: {', '.join(DOCUMENT_TYPES)}",
        )
    ext = _check_extension(file.filename or "file.pdf")
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File size {size_mb:.1f} MB exceeds limit of {MAX_FILE_SIZE_MB} MB.",
        )

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_type = document_type.replace(" ", "_").lower()
    stored_filename = f"{str(user['_id'])}_{safe_type}_{ts}{ext}"
    with open(UPLOAD_DIR / stored_filename, "wb") as f_out:
        f_out.write(content)

    doc = {
        "user_id":            user["_id"],
        "document_type":      document_type,
        "file_name":          file.filename or stored_filename,
        "stored_filename":    stored_filename,
        "file_size_kb":       round(len(content) / 1024, 1),
        "file_extension":     ext,
        "notes":              notes,
        "upload_date":        datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "verification_status": "Pending Review",
        "admin_notes":        "",
        "verified_by":        "",
        "verified_at":        None,
        "created_at":         datetime.now(timezone.utc),
    }
    result = collections["documents"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)


@router.post("/api/documents")
def add_document_metadata(payload: DocumentCreateRequest, user: dict = Depends(get_current_user)):
    """Legacy: add metadata-only document entry (no file stored)."""
    doc = {
        "user_id":            user["_id"],
        "document_type":      payload.document_type,
        "file_name":          payload.file_name,
        "stored_filename":    None,
        "file_size_kb":       None,
        "file_extension":     None,
        "notes":              payload.notes or "",
        "upload_date":        datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "verification_status": "Pending Review",
        "admin_notes":        "",
        "verified_by":        "",
        "verified_at":        None,
        "created_at":         datetime.now(timezone.utc),
    }
    result = collections["documents"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)


@router.get("/api/documents/{doc_id}/download")
def download_document(doc_id: str, user: dict = Depends(get_current_user)):
    """Allow a user to download their own uploaded document."""
    try:
        doc = collections["documents"].find_one(
            {"_id": ObjectId(doc_id), "user_id": user["_id"]}
        )
    except InvalidId:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not doc.get("stored_filename"):
        raise HTTPException(status_code=404, detail="No file stored for this document entry.")
    file_path = UPLOAD_DIR / doc["stored_filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server.")
    return FileResponse(
        path=str(file_path),
        filename=doc.get("file_name", doc["stored_filename"]),
        media_type="application/octet-stream",
    )


@router.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str, user: dict = Depends(get_current_user)):
    try:
        doc = collections["documents"].find_one(
            {"_id": ObjectId(doc_id), "user_id": user["_id"]}
        )
    except InvalidId:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if doc.get("stored_filename"):
        fp = UPLOAD_DIR / doc["stored_filename"]
        if fp.exists():
            fp.unlink()
    collections["documents"].delete_one({"_id": ObjectId(doc_id)})
    return {"message": "Document removed."}


# ??? Admin endpoints ??????????????????????????????????????????????????????????

@router.get("/api/admin/documents")
def admin_list_documents(admin: dict = Depends(get_current_admin)):
    """List all user documents with user info. Sorted newest first."""
    docs = list(
        collections["documents"].find().sort("created_at", -1).limit(500)
    )
    user_ids = {d["user_id"] for d in docs if d.get("user_id")}
    users_by_id = {
        u["_id"]: u.get("full_name", "Unknown")
        for u in collections["users"].find({"_id": {"$in": list(user_ids)}}, {"full_name": 1})
    }
    result = []
    for d in docs:
        d["user_name"] = users_by_id.get(d.get("user_id"), "Unknown")
        d["_id"]       = str(d["_id"])
        d["user_id"]   = str(d["user_id"])
        if d.get("stored_filename"):
            d["admin_download_url"] = f"/api/admin/documents/{d['_id']}/download"
        d.pop("stored_filename", None)
        if d.get("verified_at") and hasattr(d["verified_at"], "isoformat"):
            d["verified_at"] = d["verified_at"].isoformat()
        result.append(d)
    return result


@router.put("/api/admin/documents/{doc_id}/verify")
def verify_document(doc_id: str, payload: DocumentVerifyRequest, admin: dict = Depends(get_current_admin)):
    """Update the verification status of a document."""
    allowed = {"Verified", "Rejected", "Pending Review"}
    if payload.verification_status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(allowed)}")
    try:
        result = collections["documents"].update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {
                "verification_status": payload.verification_status,
                "admin_notes":         payload.admin_notes or "",
                "verified_by":         admin.get("full_name", "Admin"),
                "verified_at":         datetime.now(timezone.utc),
            }},
        )
    except InvalidId:
        raise HTTPException(status_code=404, detail="Document not found.")
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Document not found.")
    updated = collections["documents"].find_one({"_id": ObjectId(doc_id)})
    updated["_id"]     = str(updated["_id"])
    updated["user_id"] = str(updated["user_id"])
    updated.pop("stored_filename", None)
    if updated.get("verified_at") and hasattr(updated["verified_at"], "isoformat"):
        updated["verified_at"] = updated["verified_at"].isoformat()
    return updated


@router.get("/api/admin/documents/{doc_id}/download")
def admin_download_document(doc_id: str, admin: dict = Depends(get_current_admin)):
    """Admin: download any user's document."""
    try:
        doc = collections["documents"].find_one({"_id": ObjectId(doc_id)})
    except InvalidId:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if not doc.get("stored_filename"):
        raise HTTPException(status_code=404, detail="No file stored for this document.")
    file_path = UPLOAD_DIR / doc["stored_filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server.")
    return FileResponse(
        path=str(file_path),
        filename=doc.get("file_name", doc["stored_filename"]),
        media_type="application/octet-stream",
    )
