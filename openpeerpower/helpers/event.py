"""Helpers for listening to events."""
import asyncio
import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
import functools as ft
import logging
import time
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

import attr

from openpeerpower.const import (
    ATTR_ENTITY_ID,
    ATTR_NOW,
    EVENT_CORE_CONFIG_UPDATE,
    EVENT_STATE_CHANGED,
    EVENT_TIME_CHANGED,
    MATCH_ALL,
    SUN_EVENT_SUNRISE,
    SUN_EVENT_SUNSET,
)
from openpeerpower.core import (
    CALLBACK_TYPE,
    Event,
    OpenPeerPower,
    OppJob,
    State,
    callback,
    split_entity_id,
)
from openpeerpower.exceptions import TemplateError
from openpeerpower.helpers.entity_registry import EVENT_ENTITY_REGISTRY_UPDATED
from openpeerpower.helpers.ratelimit import KeyedRateLimit
from openpeerpower.helpers.sun import get_astral_event_next
from openpeerpower.helpers.template import RenderInfo, Template, result_as_boolean
from openpeerpower.helpers.typing import TemplateVarsType
from openpeerpower.loader import bind_opp
from openpeerpower.util import dt as dt_util
from openpeerpower.util.async_ import run_callback_threadsafe

TRACK_STATE_CHANGE_CALLBACKS = "track_state_change_callbacks"
TRACK_STATE_CHANGE_LISTENER = "track_state_change_listener"

TRACK_STATE_ADDED_DOMAIN_CALLBACKS = "track_state_added_domain_callbacks"
TRACK_STATE_ADDED_DOMAIN_LISTENER = "track_state_added_domain_listener"

TRACK_STATE_REMOVED_DOMAIN_CALLBACKS = "track_state_removed_domain_callbacks"
TRACK_STATE_REMOVED_DOMAIN_LISTENER = "track_state_removed_domain_listener"

TRACK_ENTITY_REGISTRY_UPDATED_CALLBACKS = "track_entity_registry_updated_callbacks"
TRACK_ENTITY_REGISTRY_UPDATED_LISTENER = "track_entity_registry_updated_listener"

_ALL_LISTENER = "all"
_DOMAINS_LISTENER = "domains"
_ENTITIES_LISTENER = "entities"

_LOGGER = logging.getLogger(__name__)


@dataclass
class TrackStates:
    """Class for keeping track of states being tracked.

    all_states: All states on the system are being tracked
    entities: Entities to track
    domains: Domains to track
    """

    all_states: bool
    entities: Set
    domains: Set


@dataclass
class TrackTemplate:
    """Class for keeping track of a template with variables.

    The template is template to calculate.
    The variables are variables to pass to the template.
    The rate_limit is a rate limit on how often the template is re-rendered.
    """

    template: Template
    variables: TemplateVarsType
    rate_limit: Optional[timedelta] = None


@dataclass
class TrackTemplateResult:
    """Class for result of template tracking.

    template
        The template that has changed.
    last_result
        The output from the template on the last successful run, or None
        if no previous successful run.
    result
        Result from the template run. This will be a string or an
        TemplateError if the template resulted in an error.
    """

    template: Template
    last_result: Any
    result: Any


def threaded_listener_factory(
    async_factory: Callable[..., Any]
) -> Callable[..., CALLBACK_TYPE]:
    """Convert an async event helper to a threaded one."""

    @ft.wraps(async_factory)
    def factory(*args: Any, **kwargs: Any) -> CALLBACK_TYPE:
        """Call async event helper safely."""
        opp = args[0]

        if not isinstance(opp, OpenPeerPower):
            raise TypeError("First parameter needs to be a opp instance")

        async_remove = run_callback_threadsafe(
            opp.loop, ft.partial(async_factory, *args, **kwargs)
        ).result()

        def remove() -> None:
            """Threadsafe removal."""
            run_callback_threadsafe(opp.loop, async_remove).result()

        return remove

    return factory


@callback
@bind_opp
def async_track_state_change(
    opp: OpenPeerPower,
    entity_ids: Union[str, Iterable[str]],
    action: Callable[[str, State, State], None],
    from_state: Union[None, str, Iterable[str]] = None,
    to_state: Union[None, str, Iterable[str]] = None,
) -> CALLBACK_TYPE:
    """Track specific state changes.

    entity_ids, from_state and to_state can be string or list.
    Use list to match multiple.

    Returns a function that can be called to remove the listener.

    If entity_ids are not MATCH_ALL along with from_state and to_state
    being None, async_track_state_change_event should be used instead
    as it is slightly faster.

    Must be run within the event loop.
    """
    if from_state is not None:
        match_from_state = process_state_match(from_state)
    if to_state is not None:
        match_to_state = process_state_match(to_state)

    # Ensure it is a lowercase list with entity ids we want to match on
    if entity_ids == MATCH_ALL:
        pass
    elif isinstance(entity_ids, str):
        entity_ids = (entity_ids.lower(),)
    else:
        entity_ids = tuple(entity_id.lower() for entity_id in entity_ids)

    job = OppJob(action)

    @callback
    def state_change_filter(event: Event) -> bool:
        """Handle specific state changes."""
        if from_state is not None:
            old_state = event.data.get("old_state")
            if old_state is not None:
                old_state = old_state.state

            if not match_from_state(old_state):
                return False

        if to_state is not None:
            new_state = event.data.get("new_state")
            if new_state is not None:
                new_state = new_state.state

            if not match_to_state(new_state):
                return False

        return True

    @callback
    def state_change_dispatcher(event: Event) -> None:
        """Handle specific state changes."""
        opp.async_run_opp_job(
            job,
            event.data.get("entity_id"),
            event.data.get("old_state"),
            event.data.get("new_state"),
        )

    @callback
    def state_change_listener(event: Event) -> None:
        """Handle specific state changes."""
        if not state_change_filter(event):
            return

        state_change_dispatcher(event)

    if entity_ids != MATCH_ALL:
        # If we have a list of entity ids we use
        # async_track_state_change_event to route
        # by entity_id to avoid iterating though state change
        # events and creating a jobs where the most
        # common outcome is to return right away because
        # the entity_id does not match since usually
        # only one or two listeners want that specific
        # entity_id.
        return async_track_state_change_event(opp, entity_ids, state_change_listener)

    return opp.bus.async_listen(
        EVENT_STATE_CHANGED, state_change_dispatcher, event_filter=state_change_filter
    )


