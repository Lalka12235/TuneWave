import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from tests.user_api.conftest import get_user_id


class TestUserAPI:
    @pytest.mark.asyncio
    async def test_get_user_success(self,get_user_id):
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            response = await ac.get('/users/{get_user_id}')
            assert response.status_code == 200
            