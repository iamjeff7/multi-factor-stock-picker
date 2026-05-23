"""Universe configuration hash helper."""

from __future__ import annotations

import hashlib
import json

from config.models import UniverseSettings
from core.types import ConfigurationHash


def hash_universe_settings(settings: UniverseSettings) -> ConfigurationHash:
    payload = settings.model_dump(mode="json")
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    return ConfigurationHash(digest)
