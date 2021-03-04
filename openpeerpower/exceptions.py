"""The exceptions used by Open Peer Power."""
from typing import TYPE_CHECKING, Generator, Optional, Sequence

import attr

if TYPE_CHECKING:
    from .core import Context


class OpenPeerPowerError(Exception):
    """General Open Peer Power exception occurred."""


class InvalidEntityFormatError(OpenPeerPowerError):
    """When an invalid formatted entity is encountered."""


class NoEntitySpecifiedError(OpenPeerPowerError):
    """When no entity is specified."""


class TemplateError(OpenPeerPowerError):
    """Error during template rendering."""

    def __init__(self, exception: Exception) -> None:
        """Init the error."""
        super().__init__(f"{exception.__class__.__name__}: {exception}")


@attr.s
class ConditionError(OpenPeerPowerError):
    """Error during condition evaluation."""

    # The type of the failed condition, such as 'and' or 'numeric_state'
    type: str = attr.ib()

    @staticmethod
    def _indent(indent: int, message: str) -> str:
        """Return indentation."""
        return "  " * indent + message

    def output(self, indent: int) -> Generator:
        """Yield an indented representation."""
        raise NotImplementedError()

    def __str__(self) -> str:
        """Return string representation."""
        return "\n".join(list(self.output(indent=0)))


@attr.s
class ConditionErrorMessage(ConditionError):
    """Condition error message."""

    # A message describing this error
    message: str = attr.ib()

    def output(self, indent: int) -> Generator:
        """Yield an indented representation."""
        yield self._indent(indent, f"In '{self.type}' condition: {self.message}")


@attr.s
class ConditionErrorIndex(ConditionError):
    """Condition error with index."""

    # The zero-based index of the failed condition, for conditions with multiple parts
    index: int = attr.ib()
    # The total number of parts in this condition, including non-failed parts
    total: int = attr.ib()
    # The error that this error wraps
    error: ConditionError = attr.ib()

    def output(self, indent: int) -> Generator:
        """Yield an indented representation."""
        if self.total > 1:
            yield self._indent(
                indent, f"In '{self.type}' (item {self.index+1} of {self.total}):"
            )
        else:
            yield self._indent(indent, f"In '{self.type}':")

        yield from self.error.output(indent + 1)


@attr.s
class ConditionErrorContainer(ConditionError):
    """Condition error with subconditions."""

    # List of ConditionErrors that this error wraps
    errors: Sequence[ConditionError] = attr.ib()

    def output(self, indent: int) -> Generator:
        """Yield an indented representation."""
        for item in self.errors:
            yield from item.output(indent)


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
