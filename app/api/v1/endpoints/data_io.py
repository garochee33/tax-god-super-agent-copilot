"""Tax God API - Data Import/Export Endpoints"""

from __future__ import annotations

import io
import zipfile

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.api.deps import CurrentUser, DBSession
from app.services.import_export_service import ENTITY_MAP, export_iif, export_to_csv, import_from_csv

router = APIRouter()

VALID_ENTITIES = list(ENTITY_MAP.keys())


@router.get("/data/export/quickbooks")
async def export_quickbooks(db: DBSession, current_user: CurrentUser):
    """Export data in QuickBooks IIF format."""
    iif_data = await export_iif(db, current_user.id)
    return Response(content=iif_data, media_type="application/octet-stream", headers={"Content-Disposition": "attachment; filename=taxgod_export.iif"})


@router.get("/data/export/all")
async def export_all_zip(db: DBSession, current_user: CurrentUser):
    """Export all entities as a zip of CSVs."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for entity in VALID_ENTITIES:
            csv_data = await export_to_csv(db, current_user.id, entity)
            zf.writestr(f"{entity}.csv", csv_data)
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="application/zip", headers={"Content-Disposition": "attachment; filename=taxgod_export.zip"})


@router.get("/data/export/{entity}")
async def export_entity_csv(entity: str, db: DBSession, current_user: CurrentUser):
    """Export entity data as CSV."""
    if entity not in VALID_ENTITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid entity. Must be one of: {VALID_ENTITIES}")
    csv_data = await export_to_csv(db, current_user.id, entity)
    return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={entity}.csv"})


@router.post("/data/import/{entity}")
async def import_entity_csv(entity: str, file: UploadFile, db: DBSession, current_user: CurrentUser):
    """Import entity data from CSV upload."""
    if entity not in VALID_ENTITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid entity. Must be one of: {VALID_ENTITIES}")
    content = (await file.read()).decode("utf-8")
    result = await import_from_csv(db, current_user.id, entity, content)
    return result
