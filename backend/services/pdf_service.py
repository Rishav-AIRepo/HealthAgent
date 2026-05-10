"""PDF ingestion orchestration: extract → LLM parse → SQLite → FAISS → snapshot."""
import json
from datetime import date
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.agents.doc_agent import extract_parameters
from backend.agents.disease_agent import run_disease_agent
from backend.agents.risk_agent import compute_risk_score
from backend.agents.intake_agent import run_intake_agent
from backend.services.embedding_service import upsert_to_faiss
from backend.db import models
from backend.utils.pdf_parser import combine_pdf_text
from config.settings import get_settings

settings = get_settings()


async def process_pdf(
    file_path: str,
    user_id: str,
    file_id: str,
    db,
) -> dict:
    # 1. Extract text using both parsers
    combined = combine_pdf_text(file_path)

    # 2. LLM extraction of structured parameters
    parameters = await extract_parameters(combined)

    # 3. Persist to SQLite
    new_records = []
    for p in parameters:
        raw_val = p.get("value")
        try:
            value = float(raw_val) if raw_val is not None else 0.0
        except (TypeError, ValueError):
            import re as _re
            m = _re.search(r"[\d.]+", str(raw_val))
            value = float(m.group()) if m else 0.0
        record = models.HealthRecord(
            user_id=user_id,
            file_id=file_id,
            parameter=p.get("test_name", "Unknown"),
            value=value,
            unit=p.get("unit", ""),
            reference_range=p.get("reference_range", ""),
            status=p.get("status", "Unknown"),
        )
        db.add(record)
        new_records.append(record)
    db.commit()

    # 4. Chunk text and embed into FAISS with temporal metadata
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.embedding_chunk_size,
        chunk_overlap=settings.embedding_chunk_overlap,
    )
    chunks = splitter.split_text(combined)
    await upsert_to_faiss(
        user_id=user_id,
        chunks=chunks,
        file_id=file_id,
        upload_date=date.today().isoformat(),
    )

    # 5. Write longitudinal snapshot (F3/F5)
    await _write_snapshot(user_id, file_id, new_records, db)

    return {"count": len(parameters), "chunks": len(chunks)}


async def _write_snapshot(user_id: str, file_id: str, new_records: list, db) -> None:
    try:
        all_records = db.query(models.HealthRecord).filter_by(user_id=user_id).all()
        conditions = run_disease_agent(all_records) if all_records else []
        risk_score, risk_level = compute_risk_score(all_records) if all_records else (0, "Low")

        bmi = None
        user = db.query(models.User).filter_by(user_id=user_id).first()
        if user and user.age and user.height_cm and user.weight_kg:
            intake = run_intake_agent(user.age, user.gender, user.height_cm, user.weight_kg)
            bmi = intake.bmi

        snapshot = models.LongitudinalSnapshot(
            user_id=user_id,
            snapshot_date=date.today(),
            risk_score=risk_score,
            risk_level=risk_level,
            bmi=bmi,
            parameters_json=json.dumps(
                {r.parameter: r.value for r in new_records}
            ),
            conditions_json=json.dumps(conditions),
            file_id=file_id,
        )
        db.add(snapshot)
        db.commit()
    except Exception:
        pass  # snapshot failure must not break the upload response
