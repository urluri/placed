import hashlib
import json
import os
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel
from PIL import Image

from .algorithm import PLACED_PALETTE, build_decoration_set

router = APIRouter(prefix="/api/labeler", tags=["labeler"])

APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT.parents[1]
LEGACY_DATA_ROOT = APP_ROOT / "data" / "labeler"
DATA_ROOT = Path(os.getenv("PLACED_LABELER_DATA_DIR", PROJECT_ROOT / "runtime" / "labeler"))
IMAGE_ROOT = DATA_ROOT / "images"
DB_PATH = DATA_ROOT / "labeler.db"
LEGACY_DB_PATH = LEGACY_DATA_ROOT / "labeler.db"
DEFAULT_INTERIOR_STYLE = "modern"
DEFAULT_PRINT_PPI = 300


class AnalyzeRequest(BaseModel):
    image_id: str
    artwork_type: str = "poster"
    decor_style: str = "signature"
    width_mm: int | None = None
    height_mm: int | None = None


class AnnotationLabel(BaseModel):
    outer_mat_color_id: str | None = None
    inner_mat_color_id: str | None = None


class AnnotationRequest(BaseModel):
    image_id: str
    artwork_type: str = "poster"
    decor_style: str = "signature"
    width_mm: int | None = None
    height_mm: int | None = None
    label: AnnotationLabel
    confidence: str = "high"
    note: str = ""


def ensure_storage():
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    IMAGE_ROOT.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists() and LEGACY_DB_PATH.exists():
        shutil.copy2(LEGACY_DB_PATH, DB_PATH)
    with connect() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source TEXT NOT NULL,
                source_url TEXT,
                path TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                width_px INTEGER NOT NULL,
                height_px INTEGER NOT NULL,
                width_mm INTEGER NOT NULL,
                height_mm INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS annotations (
                id TEXT PRIMARY KEY,
                image_id TEXT NOT NULL,
                artwork_type TEXT NOT NULL,
                decor_style TEXT NOT NULL,
                width_mm INTEGER NOT NULL,
                height_mm INTEGER NOT NULL,
                context_json TEXT NOT NULL,
                image_features_json TEXT NOT NULL,
                constructive_json TEXT NOT NULL,
                algorithm_suggestion_json TEXT NOT NULL,
                label_json TEXT NOT NULL,
                confidence TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
                UNIQUE (image_id, artwork_type, decor_style, width_mm, height_mm)
            )
            """
        )


def connect():
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def image_size_mm(width_px, height_px, ppi=DEFAULT_PRINT_PPI):
    return (
        max(1, round((width_px / ppi) * 25.4)),
        max(1, round((height_px / ppi) * 25.4)),
    )


def image_extension(name, content_type=None):
    suffix = Path(name or "").suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return suffix
    if content_type == "image/png":
        return ".png"
    if content_type == "image/webp":
        return ".webp"
    return ".jpg"


def store_image(data, name, source, source_url=None, content_type=None):
    ensure_storage()
    digest = hashlib.sha256(data).hexdigest()
    with connect() as db:
        existing = db.execute(
            "SELECT * FROM images WHERE sha256 = ? ORDER BY created_at DESC LIMIT 1",
            (digest,),
        ).fetchone()
    if existing and Path(existing["path"]).exists():
        return row_to_image(existing)

    image_id = str(uuid.uuid4())
    ext = image_extension(name, content_type)
    path = IMAGE_ROOT / f"{image_id}{ext}"
    path.write_bytes(data)

    try:
        with Image.open(path) as img:
            width_px, height_px = img.size
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded file is not a readable image") from exc

    width_mm, height_mm = image_size_mm(width_px, height_px)
    created_at = utc_now()
    with connect() as db:
        db.execute(
            """
            INSERT INTO images (id, name, source, source_url, path, sha256, width_px, height_px, width_mm, height_mm, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                image_id,
                name or f"image{ext}",
                source,
                source_url,
                str(path),
                digest,
                width_px,
                height_px,
                width_mm,
                height_mm,
                created_at,
            ),
        )

    return image_record(image_id)


def row_to_image(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "source": row["source"],
        "source_url": row["source_url"],
        "sha256": row["sha256"],
        "width_px": row["width_px"],
        "height_px": row["height_px"],
        "width_mm": row["width_mm"],
        "height_mm": row["height_mm"],
        "created_at": row["created_at"],
        "image_url": f"/api/labeler/images/{row['id']}/file",
    }


