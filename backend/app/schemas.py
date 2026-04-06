from typing import Any

from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    name: str
    path: str
    size_mb: float


class Detection(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: list[float]


class PredictionResponse(BaseModel):
    model: str
    image_size: list[int] = Field(description="[width, height]")
    detections: list[Detection]
    total_detections: int
    rendered_image: str = Field(description="Base64-encoded JPEG image with predictions")
    extra: dict[str, Any] = Field(default_factory=dict)
