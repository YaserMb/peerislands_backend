from collections.abc import Iterator
from contextlib import contextmanager
from uuid import uuid4

from redis import Redis


@contextmanager
def redis_distributed_lock(
    *,
    redis_url: str,
    key: str,
    ttl_seconds: int,
) -> Iterator[bool]:
    token = uuid4().hex
    client = Redis.from_url(redis_url)
    acquired = bool(client.set(key, token, nx=True, ex=ttl_seconds))

    try:
        yield acquired
    finally:
        if acquired:
            _release_lock(client, key=key, token=token)


def _release_lock(client: Redis, *, key: str, token: str) -> None:
    script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    end
    return 0
    """
    client.eval(script, 1, key, token)
