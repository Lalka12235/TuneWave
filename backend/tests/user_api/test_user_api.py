import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from tests.user_api.conftest import create_test_user


class TestUserAPI:
    @pytest.mark.asyncio
    async def test_get_user_success(self,create_test_user):
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            user = create_test_user
            user_id = user.id
            response = await ac.get('/users/{user_id}')
            assert response.status_code == 200
            