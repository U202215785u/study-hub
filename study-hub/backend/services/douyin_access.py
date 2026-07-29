import asyncio
import json
import random
from datetime import datetime, timedelta, timezone

from services.douyin_resolver import DouyinResolveError


class DouyinAccessGate:
    def __init__(self, *, daily_limit=150, sleep=asyncio.sleep, cooldown=None):
        self.daily_limit = daily_limit
        self.sleep = sleep
        self.cooldown = cooldown or (lambda: random.uniform(4, 8))
        self._lock = asyncio.Lock()

    @staticmethod
    def _read_state(conn, name):
        row = conn.execute(
            "SELECT value_json FROM automation_runtime_state WHERE name = ?", (name,)
        ).fetchone()
        return json.loads(row[0]) if row else {}

    @staticmethod
    def _write_state(conn, name, value):
        conn.execute(
            """
            INSERT INTO automation_runtime_state (name, value_json)
            VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET
                value_json = excluded.value_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (name, json.dumps(value, ensure_ascii=False)),
        )
        conn.commit()

    def _check_circuit(self, conn):
        state = self._read_state(conn, "douyin_access_circuit")
        if not state.get("expires_at"):
            return
        try:
            expires = datetime.fromisoformat(state["expires_at"])
        except ValueError:
            return
        if expires > datetime.now(timezone.utc):
            raise DouyinResolveError(
                state.get("error_code") or "risk_verification",
                state.get("message"),
                opens_circuit=True,
            )

    def _consume_quota(self, conn):
        today = datetime.now().astimezone().date().isoformat()
        state = self._read_state(conn, "douyin_daily_quota")
        count = int(state.get("count", 0)) if state.get("day") == today else 0
        if count >= self.daily_limit:
            raise DouyinResolveError("daily_limit_exceeded")
        self._write_state(conn, "douyin_daily_quota", {"day": today, "count": count + 1})

    def _open_circuit(self, conn, error):
        self._write_state(
            conn,
            "douyin_access_circuit",
            {
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
                "error_code": error.code,
                "message": str(error),
            },
        )

    async def run(self, conn, operation):
        async with self._lock:
            self._check_circuit(conn)
            self._consume_quota(conn)
            for attempt in range(2):
                try:
                    result = await operation()
                    await self.sleep(self.cooldown())
                    return result
                except DouyinResolveError as exc:
                    if exc.opens_circuit:
                        self._open_circuit(conn, exc)
                        raise
                    if exc.code not in {
                        "network_timeout", "network_error", "upstream_server_error"
                    } or attempt == 1:
                        raise
                    await self.sleep(random.uniform(15, 30))
