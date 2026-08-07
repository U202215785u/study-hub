import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app


@pytest.mark.asyncio
async def test_list_categories_returns_seeded_categories_in_display_order():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        response = await client.get('/ddl/categories')

    assert response.status_code == 200
    assert [category['name'] for category in response.json()] == ['待办', '学习任务', '里程碑', '未分类']
