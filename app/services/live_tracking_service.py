import json

from redis.asyncio import Redis


class LiveTrackingService:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def publish_location(self, ride_id: str, payload: dict) -> None:
        await self._redis.publish(self._channel(ride_id), json.dumps(payload))
        await self._redis.set(f"ride:{ride_id}:latest_location", json.dumps(payload), ex=3600)

    async def get_latest_location(self, ride_id: str) -> dict | None:
        raw_payload = await self._redis.get(f"ride:{ride_id}:latest_location")
        return json.loads(raw_payload) if raw_payload else None

    @staticmethod
    def _channel(ride_id: str) -> str:
        return f"ride:{ride_id}:tracking"
