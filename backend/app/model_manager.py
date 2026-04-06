from __future__ import annotations

import base64
import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

from .config import settings
from .schemas import Detection, ModelInfo, PredictionResponse


class ModelManager:
    def __init__(self, models_dir: Path) -> None:
        self.models_dir = models_dir
        self._cache: dict[str, YOLO] = {}

    def list_models(self) -> list[ModelInfo]:
        if not self.models_dir.exists():
            return []

        models: list[ModelInfo] = []
        for path in sorted(self.models_dir.glob("*.pt")):
            models.append(
                ModelInfo(
                    name=path.name,
                    path=str(path),
                    size_mb=round(path.stat().st_size / (1024 * 1024), 2),
                )
            )
        return models

    def get_model(self, model_name: str) -> YOLO:
        model_path = self.models_dir / model_name
        if not model_path.exists():
            raise FileNotFoundError(f"Model '{model_name}' was not found in {self.models_dir}")

        if model_name not in self._cache:
            self._cache[model_name] = YOLO(str(model_path))
        return self._cache[model_name]

    def predict(
        self,
        model_name: str,
        image_bytes: bytes,
        conf: float,
        iou: float,
        imgsz: int,
    ) -> PredictionResponse:
        model = self.get_model(model_name)
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(pil_image)

        results = model.predict(
            source=image_np,
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            verbose=False,
        )
        result = results[0]

        detections: list[Detection] = []
        names = result.names
        if result.boxes is not None:
            for box in result.boxes:
                cls_id = int(box.cls.item())
                detections.append(
                    Detection(
                        class_id=cls_id,
                        class_name=names.get(cls_id, str(cls_id)),
                        confidence=round(float(box.conf.item()), 4),
                        bbox=[round(float(value), 2) for value in box.xyxy[0].tolist()],
                    )
                )

        plotted = result.plot()
        plotted_rgb = cv2.cvtColor(plotted, cv2.COLOR_BGR2RGB)
        buffer = io.BytesIO()
        Image.fromarray(plotted_rgb).save(buffer, format="JPEG", quality=90)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return PredictionResponse(
            model=model_name,
            image_size=[pil_image.width, pil_image.height],
            detections=detections,
            total_detections=len(detections),
            rendered_image=encoded,
            extra={
                "speed_ms": result.speed,
                "available_classes": [names[idx] for idx in sorted(names)],
            },
        )


model_manager = ModelManager(settings.models_dir)