track_state_change = threaded_listener_factory(async_track_state_change)


@bind_opp
def async_track_state_change_event(
    opp: OpenPeerPower,
    entity_ids: Union[str, Iterable[str]],
    action: Callable[[Event], Any],
) -> Callable[[], None]:
    """Track specific state change events indexed by entity_id.

    Unlike async_track_state_change, async_track_state_change_event
    passes the full event to the callback.

    In order to avoid having to iterate a long list
    of EVENT_STATE_CHANGED and fire and create a job
    for each one, we keep a dict of entity ids that
    care about the state change events so we can
    do a fast dict lookup to route events.
    """
    entity_ids = _async_string_to_lower_list(entity_ids)
    if not entity_ids:
        return _remove_empty_listener

    entity_callbacks = opp.data.setdefault(TRACK_STATE_CHANGE_CALLBACKS, {})

    if TRACK_STATE_CHANGE_LISTENER not in opp.data:

        @callback
        def _async_state_change_filter(event: Event) -> bool:
            """Filter state changes by entity_id."""
            return event.data.get("entity_id") in entity_callbacks

        @callback
        def _async_state_change_dispatcher(event: Event) -> None:
            """Dispatch state changes by entity_id."""
            entity_id = event.data.get("entity_id")

            if entity_id not in entity_callbacks:
                return

            for job in entity_callbacks[entity_id][:]:
                try:
                    opp.async_run_opp_job(job, event)
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception(
                        "Error while processing state change for %s", entity_id
                    )

        opp.data[TRACK_STATE_CHANGE_LISTENER] = opp.bus.async_listen(
            EVENT_STATE_CHANGED,
            _async_state_change_dispatcher,
            event_filter=_async_state_change_filter,
        )

    job = OppJob(action)

    for entity_id in entity_ids:
        entity_callbacks.setdefault(entity_id, []).append(job)

    @callback
    def remove_listener() -> None:
        """Remove state change listener."""
        _async_remove_indexed_listeners(
            opp,
            TRACK_STATE_CHANGE_CALLBACKS,
            TRACK_STATE_CHANGE_LISTENER,
            entity_ids,
            job,
        )

    return remove_listener


@callback
def _remove_empty_listener() -> None:
    """Remove a listener that does nothing."""


@callback
def _async_remove_indexed_listeners(
    opp: OpenPeerPower,
    data_key: str,
    listener_key: str,
    storage_keys: Iterable[str],
    job: OppJob,
) -> None:
    """Remove a listener."""
    callbacks = opp.data[data_key]

    for storage_key in storage_keys:
        callbacks[storage_key].remove(job)
        if len(callbacks[storage_key]) == 0:
            del callbacks[storage_key]

    if not callbacks:
        opp.data[listener_key]()
        del opp.data[listener_key]


@bind_opp
def async_track_entity_registry_updated_event(
    opp: OpenPeerPower,
    entity_ids: Union[str, Iterable[str]],
    action: Callable[[Event], Any],
) -> Callable[[], None]:
    """Track specific entity registry updated events indexed by entity_id.

    Similar to async_track_state_change_event.
    """
    entity_ids = _async_string_to_lower_list(entity_ids)
    if not entity_ids:
        return _remove_empty_listener

    entity_callbacks = opp.data.setdefault(TRACK_ENTITY_REGISTRY_UPDATED_CALLBACKS, {})

    if TRACK_ENTITY_REGISTRY_UPDATED_LISTENER not in opp.data:

        @callback
        def _async_entity_registry_updated_filter(event: Event) -> bool:
            """Filter entity registry updates by entity_id."""
            entity_id = event.data.get("old_entity_id", event.data["entity_id"])
            return entity_id in entity_callbacks

        @callback
        def _async_entity_registry_updated_dispatcher(event: Event) -> None:
            """Dispatch entity registry updates by entity_id."""
            entity_id = event.data.get("old_entity_id", event.data["entity_id"])

            if entity_id not in entity_callbacks:
                return

            for job in entity_callbacks[entity_id][:]:
                try:
                    opp.async_run_opp_job(job, event)
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception(
                        "Error while processing entity registry update for %s",
                        entity_id,
                    )

        opp.data[TRACK_ENTITY_REGISTRY_UPDATED_LISTENER] = opp.bus.async_listen(
            EVENT_ENTITY_REGISTRY_UPDATED,
            _async_entity_registry_updated_dispatcher,
            event_filter=_async_entity_registry_updated_filter,
        )

    job = OppJob(action)

    for entity_id in entity_ids:
        entity_callbacks.setdefault(entity_id, []).append(job)

    @callback
    def remove_listener() -> None:
        """Remove state change listener."""
        _async_remove_indexed_listeners(
            opp,
            TRACK_ENTITY_REGISTRY_UPDATED_CALLBACKS,
            TRACK_ENTITY_REGISTRY_UPDATED_LISTENER,
            entity_ids,
            job,
        )

    return remove_listener


