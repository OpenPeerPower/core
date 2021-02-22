"""Alexa related errors."""
from openpeerpower.exceptions import OpenPeerPowerError

from .const import API_TEMP_UNITS


class UnsupportedInterface(OpenPeerPowerError):
    """This entity does not support the requested Smart Home API interface."""


class UnsupportedProperty(OpenPeerPowerError):
    """This entity does not support the requested Smart Home API property."""


class NoTokenAvailable(OpenPeerPowerError):
    """There is no access token available."""


class AlexaError(Exception):
    """Base class for errors that can be serialized for the Alexa API.

    A handler can raise subclasses of this to return an error to the request.
    """

    namespace = None
    error_type = None

    def __init__(self, error_message, payload=None):
        """Initialize an alexa error."""
        Exception.__init__(self)
        self.error_message = error_message
        self.payload = None


class AlexaInvalidEndpointError(AlexaError):
    """The endpoint in the request does not exist."""

    namespace = "Alexa"
    error_type = "NO_SUCH_ENDPOINT"

    def __init__(self, endpoint_id):
        """Initialize invalid endpoint error."""
        msg = f"The endpoint {endpoint_id} does not exist"
        AlexaError.__init__(self, msg)
        self.endpoint_id = endpoint_id


class AlexaInvalidValueError(AlexaError):
    """Class to represent InvalidValue errors."""

    namespace = "Alexa"
    error_type = "INVALID_VALUE"


class AlexaUnsupportedThermostatModeError(AlexaError):
    """Class to represent UnsupportedThermostatMode errors."""

    namespace = "Alexa.ThermostatController"
    error_type = "UNSUPPORTED_THERMOSTAT_MODE"


class AlexaTempRangeError(AlexaError):
    """Class to represent TempRange errors."""

    namespace = "Alexa"
    error_type = "TEMPERATURE_VALUE_OUT_OF_RANGE"

    def __init__(self, opp, temp, min_temp, max_temp):
        """Initialize TempRange error."""
        unit = opp.config.units.temperature_unit
        temp_range = {
            "minimumValue": {"value": min_temp, "scale": API_TEMP_UNITS[unit]},
            "maximumValue": {"value": max_temp, "scale": API_TEMP_UNITS[unit]},
        }
        payload = {"validRange": temp_range}
        msg = f"The requested temperature {temp} is out of range"

        AlexaError.__init__(self, msg, payload)


class AlexaBridgeUnreachableError(AlexaError):
    """Class to represent BridgeUnreachable errors."""

    namespace = "Alexa"
    error_type = "BRIDGE_UNREACHABLE"


class AlexaSecurityPanelUnauthorizedError(AlexaError):
    """Class to represent SecurityPanelController Unauthorized errors."""

    namespace = "Alexa.SecurityPanelController"
    error_type = "UNAUTHORIZED"


class AlexaSecurityPanelAuthorizationRequired(AlexaError):
    """Class to represent SecurityPanelController AuthorizationRequired errors."""

    namespace = "Alexa.SecurityPanelController"
    error_type = "AUTHORIZATION_REQUIRED"


class AlexaAlreadyInOperationError(AlexaError):
    """Class to represent AlreadyInOperation errors."""

    namespace = "Alexa"
    error_type = "ALREADY_IN_OPERATION"


class AlexaInvalidDirectiveError(AlexaError):
    """Class to represent InvalidDirective errors."""

    namespace = "Alexa"
    error_type = "INVALID_DIRECTIVE"


class AlexaVideoActionNotPermittedForContentError(AlexaError):
    """Class to represent action not permitted for content errors."""

    namespace = "Alexa.Video"
    error_type = "ACTION_NOT_PERMITTED_FOR_CONTENT"
