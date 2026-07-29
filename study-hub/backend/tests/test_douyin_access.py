import asyncio
from datetime import datetime, timezone

import pytest

import database
from services.douyin_access import DouyinAccessGate
from services.douyin_resolver import DouyinResolveError


@pytest.fixture(autouse=True)
def clear_access_state():
    conn = database.get_db()
    conn.execute("DELETE FROM automation_runtime_state")
    conn.commit()
    conn.close()


@pytest.mark.asyncio
async def test_access_gate_serializes_operations():
    active = 0
    maximum = 0

    async def operation():
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        await asyncio.sleep(0.01)
        active -= 1
        return "ok"

    gate = DouyinAccessGate(sleep=lambda _seconds: asyncio.sleep(0), cooldown=lambda: 0)
    conn = database.get_db()
    try:
        assert await asyncio.gather(
            gate.run(conn, operation), gate.run(conn, operation)
        ) == ["ok", "ok"]
    finally:
        conn.close()

    assert maximum == 1


@pytest.mark.asyncio
async def test_access_gate_retries_timeout_once():
    attempts = 0

    async def operation():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise DouyinResolveError("network_timeout")
        return "ok"

    gate = DouyinAccessGate(sleep=lambda _seconds: asyncio.sleep(0), cooldown=lambda: 0)
    conn = database.get_db()
    try:
        assert await gate.run(conn, operation) == "ok"
    finally:
        conn.close()
    assert attempts == 2


@pytest.mark.asyncio
async def test_risk_error_opens_persisted_circuit_without_retry():
    attempts = 0

    async def operation():
        nonlocal attempts
        attempts += 1
        raise DouyinResolveError("rate_limited", opens_circuit=True)

    gate = DouyinAccessGate(sleep=lambda _seconds: asyncio.sleep(0), cooldown=lambda: 0)
    conn = database.get_db()
    try:
        with pytest.raises(DouyinResolveError) as first:
            await gate.run(conn, operation)
        assert first.value.code == "rate_limited"
        assert attempts == 1

        with pytest.raises(DouyinResolveError) as second:
            await gate.run(conn, lambda: asyncio.sleep(0))
        assert second.value.code == "rate_limited"
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_daily_quota_blocks_the_next_attempt():
    gate = DouyinAccessGate(
        daily_limit=1,
        sleep=lambda _seconds: asyncio.sleep(0),
        cooldown=lambda: 0,
    )
    conn = database.get_db()
    try:
        assert await gate.run(conn, lambda: asyncio.sleep(0, result="ok")) == "ok"
        with pytest.raises(DouyinResolveError) as limited:
            await gate.run(conn, lambda: asyncio.sleep(0, result="never"))
        assert limited.value.code == "daily_limit_exceeded"
    finally:
        conn.close()
