"""Helper to create a unique instance ID."""
from typing import Dict, Optional
import uuid

from openpeerpower.core import OpenPeerPower

from . import singleton, storage

DATA_KEY = "core.uuid"
DATA_VERSION = 1

LEGACY_UUID_FILE = ".uuid"


@singleton.singleton(DATA_KEY)
async def async_get(opp: OpenPeerPower) -> str:
    """Get unique ID for the opp instance."""
    store = storage.Store(opp, DATA_VERSION, DATA_KEY, True)

    data: Optional[Dict[str, str]] = await storage.async_migrator(  # type: ignore
        opp,
        opp.config.path(LEGACY_UUID_FILE),
        store,
    )

    if data is not None:
        return data["uuid"]

    data = {"uuid": uuid.uuid4().hex}

    await store.async_save(data)

    return data["uuid"]