@callback
def _async_dispatch_domain_event(
    opp: OpenPeerPower, event: Event, callbacks: Dict[str, List]
) -> None:
    domain = split_entity_id(event.data["entity_id"])[0]

    if domain not in callbacks and MATCH_ALL not in callbacks:
        return

    listeners = callbacks.get(domain, []) + callbacks.get(MATCH_ALL, [])

    for job in listeners:
        try:
            opp.async_run_opp_job(job, event)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Error while processing event %s for domain %s", event, domain
            )


@bind_opp
def async_track_state_added_domain(
    opp: OpenPeerPower,
    domains: Union[str, Iterable[str]],
    action: Callable[[Event], Any],
) -> Callable[[], None]:
    """Track state change events when an entity is added to domains."""
    domains = _async_string_to_lower_list(domains)
    if not domains:
        return _remove_empty_listener

    domain_callbacks = opp.data.setdefault(TRACK_STATE_ADDED_DOMAIN_CALLBACKS, {})

    if TRACK_STATE_ADDED_DOMAIN_LISTENER not in opp.data:

        @callback
        def _async_state_change_filter(event: Event) -> bool:
            """Filter state changes by entity_id."""
            return event.data.get("old_state") is None

        @callback
        def _async_state_change_dispatcher(event: Event) -> None:
            """Dispatch state changes by entity_id."""
            if event.data.get("old_state") is not None:
                return

            _async_dispatch_domain_event(opp, event, domain_callbacks)

        opp.data[TRACK_STATE_ADDED_DOMAIN_LISTENER] = opp.bus.async_listen(
            EVENT_STATE_CHANGED,
            _async_state_change_dispatcher,
            event_filter=_async_state_change_filter,
        )

    job = OppJob(action)

    for domain in domains:
        domain_callbacks.setdefault(domain, []).append(job)

    @callback
    def remove_listener() -> None:
        """Remove state change listener."""
        _async_remove_indexed_listeners(
            opp,
            TRACK_STATE_ADDED_DOMAIN_CALLBACKS,
            TRACK_STATE_ADDED_DOMAIN_LISTENER,
            domains,
            job,
        )

    return remove_listener


@bind_opp
def async_track_state_removed_domain(
    opp: OpenPeerPower,
    domains: Union[str, Iterable[str]],
    action: Callable[[Event], Any],
) -> Callable[[], None]:
    """Track state change events when an entity is removed from domains."""
    domains = _async_string_to_lower_list(domains)
    if not domains:
        return _remove_empty_listener

    domain_callbacks = opp.data.setdefault(TRACK_STATE_REMOVED_DOMAIN_CALLBACKS, {})

    if TRACK_STATE_REMOVED_DOMAIN_LISTENER not in opp.data:

        @callback
        def _async_state_change_filter(event: Event) -> bool:
            """Filter state changes by entity_id."""
            return event.data.get("new_state") is None

        @callback
        def _async_state_change_dispatcher(event: Event) -> None:
            """Dispatch state changes by entity_id."""
            if event.data.get("new_state") is not None:
                return

            _async_dispatch_domain_event(opp, event, domain_callbacks)

        opp.data[TRACK_STATE_REMOVED_DOMAIN_LISTENER] = opp.bus.async_listen(
            EVENT_STATE_CHANGED,
            _async_state_change_dispatcher,
            event_filter=_async_state_change_filter,
        )

    job = OppJob(action)

    for domain in domains:
        domain_callbacks.setdefault(domain, []).append(job)

    @callback
    def remove_listener() -> None:
        """Remove state change listener."""
        _async_remove_indexed_listeners(
            opp,
            TRACK_STATE_REMOVED_DOMAIN_CALLBACKS,
            TRACK_STATE_REMOVED_DOMAIN_LISTENER,
            domains,
            job,
        )

    return remove_listener


@callback
def _async_string_to_lower_list(instr: Union[str, Iterable[str]]) -> List[str]:
    if isinstance(instr, str):
        return [instr.lower()]

    return [mstr.lower() for mstr in instr]


