"""
test_api_v1.py — Tests for the versioned AI Engine endpoints.
"""

from __future__ import annotations

import io
import os
import pytest
from pathlib import Path
from PIL import Image

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def synthetic_image_bytes():
    """Create a valid synthetic 224x224 CT image in memory."""
    img = Image.new('RGB', (224, 224), color='gray')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()

@pytest.fixture
def auth_headers():
    """Return headers with the expected secret."""
    secret = os.environ.get("AI_ENGINE_SECRET", "dummy_secret_for_tests")
    os.environ["AI_ENGINE_SECRET"] = secret
    return {"X-AI-Secret": secret}


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_analyze_no_auth(synthetic_image_bytes):
    """Ensure endpoint rejects requests without the shared secret."""
    # Only enforced if AI_ENGINE_SECRET is set
    os.environ["AI_ENGINE_SECRET"] = "dummy_secret_for_tests"
    
    response = client.post(
        "/api/v1/ai/analyze",
        files={"file": ("test.jpg", synthetic_image_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 401
    assert "Invalid AI Engine secret" in response.json()["detail"]


def test_analyze_invalid_image_type(auth_headers):
    """Ensure endpoint rejects non-images e.g. text/plain."""
    response = client.post(
        "/api/v1/ai/analyze",
        headers=auth_headers,
        files={"file": ("test.txt", b"this is not an image", "text/plain")}
    )
    
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_analyze_corrupt_image_bytes(auth_headers):
    """Ensure endpoint rejects corrupt JPEG bytes."""
    response = client.post(
        "/api/v1/ai/analyze",
        headers=auth_headers,
        files={"file": ("test.jpg", b"corrupt bytes header \x00\xff", "image/jpeg")}
    )
    
    assert response.status_code == 400
    assert "Cannot read image" in response.json()["detail"]


def test_get_file_invalid_inference_id(auth_headers):
    """Ensure endpoint rejects malformed UUIDs."""
    response = client.get(
        "/api/v1/ai/files/not-a-uuid/heatmap.png",
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Invalid inference ID format" in response.json()["detail"]


def test_get_file_path_traversal(auth_headers):
    """Ensure directory traversal is blocked."""
    valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
    response = client.get(
        f"/api/v1/ai/files/{valid_uuid}/..",
        headers=auth_headers
    )
    
    assert response.status_code == 404
