"""Lovelace dashboard support."""
from abc import ABC, abstractmethod
import logging
import os
from pathlib import Path
import time
from typing import Optional, cast

import voluptuous as vol

from openpeerpower.components.frontend import DATA_PANELS
from openpeerpower.const import CONF_FILENAME
from openpeerpower.core import callback
from openpeerpower.exceptions import OpenPeerPowerError
from openpeerpower.helpers import collection, storage
from openpeerpower.util.yaml import Secrets, load_yaml

from .const import (
    CONF_ICON,
    CONF_URL_PATH,
    DOMAIN,
    EVENT_LOVELACE_UPDATED,
    LOVELACE_CONFIG_FILE,
    MODE_STORAGE,
    MODE_YAML,
    STORAGE_DASHBOARD_CREATE_FIELDS,
    STORAGE_DASHBOARD_UPDATE_FIELDS,
    ConfigNotFound,
)

CONFIG_STORAGE_KEY_DEFAULT = DOMAIN
CONFIG_STORAGE_KEY = "lovelace.{}"
CONFIG_STORAGE_VERSION = 1
DASHBOARDS_STORAGE_KEY = f"{DOMAIN}_dashboards"
DASHBOARDS_STORAGE_VERSION = 1
_LOGGER = logging.getLogger(__name__)


class LovelaceConfig(ABC):
    """Base class for Lovelace config."""

    def __init__(self, opp, url_path, config):
        """Initialize Lovelace config."""
        self.opp = opp
        if config:
            self.config = {**config, CONF_URL_PATH: url_path}
        else:
            self.config = None

    @property
    def url_path(self) -> str:
        """Return url path."""
        return self.config[CONF_URL_PATH] if self.config else None

    @property
    @abstractmethod
    def mode(self) -> str:
        """Return mode of the lovelace config."""

    @abstractmethod
    async def async_get_info(self):
        """Return the config info."""

    @abstractmethod
    async def async_load(self, force):
        """Load config."""

    async def async_save(self, config):
        """Save config."""
        raise OpenPeerPowerError("Not supported")

    async def async_delete(self):
        """Delete config."""
        raise OpenPeerPowerError("Not supported")

    @callback
    def _config_updated(self):
        """Fire config updated event."""
        self.opp.bus.async_fire(EVENT_LOVELACE_UPDATED, {"url_path": self.url_path})


class LovelaceStorage(LovelaceConfig):
    """Class to handle Storage based Lovelace config."""

    def __init__(self, opp, config):
        """Initialize Lovelace config based on storage helper."""
        if config is None:
            url_path = None
            storage_key = CONFIG_STORAGE_KEY_DEFAULT
        else:
            url_path = config[CONF_URL_PATH]
            storage_key = CONFIG_STORAGE_KEY.format(config["id"])

        super().__init__(opp, url_path, config)

        self._store = storage.Store(opp, CONFIG_STORAGE_VERSION, storage_key)
        self._data = None

    @property
    def mode(self) -> str:
        """Return mode of the lovelace config."""
        return MODE_STORAGE

    async def async_get_info(self):
        """Return the Lovelace storage info."""
        if self._data is None:
            await self._load()

        if self._data["config"] is None:
            return {"mode": "auto-gen"}

        return _config_info(self.mode, self._data["config"])

    async def async_load(self, force):
        """Load config."""
        if self.opp.config.safe_mode:
            raise ConfigNotFound

        if self._data is None:
            await self._load()

        config = self._data["config"]

        if config is None:
            raise ConfigNotFound

        return config

    async def async_save(self, config):
        """Save config."""
        if self.opp.config.safe_mode:
            raise OpenPeerPowerError("Saving not supported in safe mode")

        if self._data is None:
            await self._load()
        self._data["config"] = config
        self._config_updated()
        await self._store.async_save(self._data)

    async def async_delete(self):
        """Delete config."""
        if self.opp.config.safe_mode:
            raise OpenPeerPowerError("Deleting not supported in safe mode")

        await self._store.async_remove()
        self._data = None
        self._config_updated()

    async def _load(self):
        """Load the config."""
        data = await self._store.async_load()
        self._data = data if data else {"config": None}


class LovelaceYAML(LovelaceConfig):
    """Class to handle YAML-based Lovelace config."""

    def __init__(self, opp, url_path, config):
        """Initialize the YAML config."""
        super().__init__(opp, url_path, config)

        self.path = opp.config.path(
            config[CONF_FILENAME] if config else LOVELACE_CONFIG_FILE
        )
        self._cache = None

    @property
    def mode(self) -> str:
        """Return mode of the lovelace config."""
        return MODE_YAML

    async def async_get_info(self):
        """Return the YAML storage mode."""
        try:
            config = await self.async_load(False)
        except ConfigNotFound:
            return {
                "mode": self.mode,
                "error": f"{self.path} not found",
            }

        return _config_info(self.mode, config)

    async def async_load(self, force):
        """Load config."""
        is_updated, config = await self.opp.async_add_executor_job(
            self._load_config, force
        )
        if is_updated:
            self._config_updated()
        return config

    def _load_config(self, force):
        """Load the actual config."""
        # Check for a cached version of the config
        if not force and self._cache is not None:
            config, last_update = self._cache
            modtime = os.path.getmtime(self.path)
            if config and last_update > modtime:
                return False, config

        is_updated = self._cache is not None

        try:
            config = load_yaml(self.path, Secrets(Path(self.opp.config.config_dir)))
        except FileNotFoundError:
            raise ConfigNotFound from None

        self._cache = (config, time.time())
        return is_updated, config


def _config_info(mode, config):
    """Generate info about the config."""
    return {
        "mode": mode,
        "views": len(config.get("views", [])),
    }


class DashboardsCollection(collection.StorageCollection):
    """Collection of dashboards."""

    CREATE_SCHEMA = vol.Schema(STORAGE_DASHBOARD_CREATE_FIELDS)
    UPDATE_SCHEMA = vol.Schema(STORAGE_DASHBOARD_UPDATE_FIELDS)

    def __init__(self, opp):
        """Initialize the dashboards collection."""
        super().__init__(
            storage.Store(opp, DASHBOARDS_STORAGE_VERSION, DASHBOARDS_STORAGE_KEY),
            _LOGGER,
        )

    async def _async_load_data(self) -> Optional[dict]:
        """Load the data."""
        data = await self.store.async_load()

        if data is None:
            return cast(Optional[dict], data)

        updated = False

        for item in data["items"] or []:
            if "-" not in item[CONF_URL_PATH]:
                updated = True
                item[CONF_URL_PATH] = f"lovelace-{item[CONF_URL_PATH]}"

        if updated:
            await self.store.async_save(data)

        return cast(Optional[dict], data)

    async def _process_create_data(self, data: dict) -> dict:
        """Validate the config is valid."""
        if "-" not in data[CONF_URL_PATH]:
            raise vol.Invalid("Url path needs to contain a hyphen (-)")

        if data[CONF_URL_PATH] in self.opp.data[DATA_PANELS]:
            raise vol.Invalid("Panel url path needs to be unique")

        return self.CREATE_SCHEMA(data)

    @callback
    def _get_suggested_id(self, info: dict) -> str:
        """Suggest an ID based on the config."""
        return info[CONF_URL_PATH]

    async def _update_data(self, data: dict, update_data: dict) -> dict:
        """Return a new updated data object."""
        update_data = self.UPDATE_SCHEMA(update_data)
        updated = {**data, **update_data}

        if CONF_ICON in updated and updated[CONF_ICON] is None:
            updated.pop(CONF_ICON)

        return updated
