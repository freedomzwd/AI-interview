import httpx
import pytest

from app.api.client.v1.auth import _detect_image_extension
from app.core.config import settings
from app.route.route import create_app
from app.services.client.redis_verification import RedisVerificationService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_backoffice_credentials_require_authentication():
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/backoffice/aws/temporary-credentials")

    assert response.status_code == 401


@pytest.mark.unit
def test_uploads_only_mounts_public_avatar_directory():
    app = create_app()
    paths = {route.path for route in app.routes}

    assert "/uploads" not in paths
    assert "/uploads/avatars" in paths


@pytest.mark.unit
def test_avatar_signature_validation_rejects_non_images():
    assert _detect_image_extension(b"<svg onload=alert(1)>") is None
    assert _detect_image_extension(b"\x89PNG\r\n\x1a\nrest") == "png"


@pytest.mark.unit
def test_verification_codes_are_six_digits():
    code = RedisVerificationService.generate_6_digit_code()
    assert code.isdigit()
    assert len(code) == 6


@pytest.mark.unit
@pytest.mark.asyncio
async def test_production_hides_metrics_without_token(monkeypatch):
    monkeypatch.setattr(settings, "ENV", "production")
    monkeypatch.setattr(settings, "METRICS_AUTH_TOKEN", "test-token")
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        hidden = await client.get("/metrics")
        visible = await client.get("/metrics", headers={"X-Metrics-Token": "test-token"})

    assert hidden.status_code == 404
    assert visible.status_code == 200