class _TrackStateChangeFiltered:
    """Handle removal / refresh of tracker."""

    def __init__(
        self,
        opp: OpenPeerPower,
        track_states: TrackStates,
        action: Callable[[Event], Any],
    ):
        """Handle removal / refresh of tracker init."""
        self.opp = opp
        self._action = action
        self._listeners: Dict[str, Callable] = {}
        self._last_track_states: TrackStates = track_states

    @callback
    def async_setup(self) -> None:
        """Create listeners to track states."""
        track_states = self._last_track_states

        if (
            not track_states.all_states
            and not track_states.domains
            and not track_states.entities
        ):
            return

        if track_states.all_states:
            self._setup_all_listener()
            return

        self._setup_domains_listener(track_states.domains)
        self._setup_entities_listener(track_states.domains, track_states.entities)

    @property
    def listeners(self) -> Dict:
        """State changes that will cause a re-render."""
        track_states = self._last_track_states
        return {
            _ALL_LISTENER: track_states.all_states,
            _ENTITIES_LISTENER: track_states.entities,
            _DOMAINS_LISTENER: track_states.domains,
        }

    @callback
    def async_update_listeners(self, new_track_states: TrackStates) -> None:
        """Update the listeners based on the new TrackStates."""
        last_track_states = self._last_track_states
        self._last_track_states = new_track_states

        had_all_listener = last_track_states.all_states

        if new_track_states.all_states:
            if had_all_listener:
                return
            self._cancel_listener(_DOMAINS_LISTENER)
            self._cancel_listener(_ENTITIES_LISTENER)
            self._setup_all_listener()
            return

        if had_all_listener:
            self._cancel_listener(_ALL_LISTENER)

        domains_changed = new_track_states.domains != last_track_states.domains

        if had_all_listener or domains_changed:
            domains_changed = True
            self._cancel_listener(_DOMAINS_LISTENER)
            self._setup_domains_listener(new_track_states.domains)

        if (
            had_all_listener
            or domains_changed
            or new_track_states.entities != last_track_states.entities
        ):
            self._cancel_listener(_ENTITIES_LISTENER)
            self._setup_entities_listener(
                new_track_states.domains, new_track_states.entities
            )

    @callback
    def async_remove(self) -> None:
        """Cancel the listeners."""
        for key in list(self._listeners):
            self._listeners.pop(key)()

    @callback
    def _cancel_listener(self, listener_name: str) -> None:
        if listener_name not in self._listeners:
            return

        self._listeners.pop(listener_name)()

    @callback
    def _setup_entities_listener(self, domains: Set, entities: Set) -> None:
        if domains:
            entities = entities.copy()
            entities.update(self.opp.states.async_entity_ids(domains))

        # Entities has changed to none
        if not entities:
            return

        self._listeners[_ENTITIES_LISTENER] = async_track_state_change_event(
            self.opp, entities, self._action
        )

    @callback
    def _setup_domains_listener(self, domains: Set) -> None:
        if not domains:
            return

        self._listeners[_DOMAINS_LISTENER] = async_track_state_added_domain(
            self.opp, domains, self._action
        )

    @callback
    def _setup_all_listener(self) -> None:
        self._listeners[_ALL_LISTENER] = self.opp.bus.async_listen(
            EVENT_STATE_CHANGED, self._action
        )


@callback
@bind_opp
def async_track_state_change_filtered(
    opp: OpenPeerPower,
    track_states: TrackStates,
    action: Callable[[Event], Any],
) -> _TrackStateChangeFiltered:
    """Track state changes with a TrackStates filter that can be updated.

    Parameters
    ----------
    opp
        Open Peer Power object.
    track_states
        A TrackStates data class.
    action
        Callable to call with results.

    Returns
    -------
    Object used to update the listeners (async_update_listeners) with a new TrackStates or
    cancel the tracking (async_remove).

    """
    tracker = _TrackStateChangeFiltered(opp, track_states, action)
    tracker.async_setup()
    return tracker


@callback
@bind_opp
def async_track_template(
    opp: OpenPeerPower,
    template: Template,
    action: Callable[[str, Optional[State], Optional[State]], None],
    variables: Optional[TemplateVarsType] = None,
) -> Callable[[], None]:
    """Add a listener that fires when a a template evaluates to 'true'.

    Listen for the result of the template becoming true, or a true-like
    string result, such as 'On', 'Open', or 'Yes'. If the template results
    in an error state when the value changes, this will be logged and not
    passed through.

    If the initial check of the template is invalid and results in an
    exception, the listener will still be registered but will only
    fire if the template result becomes true without an exception.

    Action arguments
    ----------------
    entity_id
        ID of the entity that triggered the state change.
    old_state
        The old state of the entity that changed.
    new_state
        New state of the entity that changed.

    Parameters
    ----------
    opp
        Open Peer Power object.
    template
        The template to calculate.
    action
        Callable to call with results. See above for arguments.
    variables
        Variables to pass to the template.

    Returns
    -------
    Callable to unregister the listener.

    """
    job = OppJob(action)

    @callback
    def _template_changed_listener(
        event: Event, updates: List[TrackTemplateResult]
    ) -> None:
        """Check if condition is correct and run action."""
        track_result = updates.pop()

        template = track_result.template
        last_result = track_result.last_result
        result = track_result.result

        if isinstance(result, TemplateError):
            _LOGGER.error(
                "Error while processing template: %s",
                template.template,
                exc_info=result,
            )
            return

        if (
            not isinstance(last_result, TemplateError)
            and result_as_boolean(last_result)
            or not result_as_boolean(result)
        ):
            return

        opp.async_run_opp_job(
            job,
            event and event.data.get("entity_id"),
            event and event.data.get("old_state"),
            event and event.data.get("new_state"),
        )

    info = async_track_template_result(
        opp, [TrackTemplate(template, variables)], _template_changed_listener
    )

    return info.async_remove


track_template = threaded_listener_factory(async_track_template)


