from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

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
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    try:
        contents = await file.read()
        return model_manager.predict(
            model_name=model_name,
            image_bytes=contents,
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            object_query=object_query,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc
