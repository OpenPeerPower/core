"""
Support to allow pieces of code to request configuration from the user.

Initiate a request by calling the `request_config` method with a callback.
This will return a request id that has to be used for future calls.
A callback has to be provided to `request_config` which will be called when
the user has submitted configuration information.
"""
import functools as ft

from openpeerpower.const import (
    ATTR_ENTITY_PICTURE,
    ATTR_FRIENDLY_NAME,
    EVENT_TIME_CHANGED,
)
from openpeerpower.core import Event, callback as async_callback
from openpeerpower.helpers.entity import async_generate_entity_id
from openpeerpower.loader import bind_opp
from openpeerpower.util.async_ import run_callback_threadsafe

_KEY_INSTANCE = "configurator"

DATA_REQUESTS = "configurator_requests"

ATTR_CONFIGURE_ID = "configure_id"
ATTR_DESCRIPTION = "description"
ATTR_DESCRIPTION_IMAGE = "description_image"
ATTR_ERRORS = "errors"
ATTR_FIELDS = "fields"
ATTR_LINK_NAME = "link_name"
ATTR_LINK_URL = "link_url"
ATTR_SUBMIT_CAPTION = "submit_caption"

DOMAIN = "configurator"

ENTITY_ID_FORMAT = DOMAIN + ".{}"

SERVICE_CONFIGURE = "configure"
STATE_CONFIGURE = "configure"
STATE_CONFIGURED = "configured"


@bind_opp
@async_callback
def async_request_config(
    opp,
    name,
    callback=None,
    description=None,
    description_image=None,
    submit_caption=None,
    fields=None,
    link_name=None,
    link_url=None,
    entity_picture=None,
):
    """Create a new request for configuration.

    Will return an ID to be used for sequent calls.
    """
    if link_name is not None and link_url is not None:
        description += f"\n\n[{link_name}]({link_url})"

    if description_image is not None:
        description += f"\n\n![Description image]({description_image})"

    instance = opp.data.get(_KEY_INSTANCE)

    if instance is None:
        instance = opp.data[_KEY_INSTANCE] = Configurator(opp)

    request_id = instance.async_request_config(
        name, callback, description, submit_caption, fields, entity_picture
    )

    if DATA_REQUESTS not in opp.data:
        opp.data[DATA_REQUESTS] = {}

    opp.data[DATA_REQUESTS][request_id] = instance

    return request_id


@bind_opp
def request_config(opp, *args, **kwargs):
    """Create a new request for configuration.

    Will return an ID to be used for sequent calls.
    """
    return run_callback_threadsafe(
        opp.loop, ft.partial(async_request_config, opp, *args, **kwargs)
    ).result()


@bind_opp
@async_callback
def async_notify_errors(opp, request_id, error):
    """Add errors to a config request."""
    try:
        opp.data[DATA_REQUESTS][request_id].async_notify_errors(request_id, error)
    except KeyError:
        # If request_id does not exist
        pass


@bind_opp
def notify_errors(opp, request_id, error):
    """Add errors to a config request."""
    return run_callback_threadsafe(
        opp.loop, async_notify_errors, opp, request_id, error
    ).result()


@bind_opp
@async_callback
def async_request_done(opp, request_id):
    """Mark a configuration request as done."""
    try:
        opp.data[DATA_REQUESTS].pop(request_id).async_request_done(request_id)
    except KeyError:
        # If request_id does not exist
        pass


@bind_opp
def request_done(opp, request_id):
    """Mark a configuration request as done."""
    return run_callback_threadsafe(
        opp.loop, async_request_done, opp, request_id
    ).result()


async def async_setup(opp, config):
    """Set up the configurator component."""
    return True


class Configurator:
    """The class to keep track of current configuration requests."""

    def __init__(self, opp):
        """Initialize the configurator."""
        self.opp = opp
        self._cur_id = 0
        self._requests = {}
        opp.services.async_register(
            DOMAIN, SERVICE_CONFIGURE, self.async_handle_service_call
        )

    @async_callback
    def async_request_config(
        self, name, callback, description, submit_caption, fields, entity_picture
    ):
        """Set up a request for configuration."""
        entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, name, opp=self.opp)

        if fields is None:
            fields = []

        request_id = self._generate_unique_id()

        self._requests[request_id] = (entity_id, fields, callback)

        data = {
            ATTR_CONFIGURE_ID: request_id,
            ATTR_FIELDS: fields,
            ATTR_FRIENDLY_NAME: name,
            ATTR_ENTITY_PICTURE: entity_picture,
        }

        data.update(
            {
                key: value
                for key, value in [
                    (ATTR_DESCRIPTION, description),
                    (ATTR_SUBMIT_CAPTION, submit_caption),
                ]
                if value is not None
            }
        )

        self.opp.states.async_set(entity_id, STATE_CONFIGURE, data)

        return request_id

    @async_callback
    def async_notify_errors(self, request_id, error):
        """Update the state with errors."""
        if not self._validate_request_id(request_id):
            return

        entity_id = self._requests[request_id][0]

        state = self.opp.states.get(entity_id)

        new_data = dict(state.attributes)
        new_data[ATTR_ERRORS] = error

        self.opp.states.async_set(entity_id, STATE_CONFIGURE, new_data)

    @async_callback
    def async_request_done(self, request_id):
        """Remove the configuration request."""
        if not self._validate_request_id(request_id):
            return

        entity_id = self._requests.pop(request_id)[0]

        # If we remove the state right away, it will not be included with
        # the result of the service call (current design limitation).
        # Instead, we will set it to configured to give as feedback but delete
        # it shortly after so that it is deleted when the client updates.
        self.opp.states.async_set(entity_id, STATE_CONFIGURED)

        def deferred_remove(event: Event):
            """Remove the request state."""
            self.opp.states.async_remove(entity_id, context=event.context)

        self.opp.bus.async_listen_once(EVENT_TIME_CHANGED, deferred_remove)

    async def async_handle_service_call(self, call):
        """Handle a configure service call."""
        request_id = call.data.get(ATTR_CONFIGURE_ID)

        if not self._validate_request_id(request_id):
            return

        # pylint: disable=unused-variable
        entity_id, fields, callback = self._requests[request_id]

        # field validation goes here?
        if callback:
            await self.opp.async_add_job(callback, call.data.get(ATTR_FIELDS, {}))

    def _generate_unique_id(self):
        """Generate a unique configurator ID."""
        self._cur_id += 1
        return f"{id(self)}-{self._cur_id}"

    def _validate_request_id(self, request_id):
        """Validate that the request belongs to this instance."""
        return request_id in self._requests