class _TrackTemplateResultInfo:
    """Handle removal / refresh of tracker."""

    def __init__(
        self,
        opp: OpenPeerPower,
        track_templates: Iterable[TrackTemplate],
        action: Callable,
    ):
        """Handle removal / refresh of tracker init."""
        self.opp = opp
        self._job = OppJob(action)

        for track_template_ in track_templates:
            track_template_.template.opp = opp
        self._track_templates = track_templates

        self._last_result: Dict[Template, Union[str, TemplateError]] = {}

        self._rate_limit = KeyedRateLimit(opp)
        self._info: Dict[Template, RenderInfo] = {}
        self._track_state_changes: Optional[_TrackStateChangeFiltered] = None
        self._time_listeners: Dict[Template, Callable] = {}

    def async_setup(self, raise_on_template_error: bool) -> None:
        """Activation of template tracking."""
        for track_template_ in self._track_templates:
            template = track_template_.template
            variables = track_template_.variables
            self._info[template] = info = template.async_render_to_info(variables)

            if info.exception:
                if raise_on_template_error:
                    raise info.exception
                _LOGGER.error(
                    "Error while processing template: %s",
                    track_template_.template,
                    exc_info=info.exception,
                )

        self._track_state_changes = async_track_state_change_filtered(
            self.opp, _render_infos_to_track_states(self._info.values()), self._refresh
        )
        self._update_time_listeners()
        _LOGGER.debug(
            "Template group %s listens for %s",
            self._track_templates,
            self.listeners,
        )

    @property
    def listeners(self) -> Dict:
        """State changes that will cause a re-render."""
        assert self._track_state_changes
        return {
            **self._track_state_changes.listeners,
            "time": bool(self._time_listeners),
        }

    @callback
    def _setup_time_listener(self, template: Template, has_time: bool) -> None:
        if not has_time:
            if template in self._time_listeners:
                # now() or utcnow() has left the scope of the template
                self._time_listeners.pop(template)()
            return

        if template in self._time_listeners:
            return

        track_templates = [
            track_template_
            for track_template_ in self._track_templates
            if track_template_.template == template
        ]

        @callback
        def _refresh_from_time(now: datetime) -> None:
            self._refresh(None, track_templates=track_templates)

        self._time_listeners[template] = async_track_utc_time_change(
            self.opp, _refresh_from_time, second=0
        )

    @callback
    def _update_time_listeners(self) -> None:
        for template, info in self._info.items():
            self._setup_time_listener(template, info.has_time)

    @callback
    def async_remove(self) -> None:
        """Cancel the listener."""
        assert self._track_state_changes
        self._track_state_changes.async_remove()
        self._rate_limit.async_remove()
        for template in list(self._time_listeners):
            self._time_listeners.pop(template)()

    @callback
    def async_refresh(self) -> None:
        """Force recalculate the template."""
        self._refresh(None)

    def _render_template_if_ready(
        self,
        track_template_: TrackTemplate,
        now: datetime,
        event: Optional[Event],
    ) -> Union[bool, TrackTemplateResult]:
        """Re-render the template if conditions match.

        Returns False if the template was not be re-rendered

        Returns True if the template re-rendered and did not
        change.

        Returns TrackTemplateResult if the template re-render
        generates a new result.
        """
        template = track_template_.template

        if event:
            info = self._info[template]

            if not _event_triggers_rerender(event, info):
                return False

            had_timer = self._rate_limit.async_has_timer(template)

            if self._rate_limit.async_schedule_action(
                template,
                _rate_limit_for_event(event, info, track_template_),
                now,
                self._refresh,
                event,
                (track_template_,),
                True,
            ):
                return not had_timer

            _LOGGER.debug(
                "Template update %s triggered by event: %s",
                template.template,
                event,
            )

        self._rate_limit.async_triggered(template, now)
        self._info[template] = info = template.async_render_to_info(
            track_template_.variables
        )

        try:
            result: Union[str, TemplateError] = info.result()
        except TemplateError as ex:
            result = ex

        last_result = self._last_result.get(template)

        # Check to see if the result has changed
        if result == last_result:
            return True

        if isinstance(result, TemplateError) and isinstance(last_result, TemplateError):
            return True

        return TrackTemplateResult(template, last_result, result)

    @callback
    def _refresh(
        self,
        event: Optional[Event],
        track_templates: Optional[Iterable[TrackTemplate]] = None,
        replayed: Optional[bool] = False,
    ) -> None:
        """Refresh the template.

        The event is the state_changed event that caused the refresh
        to be considered.

        track_templates is an optional list of TrackTemplate objects
        to refresh.  If not provided, all tracked templates will be
        considered.

        replayed is True if the event is being replayed because the
        rate limit was hit.
        """
        updates = []
        info_changed = False
        now = event.time_fired if not replayed and event else dt_util.utcnow()

        for track_template_ in track_templates or self._track_templates:
            update = self._render_template_if_ready(track_template_, now, event)
            if not update:
                continue

            template = track_template_.template
            self._setup_time_listener(template, self._info[template].has_time)

            info_changed = True

            if isinstance(update, TrackTemplateResult):
                updates.append(update)

        if info_changed:
            assert self._track_state_changes
            self._track_state_changes.async_update_listeners(
                _render_infos_to_track_states(
                    [
                        _suppress_domain_all_in_render_info(self._info[template])
                        if self._rate_limit.async_has_timer(template)
                        else self._info[template]
                        for template in self._info
                    ]
                )
            )
            _LOGGER.debug(
                "Template group %s listens for %s",
                self._track_templates,
                self.listeners,
            )

        if not updates:
            return

        for track_result in updates:
            self._last_result[track_result.template] = track_result.result

        self.opp.async_run_opp_job(self._job, event, updates)


