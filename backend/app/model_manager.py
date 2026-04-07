from __future__ import annotations

import base64
import io
import re
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
        object_query: str = "",
    ) -> PredictionResponse:
        model = self.get_model(model_name)
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(pil_image)
        names = model.names
        requested_labels = self._parse_object_query(object_query)
        selected_class_ids = self._match_class_ids(names, requested_labels)

        results = model.predict(
            source=image_np,
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            classes=selected_class_ids if selected_class_ids else None,
            verbose=False,
        )
        result = results[0]

        detections: list[Detection] = []
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

        if requested_labels and not selected_class_ids:
            encoded = self._encode_image(pil_image)
        else:
            plotted = result.plot()
            plotted_rgb = cv2.cvtColor(plotted, cv2.COLOR_BGR2RGB)
            encoded = self._encode_image(Image.fromarray(plotted_rgb))

        return PredictionResponse(
            model=model_name,
            image_size=[pil_image.width, pil_image.height],
            detections=detections,
            total_detections=len(detections),
            rendered_image=encoded,
            extra={
                "speed_ms": result.speed,
                "available_classes": [names[idx] for idx in sorted(names)],
                "requested_classes": requested_labels,
                "matched_classes": [names[idx] for idx in selected_class_ids],
                "query_applied": bool(requested_labels),
            },
        )

    @staticmethod
    def _parse_object_query(object_query: str) -> list[str]:
        if not object_query.strip():
            return []

        parts = re.split(r"[,;\n]+", object_query)
        return [part.strip() for part in parts if part.strip()]

    @staticmethod
    def _normalize_label(label: str) -> str:
        return re.sub(r"\s+", " ", label.strip().lower())

    def _match_class_ids(self, names: dict[int, str], requested_labels: list[str]) -> list[int]:
        if not requested_labels:
            return []

        normalized_names = {
            class_id: self._normalize_label(class_name)
            for class_id, class_name in names.items()
        }

        matched_ids: list[int] = []
        for requested_label in requested_labels:
            normalized_request = self._normalize_label(requested_label)
            for class_id, normalized_name in normalized_names.items():
                if (
                    normalized_request == normalized_name
                    or normalized_request in normalized_name
                    or normalized_name in normalized_request
                ) and class_id not in matched_ids:
                    matched_ids.append(class_id)
        return matched_ids

    @staticmethod
    def _encode_image(image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


model_manager = ModelManager(settings.models_dir)
