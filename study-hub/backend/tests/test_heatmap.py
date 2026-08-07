import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import database
from main import app


async def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url='http://test')


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    db_dir = tmp_path / 'data'
    monkeypatch.setattr(database, 'DB_DIR', str(db_dir))
    monkeypatch.setattr(database, 'DB_PATH', str(db_dir / 'study_hub.db'))
    database.init_db()


@pytest.mark.asyncio
async def test_catalog_exposes_field_level_grid_contract():
    async with await client() as http:
        response = await http.get('/heatmap/catalog')

    assert response.status_code == 200
    grid = next(style for style in response.json()['styles'] if style['id'] == 'grid')
    assert grid['settings_schema']['layout']['columns_by_range'] == {'90': 13, '196': 28, '365': 53}
    fields = {field['key']: field for field in grid['settings_schema']['fields']}
    assert fields['cell_gap'] == {'key': 'cell_gap', 'type': 'number', 'min': 0, 'max': 12, 'step': 1, 'default': 5}
    assert fields['cell_radius']['depends_on'] == {'key': 'cell_shape', 'equals': 'rounded'}
    assert {style['id'] for style in response.json()['styles']} == {'grid', 'calendar', 'circular', 'flow'}


@pytest.mark.asyncio
async def test_preferences_normalize_square_radius_and_reject_invalid_contract_values():
    async with await client() as http:
        saved = await http.put('/heatmap/preferences', json={'style_id': 'grid', 'settings': {'cell_shape': 'square', 'cell_radius': 8, 'cell_opacity': 20}})
        reserved = await http.put('/heatmap/preferences', json={'style_id': 'calendar', 'settings': {}})
        unknown = await http.put('/heatmap/preferences', json={'style_id': 'grid', 'settings': {'unknown': True}})
        invalid_step = await http.put('/heatmap/preferences', json={'style_id': 'grid', 'settings': {'cell_opacity': 21}})

    assert saved.status_code == 200
    assert saved.json()['settings']['cell_radius'] == 0
    assert reserved.status_code == unknown.status_code == invalid_step.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize(('range_days', 'columns'), [(90, 13), (196, 28), (365, 53)])
async def test_data_returns_real_cells_and_fixed_grid_dimensions(range_days, columns):
    async with await client() as http:
        response = await http.get('/heatmap/data', params={'range_days': range_days, 'sources': 'documents', 'end_date': '2026-08-03'})

    payload = response.json()
    assert response.status_code == 200
    assert payload['metric'] == 'records'
    assert len(payload['cells']) == range_days
    assert payload['grid']['columns'] == columns
    assert payload['grid']['rows'] == 7
    assert payload['grid']['slot_count'] == columns * 7


@pytest.mark.asyncio
async def test_data_aggregates_the_three_sources_and_excludes_error_queue_records():
    conn = database.get_db()
    try:
        conn.execute("INSERT INTO ddl_tasks (title, created_at, updated_at) VALUES ('task', '2026-08-03 08:00:00', '2026-08-03 10:00:00')")
        conn.execute("INSERT INTO documents (title, content, created_at) VALUES ('doc', 'content', '2026-08-03 09:00:00')")
        conn.execute("INSERT INTO task_queue (task_id, module_id, input_text, status, created_at) VALUES ('queue-ok', 'test', 'input', 'done', '2026-08-03 10:00:00')")
        conn.execute("INSERT INTO task_queue (task_id, module_id, input_text, status, created_at) VALUES ('queue-error', 'test', 'input', 'error', '2026-08-03 10:00:00')")
        conn.commit()
    finally:
        conn.close()

    async with await client() as http:
        response = await http.get('/heatmap/data', params={'range_days': 90, 'sources': 'tasks,documents,queue', 'end_date': '2026-08-03'})

    cell = next(item for item in response.json()['cells'] if item['date'] == '2026-08-03')
    assert cell['count'] == 3
    assert cell['source_counts'] == {'tasks': 1, 'documents': 1, 'queue': 1}


@pytest.mark.asyncio
async def test_queue_is_limited_to_the_latest_200_records_in_the_recent_seven_day_window():
    conn = database.get_db()
    try:
        for index in range(205):
            conn.execute("INSERT INTO task_queue (task_id, module_id, input_text, status, created_at) VALUES (?, 'test', 'input', 'done', '2026-08-03 10:00:00')", (f'queue-{index}',))
        conn.execute("INSERT INTO task_queue (task_id, module_id, input_text, status, created_at) VALUES ('old-queue', 'test', 'input', 'done', '2026-07-26 10:00:00')")
        conn.commit()
    finally:
        conn.close()

    async with await client() as http:
        response = await http.get('/heatmap/data', params={'range_days': 90, 'sources': 'queue', 'end_date': '2026-08-03'})

    payload = response.json()
    assert payload['summary']['total'] == 200
    assert payload['summary']['source_counts'] == {'queue': 200}


@pytest.mark.asyncio
async def test_data_rejects_invalid_queries():
    async with await client() as http:
        bad_range = await http.get('/heatmap/data', params={'range_days': 91})
        bad_source = await http.get('/heatmap/data', params={'sources': 'tasks,tasks'})
        bad_date = await http.get('/heatmap/data', params={'end_date': '03-08-2026'})

    assert bad_range.status_code == bad_source.status_code == bad_date.status_code == 422


def test_init_db_adds_preferences_table_to_an_existing_database():
    conn = database.get_db()
    conn.execute('DROP TABLE heatmap_preferences')
    conn.commit()
    conn.close()

    database.init_db()

    conn = database.get_db()
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()
    assert 'heatmap_preferences' in tables