TrackTemplateResultListener = Callable[
    [
        Event,
        List[TrackTemplateResult],
    ],
    None,
]
"""Type for the listener for template results.

    Action arguments
    ----------------
    event
        Event that caused the template to change output. None if not
        triggered by an event.
    updates
        A list of TrackTemplateResult
"""


@callback
@bind_opp
def async_track_template_result(
    opp: OpenPeerPower,
    track_templates: Iterable[TrackTemplate],
    action: TrackTemplateResultListener,
    raise_on_template_error: bool = False,
) -> _TrackTemplateResultInfo:
    """Add a listener that fires when the result of a template changes.

    The action will fire with the initial result from the template, and
    then whenever the output from the template changes. The template will
    be reevaluated if any states referenced in the last run of the
    template change, or if manually triggered. If the result of the
    evaluation is different from the previous run, the listener is passed
    the result.

    If the template results in an TemplateError, this will be returned to
    the listener the first time this happens but not for subsequent errors.
    Once the template returns to a non-error condition the result is sent
    to the action as usual.

    Parameters
    ----------
    opp
        Open Peer Power object.
    track_templates
        An iterable of TrackTemplate.
    action
        Callable to call with results.
    raise_on_template_error
        When set to True, if there is an exception
        processing the template during setup, the system
        will raise the exception instead of setting up
        tracking.

    Returns
    -------
    Info object used to unregister the listener, and refresh the template.

    """
    tracker = _TrackTemplateResultInfo(opp, track_templates, action)
    tracker.async_setup(raise_on_template_error)
    return tracker


@callback
@bind_opp
def async_track_same_state(
    opp: OpenPeerPower,
    period: timedelta,
    action: Callable[..., None],
    async_check_same_func: Callable[[str, Optional[State], Optional[State]], bool],
    entity_ids: Union[str, Iterable[str]] = MATCH_ALL,
) -> CALLBACK_TYPE:
    """Track the state of entities for a period and run an action.

    If async_check_func is None it use the state of orig_value.
    Without entity_ids we track all state changes.
    """
    async_remove_state_for_cancel: Optional[CALLBACK_TYPE] = None
    async_remove_state_for_listener: Optional[CALLBACK_TYPE] = None

    job = OppJob(action)

    @callback
    def clear_listener() -> None:
        """Clear all unsub listener."""
        nonlocal async_remove_state_for_cancel, async_remove_state_for_listener

        if async_remove_state_for_listener is not None:
            async_remove_state_for_listener()
            async_remove_state_for_listener = None
        if async_remove_state_for_cancel is not None:
            async_remove_state_for_cancel()
            async_remove_state_for_cancel = None

    @callback
    def state_for_listener(now: Any) -> None:
        """Fire on state changes after a delay and calls action."""
        nonlocal async_remove_state_for_listener
        async_remove_state_for_listener = None
        clear_listener()
        opp.async_run_opp_job(job)

    @callback
    def state_for_cancel_listener(event: Event) -> None:
        """Fire on changes and cancel for listener if changed."""
        entity: str = event.data["entity_id"]
        from_state: Optional[State] = event.data.get("old_state")
        to_state: Optional[State] = event.data.get("new_state")

        if not async_check_same_func(entity, from_state, to_state):
            clear_listener()

    async_remove_state_for_listener = async_track_point_in_utc_time(
        opp, state_for_listener, dt_util.utcnow() + period
    )

    if entity_ids == MATCH_ALL:
        async_remove_state_for_cancel = opp.bus.async_listen(
            EVENT_STATE_CHANGED, state_for_cancel_listener
        )
    else:
        async_remove_state_for_cancel = async_track_state_change_event(
            opp,
            [entity_ids] if isinstance(entity_ids, str) else entity_ids,
            state_for_cancel_listener,
        )

    return clear_listener


track_same_state = threaded_listener_factory(async_track_same_state)


@callback
@bind_opp
def async_track_point_in_time(
    opp: OpenPeerPower,
    action: Union[OppJob, Callable[..., None]],
    point_in_time: datetime,
) -> CALLBACK_TYPE:
    """Add a listener that fires once after a specific point in time."""
    job = action if isinstance(action, OppJob) else OppJob(action)

    @callback
    def utc_converter(utc_now: datetime) -> None:
        """Convert passed in UTC now to local now."""
        opp.async_run_opp_job(job, dt_util.as_local(utc_now))

    return async_track_point_in_utc_time(opp, utc_converter, point_in_time)


track_point_in_time = threaded_listener_factory(async_track_point_in_time)


@callback
@bind_opp
def async_track_point_in_utc_time(
    opp: OpenPeerPower,
    action: Union[OppJob, Callable[..., None]],
    point_in_time: datetime,
) -> CALLBACK_TYPE:
    """Add a listener that fires once after a specific point in UTC time."""
    # Ensure point_in_time is UTC
    utc_point_in_time = dt_util.as_utc(point_in_time)

    # Since this is called once, we accept a OppJob so we can avoid
    # having to figure out how to call the action every time its called.
    job = action if isinstance(action, OppJob) else OppJob(action)

    cancel_callback: Optional[asyncio.TimerHandle] = None

    @callback
    def run_action() -> None:
        """Call the action."""
        nonlocal cancel_callback

        now = time_tracker_utcnow()

        # Depending on the available clock support (including timer hardware
        # and the OS kernel) it can happen that we fire a little bit too early
        # as measured by utcnow(). That is bad when callbacks have assumptions
        # about the current time. Thus, we rearm the timer for the remaining
        # time.
        delta = (utc_point_in_time - now).total_seconds()
        if delta > 0:
            _LOGGER.debug("Called %f seconds too early, rearming", delta)

            cancel_callback = opp.loop.call_later(delta, run_action)
            return

        opp.async_run_opp_job(job, utc_point_in_time)

    delta = utc_point_in_time.timestamp() - time.time()
    cancel_callback = opp.loop.call_later(delta, run_action)

    @callback
    def unsub_point_in_time_listener() -> None:
        """Cancel the call_later."""
        assert cancel_callback is not None
        cancel_callback.cancel()

    return unsub_point_in_time_listener


