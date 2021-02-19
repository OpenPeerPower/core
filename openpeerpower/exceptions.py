"""The exceptions used by Home Assistant."""
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .core import Context  # noqa: F401 pylint: disable=unused-import


class OpenPeerPowerError(Exception):
    """General Home Assistant exception occurred."""


class InvalidEntityFormatError(OpenPeerPowerError):
    """When an invalid formatted entity is encountered."""


class NoEntitySpecifiedError(OpenPeerPowerError):
    """When no entity is specified."""


class TemplateError(OpenPeerPowerError):
    """Error during template rendering."""

    def __init__(self, exception: Exception) -> None:
        """Init the error."""
        super().__init__(f"{exception.__class__.__name__}: {exception}")


class ConditionError(OpenPeerPowerError):
    """Error during condition evaluation."""


class PlatformNotReady(OpenPeerPowerError):
    """Error to indicate that platform is not ready."""


class ConfigEntryNotReady(OpenPeerPowerError):
    """Error to indicate that config entry is not ready."""


class InvalidStateError(OpenPeerPowerError):
    """When an invalid state is encountered."""


class Unauthorized(OpenPeerPowerError):
    """When an action is unauthorized."""

    def __init__(
        self,
        context: Optional["Context"] = None,
        user_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        config_entry_id: Optional[str] = None,
        perm_category: Optional[str] = None,
        permission: Optional[str] = None,
    ) -> None:
        """Unauthorized error."""
        super().__init__(self.__class__.__name__)
        self.context = context

        if user_id is None and context is not None:
            user_id = context.user_id

        self.user_id = user_id
        self.entity_id = entity_id
        self.config_entry_id = config_entry_id
        # Not all actions have an ID (like adding config entry)
        # We then use this fallback to know what category was unauth
        self.perm_category = perm_category
        self.permission = permission


class UnknownUser(Unauthorized):
    """When call is made with user ID that doesn't exist."""


class ServiceNotFound(OpenPeerPowerError):
    """Raised when a service is not found."""

    def __init__(self, domain: str, service: str) -> None:
        """Initialize error."""
        super().__init__(self, f"Service {domain}.{service} not found")
        self.domain = domain
        self.service = service

    def __str__(self) -> str:
        """Return string representation."""
        return f"Unable to find service {self.domain}.{self.service}"
