import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


class TestUserAPI:
    @pytest.mark.asyncio
    async def test_get_user_success(self):
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            pass