track_point_in_utc_time = threaded_listener_factory(async_track_point_in_utc_time)


@callback
@bind_opp
def async_call_later(
    opp: OpenPeerPower, delay: float, action: Union[OppJob, Callable[..., None]]
) -> CALLBACK_TYPE:
    """Add a listener that is called in <delay>."""
    return async_track_point_in_utc_time(
        opp, action, dt_util.utcnow() + timedelta(seconds=delay)
    )


call_later = threaded_listener_factory(async_call_later)


@callback
@bind_opp
def async_track_time_interval(
    opp: OpenPeerPower,
    action: Callable[..., Union[None, Awaitable]],
    interval: timedelta,
) -> CALLBACK_TYPE:
    """Add a listener that fires repetitively at every timedelta interval."""
    remove = None
    interval_listener_job = None

    job = OppJob(action)

    def next_interval() -> datetime:
        """Return the next interval."""
        return dt_util.utcnow() + interval

    @callback
    def interval_listener(now: datetime) -> None:
        """Handle elapsed intervals."""
        nonlocal remove
        nonlocal interval_listener_job

        remove = async_track_point_in_utc_time(
            opp, interval_listener_job, next_interval()  # type: ignore
        )
        opp.async_run_opp_job(job, now)

    interval_listener_job = OppJob(interval_listener)
    remove = async_track_point_in_utc_time(opp, interval_listener_job, next_interval())

    def remove_listener() -> None:
        """Remove interval listener."""
        remove()  # type: ignore

    return remove_listener


track_time_interval = threaded_listener_factory(async_track_time_interval)


@attr.s
class SunListener:
    """Helper class to help listen to sun events."""

    opp: OpenPeerPower = attr.ib()
    job: OppJob = attr.ib()
    event: str = attr.ib()
    offset: Optional[timedelta] = attr.ib()
    _unsub_sun: Optional[CALLBACK_TYPE] = attr.ib(default=None)
    _unsub_config: Optional[CALLBACK_TYPE] = attr.ib(default=None)

    @callback
    def async_attach(self) -> None:
        """Attach a sun listener."""
        assert self._unsub_config is None

        self._unsub_config = self.opp.bus.async_listen(
            EVENT_CORE_CONFIG_UPDATE, self._handle_config_event
        )

        self._listen_next_sun_event()

    @callback
    def async_detach(self) -> None:
        """Detach the sun listener."""
        assert self._unsub_sun is not None
        assert self._unsub_config is not None

        self._unsub_sun()
        self._unsub_sun = None
        self._unsub_config()
        self._unsub_config = None

    @callback
    def _listen_next_sun_event(self) -> None:
        """Set up the sun event listener."""
        assert self._unsub_sun is None

        self._unsub_sun = async_track_point_in_utc_time(
            self.opp,
            self._handle_sun_event,
            get_astral_event_next(self.opp, self.event, offset=self.offset),
        )

    @callback
    def _handle_sun_event(self, _now: Any) -> None:
        """Handle solar event."""
        self._unsub_sun = None
        self._listen_next_sun_event()
        self.opp.async_run_opp_job(self.job)

    @callback
    def _handle_config_event(self, _event: Any) -> None:
        """Handle core config update."""
        assert self._unsub_sun is not None
        self._unsub_sun()
        self._unsub_sun = None
        self._listen_next_sun_event()


@callback
@bind_opp
def async_track_sunrise(
    opp: OpenPeerPower, action: Callable[..., None], offset: Optional[timedelta] = None
) -> CALLBACK_TYPE:
    """Add a listener that will fire a specified offset from sunrise daily."""
    listener = SunListener(opp, OppJob(action), SUN_EVENT_SUNRISE, offset)
    listener.async_attach()
    return listener.async_detach


track_sunrise = threaded_listener_factory(async_track_sunrise)


@callback
@bind_opp
def async_track_sunset(
    opp: OpenPeerPower, action: Callable[..., None], offset: Optional[timedelta] = None
) -> CALLBACK_TYPE:
    """Add a listener that will fire a specified offset from sunset daily."""
    listener = SunListener(opp, OppJob(action), SUN_EVENT_SUNSET, offset)
    listener.async_attach()
    return listener.async_detach


track_sunset = threaded_listener_factory(async_track_sunset)

# For targeted patching in tests
time_tracker_utcnow = dt_util.utcnow


