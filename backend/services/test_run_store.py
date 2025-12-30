from typing import Dict, Any, List, Optional
import json
import time
from redis import Redis
from config.settings import settings
from utils.logger import logger

_memory_runs: Dict[str, Dict[str, Any]] = {}
_memory_steps: Dict[str, List[Dict[str, Any]]] = {}
_memory_artifacts: Dict[str, List[Dict[str, Any]]] = {}

class TestRunStore:
    def __init__(self):
        self.redis = self._init_redis()
        self.ttl_seconds = settings.TEST_RUN_TTL_SECONDS

    def _init_redis(self) -> Optional[Redis]:
        if not settings.REDIS_URL:
            return None
        try:
            client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            client.ping()
            logger.info("[TestRunStore] Redis enabled")
            return client
        except Exception as e:
            logger.warning(f"[TestRunStore] Redis unavailable, using memory store: {e}")
            return None

    def _run_key(self, run_id: str) -> str:
        return f"test_run:{run_id}"

    def _steps_key(self, run_id: str) -> str:
        return f"test_run:{run_id}:steps"

    def _artifacts_key(self, run_id: str) -> str:
        return f"test_run:{run_id}:artifacts"

    def create_run(self, run_id: str, meta: Dict[str, Any]):
        payload = {
            "status": "queued",
            "started_at": "",
            "ended_at": "",
            **meta,
        }
        if self.redis:
            self.redis.hset(self._run_key(run_id), mapping=payload)
            if self.ttl_seconds > 0:
                self.redis.expire(self._run_key(run_id), self.ttl_seconds)
        else:
            _memory_runs[run_id] = payload

    def update_status(self, run_id: str, status: str, **fields: Any):
        fields = {**fields, "status": status}
        if status == "running" and not fields.get("started_at"):
            fields["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if status in {"passed", "failed", "blocked"} and not fields.get("ended_at"):
            fields["ended_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        fields = {k: "" if v is None else v for k, v in fields.items()}
        if self.redis:
            self.redis.hset(self._run_key(run_id), mapping=fields)
            if self.ttl_seconds > 0:
                self.redis.expire(self._run_key(run_id), self.ttl_seconds)
        else:
            _memory_runs.setdefault(run_id, {}).update(fields)

    def add_step(self, run_id: str, step: Dict[str, Any]):
        if self.redis:
            self.redis.rpush(self._steps_key(run_id), json.dumps(step))
            if self.ttl_seconds > 0:
                self.redis.expire(self._steps_key(run_id), self.ttl_seconds)
        else:
            _memory_steps.setdefault(run_id, []).append(step)

    def add_artifact(self, run_id: str, artifact: Dict[str, Any]):
        if self.redis:
            self.redis.rpush(self._artifacts_key(run_id), json.dumps(artifact))
            if self.ttl_seconds > 0:
                self.redis.expire(self._artifacts_key(run_id), self.ttl_seconds)
        else:
            _memory_artifacts.setdefault(run_id, []).append(artifact)

    def cache_catalog(self, doc_id: str, catalog: Dict[str, Any]):
        key = f"test_catalog:{doc_id}"
        if self.redis:
            self.redis.set(key, json.dumps(catalog))
            if self.ttl_seconds > 0:
                self.redis.expire(key, self.ttl_seconds)
        else:
            _memory_runs[key] = catalog

    def get_cached_catalog(self, doc_id: str) -> Optional[Dict[str, Any]]:
        key = f"test_catalog:{doc_id}"
        if self.redis:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        return _memory_runs.get(key)  # type: ignore[return-value]

    def get_run(self, run_id: str) -> Dict[str, Any]:
        if self.redis:
            run = self.redis.hgetall(self._run_key(run_id))
            steps = [json.loads(s) for s in self.redis.lrange(self._steps_key(run_id), 0, -1)]
            artifacts = [json.loads(a) for a in self.redis.lrange(self._artifacts_key(run_id), 0, -1)]
            return {"run": run, "steps": steps, "artifacts": artifacts}

        return {
            "run": _memory_runs.get(run_id, {}),
            "steps": _memory_steps.get(run_id, []),
            "artifacts": _memory_artifacts.get(run_id, []),
        }

test_run_store = TestRunStore()
