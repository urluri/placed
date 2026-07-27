import io
import json
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .algorithm import build_decoration_set, renderer_geometry
from .renderer.scene import render

DEFAULT_IMAGE = Path(__file__).resolve().parent / "assets" / "default_artwork.jpg"
LOCAL_FRONTEND_ORIGINS = ["http://127.0.0.1:5173", "http://localhost:5173"]

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


@app.api_route("/", methods=["GET", "HEAD"])
@app.api_route("/health", methods=["GET", "HEAD"])
@app.api_route("/api/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok", "service": "placed-api"}


@app.post("/api/recommend")
async def recommend(
    widthMm: int = Form(300),
    heightMm: int = Form(400),
    artworkType: str = Form("poster"),
    interiorStyle: str = Form("minimal"),
    image: UploadFile | None = File(None),
):
    try:
        with await uploaded_or_default_image(image) as image_path:
            result = build_decoration_set(
                image_path=str(image_path),
                artwork_width_mm=widthMm,
                artwork_height_mm=heightMm,
                artwork_type=artworkType,
                interior_style=interiorStyle,
            )
        return JSONResponse(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/render")
async def render_preview(
    widthMm: int = Form(300),
    heightMm: int = Form(400),
    artworkType: str = Form("poster"),
    interiorStyle: str = Form("minimal"),
    decorStyle: str = Form("standard"),
    spec: str | None = Form(None),
    image: UploadFile | None = File(None),
):
    try:
        with await uploaded_or_default_image(image) as image_path:
            if spec:
                variant = json.loads(spec)
            else:
                result = build_decoration_set(
                    image_path=str(image_path),
                    artwork_width_mm=widthMm,
                    artwork_height_mm=heightMm,
                    artwork_type=artworkType,
                    interior_style=interiorStyle,
                )
                variant = find_variant(result["variants"], decorStyle)

            geometry = renderer_geometry(variant)
            with tempfile.TemporaryDirectory() as tmp_dir:
                rendered = render(
                    str(image_path),
                    widthMm,
                    heightMm,
                    geometry,
                    output_path=str(Path(tmp_dir) / "preview.jpg"),
                )

        buffer = io.BytesIO()
        rendered.save(buffer, format="JPEG", quality=92)
        buffer.seek(0)

        headers = {"X-Decor-Style": variant["decor_style"]}
        return StreamingResponse(buffer, media_type="image/jpeg", headers=headers)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def find_variant(variants, decor_style):
    for variant in variants:
        if variant["decor_style"] == decor_style:
            return variant
    return variants[0]


async def uploaded_or_default_image(uploaded: UploadFile | None):
    if not uploaded or not uploaded.filename:
        return LocalImage(DEFAULT_IMAGE)

    data = await uploaded.read()
    return UploadedImage(data)


class LocalImage:
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        return self.path

    def __exit__(self, exc_type, exc, traceback):
        return None


class UploadedImage:
    def __init__(self, data: bytes):
        self.data = data
        self.tmp_dir = None
        self.path = None

    def __enter__(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp_dir.name) / "artwork"
        self.path.write_bytes(self.data)
        return self.path

    def __exit__(self, exc_type, exc, traceback):
        if self.tmp_dir:
            self.tmp_dir.cleanup()
        return None
