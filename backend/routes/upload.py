import uuid
import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.services.pdf_service import process_pdf
from backend.models.schemas import UploadResponse
from backend.utils.auth_dep import get_current_user
from backend.utils.plan_guard import check_upload_quota, increment_upload_count
from config.settings import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/{user_id}", response_model=UploadResponse)
async def upload_pdf(
    user_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    check_upload_quota(user_id, db)

    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    if file.size and file.size > 20 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(status_code=413, detail="File too large (max 20 MB)")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(
        settings.pdf_storage_path,
        f"{user_id}_{file_id}.pdf",
    )
    os.makedirs(settings.pdf_storage_path, exist_ok=True)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    result = await process_pdf(file_path, user_id, file_id, db)
    increment_upload_count(user_id, db)

    return UploadResponse(
        message="PDF processed successfully",
        file_id=file_id,
        parameters_extracted=result["count"],
    )
