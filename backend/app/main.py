import base64
import binascii
import hashlib
import io
import json
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from openai import OpenAI
from PIL import Image

from .algorithm import build_decoration_set, renderer_geometry
from .labeler import router as labeler_router
from .mat_ml import model_metadata
from .renderer.scene import render

APP_DATA_ROOT = Path(__file__).resolve().parent / "data"
DEFAULT_TEMP_ROOT = Path(tempfile.gettempdir()) / "placed-api"
APP_TEMP_ROOT = Path(os.getenv("PLACED_TEMP_DIR", DEFAULT_TEMP_ROOT))
DEFAULT_IMAGE = Path(__file__).resolve().parent / "assets" / "default_artwork.jpg"
MAX_WORK_IMAGE_SIDE = 1800
IMAGE_CACHE_ROOT = APP_TEMP_ROOT / "uploads"
LOCAL_FRONTEND_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5174",
    "http://localhost:5174",
]
NO_STORE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
}
TIMEWEB_IMAGE_MODEL = os.getenv("TIMEWEB_IMAGE_MODEL", "openai/gpt-image-2")
TIMEWEB_PHOTO_RENDER_QUALITY = os.getenv("TIMEWEB_PHOTO_RENDER_QUALITY", "low")

APP_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
IMAGE_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("TMPDIR", str(APP_TEMP_ROOT))
os.environ.setdefault("TEMP", str(APP_TEMP_ROOT))
os.environ.setdefault("TMP", str(APP_TEMP_ROOT))
tempfile.tempdir = str(APP_TEMP_ROOT)

app = FastAPI(title="Placed API", version="0.1.0")


def allowed_origins():
    cloud_origins = [
        origin.strip()
        for origin in os.getenv("FRONTEND_ORIGIN", "").split(",")
        if origin.strip()
    ]
    return LOCAL_FRONTEND_ORIGINS + cloud_origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Decor-Style"],
)

app.include_router(labeler_router)


@app.api_route("/", methods=["GET", "HEAD"])
@app.api_route("/health", methods=["GET", "HEAD"])
@app.api_route("/api/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok", "service": "placed-api"}


@app.get("/api/ml/status")
def ml_status():
    return JSONResponse(model_metadata(), headers=NO_STORE_HEADERS)


@app.post("/api/recommend")
async def recommend(request: Request):
    try:
        payload = await read_payload(request)
        width_mm = int(payload.get("widthMm", 300))
        height_mm = int(payload.get("heightMm", 400))
        artwork_type = str(payload.get("artworkType", "poster"))
        interior_style = str(payload.get("interiorStyle", "minimal"))
        mat_color_analyzer = str(payload.get("matColorAnalyzer", "rules"))
        mat_size_config = parse_json_field(payload.get("matSizeConfig"))
        image_source = await image_from_payload(payload)

        with image_source as image_path:
            result = build_decoration_set(
                image_path=str(image_path),
                artwork_width_mm=width_mm,
                artwork_height_mm=height_mm,
                artwork_type=artwork_type,
                interior_style=interior_style,
                mat_size_config=mat_size_config,
                mat_color_analyzer=mat_color_analyzer,
            )
        image_token = getattr(image_source, "token", None)
        if image_token:
            result["image_token"] = image_token
        return JSONResponse(result, headers=NO_STORE_HEADERS)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/render")
async def render_preview(request: Request):
    try:
        payload = await read_payload(request)
        width_mm = int(payload.get("widthMm", 300))
        height_mm = int(payload.get("heightMm", 400))
        artwork_type = str(payload.get("artworkType", "poster"))
        interior_style = str(payload.get("interiorStyle", "minimal"))
        decor_style = str(payload.get("decorStyle", "standard"))
        rotate_artwork = parse_bool(payload.get("rotateArtwork", False))
        rotation_degrees = int(payload.get("rotationDegrees", 0))
        crop_artwork_to_format = parse_bool(payload.get("cropArtworkToFormat", False))
        mat_color_analyzer = str(payload.get("matColorAnalyzer", "rules"))
        mat_size_config = parse_json_field(payload.get("matSizeConfig"))
        spec = payload.get("spec")
        image_source = await image_from_payload(payload)

        with image_source as image_path:
            if spec:
                variant = parse_json_field(spec)
            else:
                result = build_decoration_set(
                    image_path=str(image_path),
                    artwork_width_mm=width_mm,
                    artwork_height_mm=height_mm,
                    artwork_type=artwork_type,
                    interior_style=interior_style,
                    mat_size_config=mat_size_config,
                    mat_color_analyzer=mat_color_analyzer,
                )
                variant = find_variant(result["variants"], decor_style)

            geometry = renderer_geometry(variant)
            rendered = render(
                str(image_path),
                width_mm,
                height_mm,
                geometry,
                output_path=None,
                rotation_degrees=normalize_rotation(rotation_degrees, rotate_artwork),
                crop_artwork_to_format=crop_artwork_to_format,
            )

        buffer = io.BytesIO()
        rendered.save(buffer, format="JPEG", quality=92)
        headers = {"X-Decor-Style": variant["decor_style"], **NO_STORE_HEADERS}
        return Response(content=buffer.getvalue(), media_type="image/jpeg", headers=headers)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/photo-render")
