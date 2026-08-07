import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app


@pytest.mark.asyncio
async def test_delete_missing_document_has_explicit_failure_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        response = await client.delete('/documents/999999')

    assert response.status_code == 404
    assert response.json()['detail'] == 'document not found'
