"""Scikit-learn based road risk engine (feature #5).

The model is trained on MoRTH historical black-spot data. Until the
trained model is published, this module exposes a deterministic
scoring function so the rest of the pipeline can be exercised end to
end without a placeholder array.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import get_settings

logger = logging.getLogger("aeris.ml")


class RiskEngine:
    def __init__(self) -> None:
        self._model = None
        self._version = "0.0.1"
        self._model_path: Optional[Path] = None

    def load_model(self, path: Path) -> None:
        try:
            import joblib
            self._model = joblib.load(path)
            self._model_path = path
            self._version = "1.0.0-trained"
            logger.info("Risk model loaded from %s", path)
        except Exception as exc:
            logger.error("Could not load risk model: %s", type(exc).__name__)
            self._model = None

    def score_segment(self, features: Dict[str, Any]) -> float:
        """Return a normalised risk score in [0, 1].

        Expected features: accidents_3y, avg_speed_kmh, lane_count,
        shoulder_width_m, sight_distance_m, weather_severity, light_condition.
        """
        if self._model is not None:
            import numpy as np
            X = np.array([[
                features.get("accidents_3y", 0),
                features.get("avg_speed_kmh", 50),
                features.get("lane_count", 2),
                features.get("shoulder_width_m", 1.5),
                features.get("sight_distance_m", 80),
                features.get("weather_severity", 0.3),
                features.get("light_condition", 1),
            ]])
            raw = float(self._model.predict_proba(X)[0][1] if hasattr(self._model, "predict_proba") else self._model.predict(X)[0])
            return max(0.0, min(1.0, raw))

        # Deterministic fallback until a trained model is registered.
        accidents = max(0, features.get("accidents_3y", 0))
        speed_factor = max(0.0, (features.get("avg_speed_kmh", 50) - 40) / 80)
        weather = max(0.0, min(1.0, features.get("weather_severity", 0.3)))
        sight_factor = max(0.0, 1.0 - features.get("sight_distance_m", 80) / 200)

        score = 0.4 * min(1.0, accidents / 10) + 0.25 * speed_factor + 0.2 * weather + 0.15 * sight_factor
        return round(max(0.0, min(1.0, score)), 4)

    def score_route(self, segments: list[Dict[str, Any]]) -> Dict[str, Any]:
        if not segments:
            return {"overall": 0.0, "max_segment": 0.0, "segments": [], "version": self._version}
        scores = []
        for seg in segments:
            scores.append(self.score_segment(seg.get("features", {})))
        return {
            "overall": round(sum(scores) / len(scores), 4),
            "max_segment": max(scores),
            "segments": scores,
            "version": self._version,
        }

    @property
    def version(self) -> str:
        return self._version


risk_engine = RiskEngine()
