"""AERIS external service stubs.

Each service exposes a tiny, well-typed surface area. The actual API
calls are wrapped behind async functions so they can be swapped with
mocks during tests and so unit tests can monkeypatch the layer.
"""
from app.services.mappls import MapplsClient
from app.services.firebase import FirebaseClient
from app.services.ml_engine import RiskEngine
