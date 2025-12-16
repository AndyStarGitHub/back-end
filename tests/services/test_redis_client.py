import pytest

pytestmark = pytest.mark.anyio


async def test_get_pool_is_cached(monkeypatch):
    import app.services.redis_client as rc

    rc._pool = None

    calls = {"n": 0}

    def fake_from_url(*args, **kwargs):
        calls["n"] += 1
        return object()

    monkeypatch.setattr(
        rc.ConnectionPool,
        "from_url",
        staticmethod(fake_from_url),
        raising=True
    )

    p1 = rc._get_pool()
    p2 = rc._get_pool()

    assert p1 is p2
    assert calls["n"] == 1


async def test_get_redis_uses_pool(monkeypatch):
    import app.services.redis_client as rc

    rc._pool = None

    pool_obj = object()

    def fake_from_url(*args, **kwargs):
        return pool_obj

    class FakeRedis:
        def __init__(self, connection_pool):
            self.connection_pool = connection_pool

    monkeypatch.setattr(
        rc.ConnectionPool,
        "from_url",
        staticmethod(fake_from_url),
        raising=True
    )
    monkeypatch.setattr(rc, "Redis", FakeRedis, raising=True)

    redis = await rc.get_redis()
    assert redis.connection_pool is pool_obj


async def test_close_redis_closes_and_resets(monkeypatch):
    import app.services.redis_client as rc

    class FakeRedis:
        def __init__(self):
            self.closed = False

        async def close(self):
            self.closed = True

    fake = FakeRedis()

    rc._redis = fake

    await rc.close_redis()

    assert fake.closed is True
    assert rc._redis is None