@callback
@bind_opp
def async_track_utc_time_change(
    opp: OpenPeerPower,
    action: Callable[..., None],
    hour: Optional[Any] = None,
    minute: Optional[Any] = None,
    second: Optional[Any] = None,
    local: bool = False,
) -> CALLBACK_TYPE:
    """Add a listener that will fire if time matches a pattern."""
    job = OppJob(action)
    # We do not have to wrap the function with time pattern matching logic
    # if no pattern given
    if all(val is None for val in (hour, minute, second)):

        @callback
        def time_change_listener(event: Event) -> None:
            """Fire every time event that comes in."""
            opp.async_run_opp_job(job, event.data[ATTR_NOW])

        return opp.bus.async_listen(EVENT_TIME_CHANGED, time_change_listener)

    matching_seconds = dt_util.parse_time_expression(second, 0, 59)
    matching_minutes = dt_util.parse_time_expression(minute, 0, 59)
    matching_hours = dt_util.parse_time_expression(hour, 0, 23)

    def calculate_next(now: datetime) -> datetime:
        """Calculate and set the next time the trigger should fire."""
        localized_now = dt_util.as_local(now) if local else now
        return dt_util.find_next_time_expression_time(
            localized_now, matching_seconds, matching_minutes, matching_hours
        )

    time_listener: Optional[CALLBACK_TYPE] = None

    @callback
    def pattern_time_change_listener(_: datetime) -> None:
        """Listen for matching time_changed events."""
        nonlocal time_listener

        now = time_tracker_utcnow()
        opp.async_run_opp_job(job, dt_util.as_local(now) if local else now)

        time_listener = async_track_point_in_utc_time(
            opp,
            pattern_time_change_listener,
            calculate_next(now + timedelta(seconds=1)),
        )

    time_listener = async_track_point_in_utc_time(
        opp, pattern_time_change_listener, calculate_next(dt_util.utcnow())
    )

    @callback
    def unsub_pattern_time_change_listener() -> None:
        """Cancel the time listener."""
        assert time_listener is not None
        time_listener()

    return unsub_pattern_time_change_listener


track_utc_time_change = threaded_listener_factory(async_track_utc_time_change)


@callback
@bind_opp
def async_track_time_change(
    opp: OpenPeerPower,
    action: Callable[..., None],
    hour: Optional[Any] = None,
    minute: Optional[Any] = None,
    second: Optional[Any] = None,
) -> CALLBACK_TYPE:
    """Add a listener that will fire if UTC time matches a pattern."""
    return async_track_utc_time_change(opp, action, hour, minute, second, local=True)


track_time_change = threaded_listener_factory(async_track_time_change)


def process_state_match(
    parameter: Union[None, str, Iterable[str]]
) -> Callable[[str], bool]:
    """Convert parameter to function that matches input against parameter."""
    if parameter is None or parameter == MATCH_ALL:
        return lambda _: True

    if isinstance(parameter, str) or not hasattr(parameter, "__iter__"):
        return lambda state: state == parameter

    parameter_set = set(parameter)
    return lambda state: state in parameter_set


@callback
def _entities_domains_from_render_infos(
    render_infos: Iterable[RenderInfo],
) -> Tuple[Set, Set]:
    """Combine from multiple RenderInfo."""
    entities = set()
    domains = set()

    for render_info in render_infos:
        if render_info.entities:
            entities.update(render_info.entities)
        if render_info.domains:
            domains.update(render_info.domains)
        if render_info.domains_lifecycle:
            domains.update(render_info.domains_lifecycle)
    return entities, domains


@callback
def _render_infos_needs_all_listener(render_infos: Iterable[RenderInfo]) -> bool:
    """Determine if an all listener is needed from RenderInfo."""
    for render_info in render_infos:
        # Tracking all states
        if render_info.all_states or render_info.all_states_lifecycle:
            return True

        # Previous call had an exception
        # so we do not know which states
        # to track
        if render_info.exception:
            return True

    return False


@callback
def _render_infos_to_track_states(render_infos: Iterable[RenderInfo]) -> TrackStates:
    """Create a TrackStates dataclass from the latest RenderInfo."""
    if _render_infos_needs_all_listener(render_infos):
        return TrackStates(True, set(), set())

    return TrackStates(False, *_entities_domains_from_render_infos(render_infos))


@callback
def _event_triggers_rerender(event: Event, info: RenderInfo) -> bool:
    """Determine if a template should be re-rendered from an event."""
    entity_id = event.data.get(ATTR_ENTITY_ID)

    if info.filter(entity_id):
        return True

    if (
        event.data.get("new_state") is not None
        and event.data.get("old_state") is not None
    ):
        return False

    return bool(info.filter_lifecycle(entity_id))


@callback
def _rate_limit_for_event(
    event: Event, info: RenderInfo, track_template_: TrackTemplate
) -> Optional[timedelta]:
    """Determine the rate limit for an event."""
    entity_id = event.data.get(ATTR_ENTITY_ID)

    # Specifically referenced entities are excluded
    # from the rate limit
    if entity_id in info.entities:
        return None

    if track_template_.rate_limit is not None:
        return track_template_.rate_limit

    rate_limit: Optional[timedelta] = info.rate_limit
    return rate_limit


def _suppress_domain_all_in_render_info(render_info: RenderInfo) -> RenderInfo:
    """Remove the domains and all_states from render info during a ratelimit."""
    rate_limited_render_info = copy.copy(render_info)
    rate_limited_render_info.all_states = False
    rate_limited_render_info.all_states_lifecycle = False
    rate_limited_render_info.domains = set()
    rate_limited_render_info.domains_lifecycle = set()
    return rate_limited_render_info