def image_record(image_id):
    with connect() as db:
        row = db.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Image not found")
    return row_to_image(row)


def image_row(image_id):
    with connect() as db:
        row = db.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Image not found")
    return row


def annotation_row_to_dict(row):
    return {
        "id": row["id"],
        "image_id": row["image_id"],
        "artwork_type": row["artwork_type"],
        "decor_style": row["decor_style"],
        "width_mm": row["width_mm"],
        "height_mm": row["height_mm"],
        "context": json.loads(row["context_json"]),
        "image_features": json.loads(row["image_features_json"]),
        "constructive": json.loads(row["constructive_json"]),
        "algorithm_suggestion": json.loads(row["algorithm_suggestion_json"]),
        "label": json.loads(row["label_json"]),
        "confidence": row["confidence"],
        "note": row["note"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def analyze_for_labeler(image_id, artwork_type, decor_style, width_mm=None, height_mm=None):
    row = image_row(image_id)
    width = int(width_mm or row["width_mm"])
    height = int(height_mm or row["height_mm"])
    result = build_decoration_set(
        image_path=row["path"],
        artwork_width_mm=width,
        artwork_height_mm=height,
        artwork_type=artwork_type,
        interior_style=DEFAULT_INTERIOR_STYLE,
    )
    variants = result["variants"]
    variant = next((item for item in variants if item["decor_style"] == decor_style), variants[0])
    mat = variant["mat"]
    context = {
        "artwork_type": variant["artwork_type"],
        "decor_style": variant["decor_style"],
        "width_mm": width,
        "height_mm": height,
        "size_profile": variant["geometry"]["size_profile"],
    }
    constructive = {
        "mat_enabled": mat["enabled"],
        "outer_mat_mm": {
            "left": mat["left_mm"],
            "right": mat["right_mm"],
            "top": mat["top_mm"],
            "bottom": mat["bottom_mm"],
        },
        "inner_reveal_mm": {
            "left": mat["inner_reveal_left_mm"],
            "right": mat["inner_reveal_right_mm"],
            "top": mat["inner_reveal_top_mm"],
            "bottom": mat["inner_reveal_bottom_mm"],
        },
        "overlap_mm": mat["overlap_mm"],
    }
    algorithm_suggestion = {
        "outer_mat_color_id": mat["outer_color"]["id"] if mat["outer_color"] else None,
        "inner_mat_color_id": mat["inner_color"]["id"] if mat["inner_color"] else None,
    }
    return {
        "image": row_to_image(row),
        "context": context,
        "image_analysis": result["image_analysis"],
        "variant": variant,
        "constructive": constructive,
        "algorithm_suggestion": algorithm_suggestion,
    }


@router.get("/palette")
def palette():
    ensure_storage()
    return {"colors": list(PLACED_PALETTE.values())}


@router.get("/images")
def list_images(
    limit: int = Query(150, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    ensure_storage()
    with connect() as db:
        total = db.execute("SELECT COUNT(*) FROM images").fetchone()[0]
        rows = db.execute(
            "SELECT * FROM images ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return {"images": [row_to_image(row) for row in rows], "total": total}


@router.post("/images")
async def upload_images(files: list[UploadFile] = File(...)):
    stored = []
    for file in files:
        data = await file.read()
        stored.append(store_image(data, file.filename, "local", content_type=file.content_type))
    return {"images": stored}


@router.post("/images/from-url")
def upload_image_from_url(url: str = Form(...)):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="URL must start with http or https")

    request = Request(url, headers={"User-Agent": "placed-labeler/0.1"})
    try:
        with urlopen(request, timeout=12) as response:
            content_type = response.headers.get("content-type")
            data = response.read(12 * 1024 * 1024)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not fetch image URL") from exc

    name = Path(parsed.path).name or "remote-image"
    return {"image": store_image(data, name, "url", source_url=url, content_type=content_type)}


@router.get("/images/{image_id}/file")
def image_file(image_id: str):
    row = image_row(image_id)
    path = Path(row["path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")
    return FileResponse(path)


@router.delete("/images/{image_id}")
def delete_image(image_id: str):
    row = image_row(image_id)
    with connect() as db:
        db.execute("DELETE FROM annotations WHERE image_id = ?", (image_id,))
        db.execute("DELETE FROM images WHERE id = ?", (image_id,))
    Path(row["path"]).unlink(missing_ok=True)
    return {"status": "ok"}


@router.post("/analyze")
def analyze(request: AnalyzeRequest):
    return analyze_for_labeler(
        request.image_id,
        request.artwork_type,
        request.decor_style,
        request.width_mm,
        request.height_mm,
    )


@router.get("/annotations")
def list_annotations(
    limit: int = Query(300, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    ensure_storage()
    with connect() as db:
        total = db.execute("SELECT COUNT(*) FROM annotations").fetchone()[0]
        rows = db.execute(
            "SELECT * FROM annotations ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return {"annotations": [annotation_row_to_dict(row) for row in rows], "total": total}


@router.post("/annotations")
def save_annotation(request: AnnotationRequest):
    analysis = analyze_for_labeler(
        request.image_id,
        request.artwork_type,
        request.decor_style,
        request.width_mm,
        request.height_mm,
    )
    context = analysis["context"]
    image_features = analysis["image_analysis"]
    constructive = analysis["constructive"]
    algorithm_suggestion = analysis["algorithm_suggestion"]
    label = request.label.dict()
    now = utc_now()
    annotation_id = str(uuid.uuid4())

    with connect() as db:
        existing = db.execute(
            """
            SELECT id, created_at FROM annotations
            WHERE image_id = ? AND artwork_type = ? AND decor_style = ? AND width_mm = ? AND height_mm = ?
            """,
            (
                request.image_id,
                context["artwork_type"],
                context["decor_style"],
                context["width_mm"],
                context["height_mm"],
            ),
        ).fetchone()
        if existing:
            annotation_id = existing["id"]
            created_at = existing["created_at"]
        else:
            created_at = now

        db.execute(
            """
            INSERT INTO annotations (
                id, image_id, artwork_type, decor_style, width_mm, height_mm,
                context_json, image_features_json, constructive_json, algorithm_suggestion_json,
                label_json, confidence, note, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (image_id, artwork_type, decor_style, width_mm, height_mm)
            DO UPDATE SET
                context_json = excluded.context_json,
                image_features_json = excluded.image_features_json,
                constructive_json = excluded.constructive_json,
                algorithm_suggestion_json = excluded.algorithm_suggestion_json,
                label_json = excluded.label_json,
                confidence = excluded.confidence,
                note = excluded.note,
                updated_at = excluded.updated_at
            """,
            (
                annotation_id,
                request.image_id,
                context["artwork_type"],
                context["decor_style"],
                context["width_mm"],
                context["height_mm"],
                json.dumps(context, ensure_ascii=False),
                json.dumps(image_features, ensure_ascii=False),
                json.dumps(constructive, ensure_ascii=False),
                json.dumps(algorithm_suggestion, ensure_ascii=False),
                json.dumps(label, ensure_ascii=False),
                request.confidence,
                request.note,
                created_at,
                now,
            ),
        )

    with connect() as db:
        row = db.execute("SELECT * FROM annotations WHERE id = ?", (annotation_id,)).fetchone()
    return {"annotation": annotation_row_to_dict(row)}


@router.delete("/annotations/{annotation_id}")
def delete_annotation(annotation_id: str):
    ensure_storage()
    with connect() as db:
        cursor = db.execute("DELETE FROM annotations WHERE id = ?", (annotation_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Annotation not found")
    return {"status": "ok"}


@router.get("/export.jsonl")
def export_jsonl():
    ensure_storage()
    with connect() as db:
        rows = db.execute(
            """
            SELECT annotations.*, images.name, images.source, images.source_url, images.sha256, images.width_px, images.height_px
            FROM annotations
            JOIN images ON images.id = annotations.image_id
            ORDER BY annotations.updated_at DESC
            """
        ).fetchall()

    lines = []
    for row in rows:
        item = annotation_row_to_dict(row)
        item.pop("artwork_type", None)
        if isinstance(item.get("context"), dict):
            item["context"].pop("artwork_type", None)
        item["image"] = {
            "id": row["image_id"],
            "name": row["name"],
            "source": row["source"],
            "source_url": row["source_url"],
            "sha256": row["sha256"],
            "width_px": row["width_px"],
            "height_px": row["height_px"],
        }
        lines.append(json.dumps(item, ensure_ascii=False))

    return PlainTextResponse("\n".join(lines) + ("\n" if lines else ""), media_type="application/x-ndjson")
