import time
from typing import Any, Dict, Optional

class AnalyticsCache:
    _cache: Dict[str, Dict[str, Any]] = {}
    _precomputed: Dict[str, Any] = {
        "admin_vitals": None,
        "faculty_vitals": None,
        "student_vitals": None
    }
    
    @classmethod
    def get_precomputed(cls, key: str) -> Optional[Any]:
        return cls._precomputed.get(key)
    
    @classmethod
    def set_precomputed(cls, key: str, data: Any):
        cls._precomputed[key] = data

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        if key in cls._cache:
            entry = cls._cache[key]
            if time.time() < entry["expires"]:
                return entry["data"]
            else:
                cls._cache.pop(key, None)
        return None

    @classmethod
    def set(cls, key: str, data: Any, ttl: int = 300):
        cls._cache[key] = {
            "data": data,
            "expires": time.time() + ttl
        }

    @classmethod
    def clear(cls):
        cls._cache.clear()
        cls._precomputed = {
            "admin_vitals": None,
            "faculty_vitals": None,
            "student_vitals": None
        }
        print("Analytics cache cleared.")

analytics_cache = AnalyticsCache()
