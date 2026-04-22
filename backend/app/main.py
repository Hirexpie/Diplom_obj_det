from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import settings
from .model_manager import model_manager
from .schemas import ModelInfo, PredictionResponse


app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/models", response_model=list[ModelInfo])
def list_models() -> list[ModelInfo]:
    models = model_manager.list_models()
    if not models:
        raise HTTPException(status_code=404, detail="No .pt models found")
    return models


@app.post("/api/predict", response_model=PredictionResponse)
async def predict(
    model_name: str = Form(...),
    conf: float = Form(0.25),
    iou: float = Form(0.45),
    imgsz: int = Form(960),
    object_query: str = Form(""),
    file: UploadFile = File(...),
) -> PredictionResponse:
    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        media_type = "image"
    elif content_type.startswith("video/"):
        media_type = "video"
    else:
        raise HTTPException(
            status_code=400,
            detail="Only image and video files are supported",
        )

    try:
        contents = await file.read()
        return model_manager.predict(
            model_name=model_name,
            file_bytes=contents,
            media_type=media_type,
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            object_query=object_query,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc


@app.get("/api/stream")
def stream(
    model_name: str,
    source: str = "0",
    conf: float = 0.25,
    iou: float = 0.45,
    imgsz: int = 960,
    object_query: str = "",
    max_fps: float = 12.0,
) -> StreamingResponse:
    try:
        frames = model_manager.stream_mjpeg(
            model_name=model_name,
            source=source,
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            object_query=object_query,
            max_fps=max_fps,
        )
        return StreamingResponse(
            frames,
            media_type="multipart/x-mixed-replace; boundary=frame",
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Stream failed: {exc}") from exc