async def photo_render(preview: UploadFile = File(...)):
    api_key = os.getenv("TIMEWEB_AI_PROXY_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="TIMEWEB_AI_PROXY_KEY не настроен")

    preview_bytes = await preview.read()
    if not preview_bytes:
        raise HTTPException(status_code=400, detail="Пустое изображение превью")

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.timeweb.ai/v1",
        )
        image_file = io.BytesIO(preview_bytes)
        image_file.name = preview.filename or "placed-preview.jpg"
        response = client.images.edit(
            model=TIMEWEB_IMAGE_MODEL,
            image=image_file,
            prompt=(
                "Use the uploaded image as the exact composition reference. "
                "Preserve the artwork, frame color, mat colors, proportions, crop, and layout. "
                "Do not replace, redraw, restyle, recolor, or reinterpret the artwork. "
                "Only improve photorealism of the physical presentation: realistic mat board paper texture, "
                "subtle material depth, natural frame surface, clean studio product lighting, "
                "and soft believable shadows. The final image must look like a high-quality product photo."
            ),
            size="1024x1024",
            quality=TIMEWEB_PHOTO_RENDER_QUALITY,
        )
        encoded_image = response.data[0].b64_json
        if not encoded_image:
            raise ValueError("AI gateway did not return b64_json")
        rendered_bytes = base64.b64decode(encoded_image)
        return Response(content=rendered_bytes, media_type="image/png", headers=NO_STORE_HEADERS)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Фоторендер не собрался: {exc}") from exc


def find_variant(variants, decor_style):
    for variant in variants:
        if variant["decor_style"] == decor_style:
            return variant
    return variants[0]


def parse_json_field(value: str | None):
    if not value:
        return None
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)


async def read_payload(request: Request):
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("application/json"):
        payload = await request.json()
        return payload if isinstance(payload, dict) else {}
    raw_payload = request.query_params.get("payload")
    if raw_payload:
        payload = json.loads(raw_payload)
        if not isinstance(payload, dict):
            return {}
        body = await request.body()
        if body:
            payload["imageBytes"] = body
        return payload
    form = await request.form()
    return dict(form)


def parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def normalize_rotation(rotation_degrees: int, rotate_artwork: bool):
    if rotation_degrees in (-90, 0, 90):
        return rotation_degrees
    return 90 if rotate_artwork else 0


async def image_from_payload(payload):
    image_bytes = payload.get("imageBytes")
    if isinstance(image_bytes, (bytes, bytearray)):
        return CachedUploadedImage(bytes(image_bytes))

    image_token = payload.get("imageToken")
    if image_token:
        cached_image = cached_image_path(str(image_token))
        if cached_image.exists():
            return LocalImage(cached_image)

    image_data_url = payload.get("imageDataUrl")
    if image_data_url:
        return CachedUploadedImage(decode_data_url(image_data_url))

    uploaded = payload.get("image")
    if isinstance(uploaded, UploadFile) and uploaded.filename:
        data = await uploaded.read()
        return CachedUploadedImage(data)

    if hasattr(uploaded, "read") and getattr(uploaded, "filename", None):
        data = await uploaded.read()
        return CachedUploadedImage(data)

    return LocalImage(DEFAULT_IMAGE)


def decode_data_url(value):
    text = str(value)
    if "," in text and text.startswith("data:"):
        text = text.split(",", 1)[1]
    try:
        return base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid imageDataUrl payload") from exc


class LocalImage:
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        return self.path

    def __exit__(self, exc_type, exc, traceback):
        return None


class CachedUploadedImage:
    def __init__(self, data: bytes):
        self.data = data
        self.path = None
        self.token = hashlib.sha256(data).hexdigest()

    def __enter__(self):
        self.path = cached_image_path(self.token)
        if not self.path.exists():
            self.path.write_bytes(prepare_work_image(self.data))
        return self.path

    def __exit__(self, exc_type, exc, traceback):
        return None


def cached_image_path(token: str):
    safe_token = "".join(char for char in token.lower() if char in "0123456789abcdef")[:64]
    if len(safe_token) != 64:
        raise ValueError("Invalid image token")
    return IMAGE_CACHE_ROOT / f"{safe_token}.jpg"


def prepare_work_image(data: bytes):
    try:
        image = Image.open(io.BytesIO(data)).convert("RGB")
        image.thumbnail((MAX_WORK_IMAGE_SIDE, MAX_WORK_IMAGE_SIDE), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=94, subsampling=0)
        return buffer.getvalue()
    except Exception:
        return data
