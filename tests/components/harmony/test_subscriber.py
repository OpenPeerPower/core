"""Test the HarmonySubscriberMixin class."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from openpeerpower.components.harmony.subscriber import (
    HarmonyCallback,
    HarmonySubscriberMixin,
)

_NO_PARAM_CALLBACKS = {
    "connected": "_connected",
    "disconnected": "_disconnected",
    "config_updated": "_config_updated",
}

_ACTIVITY_CALLBACKS = {
    "activity_starting": "_activity_starting",
    "activity_started": "_activity_started",
}

_ALL_CALLBACK_NAMES = list(_NO_PARAM_CALLBACKS.keys()) + list(
    _ACTIVITY_CALLBACKS.keys()
)

_ACTIVITY_TUPLE = ("not", "used")


async def test_no_callbacks.opp):
    """Ensure we handle no subscriptions."""
    subscriber = HarmonySubscriberMixin.opp)
    _call_all_callbacks(subscriber)
    await opp.async_block_till_done()


async def test_empty_callbacks.opp):
    """Ensure we handle a missing callback in a subscription."""
    subscriber = HarmonySubscriberMixin.opp)

    callbacks = {k: None for k in _ALL_CALLBACK_NAMES}
    subscriber.async_subscribe(HarmonyCallback(**callbacks))
    _call_all_callbacks(subscriber)
    await opp.async_block_till_done()


async def test_async_callbacks.opp):
    """Ensure we handle async callbacks."""
    subscriber = HarmonySubscriberMixin.opp)

    callbacks = {k: AsyncMock() for k in _ALL_CALLBACK_NAMES}
    subscriber.async_subscribe(HarmonyCallback(**callbacks))
    _call_all_callbacks(subscriber)
    await opp.async_block_till_done()

    for callback_name in _NO_PARAM_CALLBACKS.keys():
        callback_mock = callbacks[callback_name]
        callback_mock.assert_awaited_once()

    for callback_name in _ACTIVITY_CALLBACKS.keys():
        callback_mock = callbacks[callback_name]
        callback_mock.assert_awaited_once_with(_ACTIVITY_TUPLE)


async def test_long_async_callbacks.opp):
    """Ensure we handle async callbacks that may have sleeps."""
    subscriber = HarmonySubscriberMixin.opp)

    blocker_event = asyncio.Event()
    notifier_event_one = asyncio.Event()
    notifier_event_two = asyncio.Event()

    async def blocks_until_notified():
        await blocker_event.wait()
        notifier_event_one.set()

    async def notifies_when_called():
        notifier_event_two.set()

    callbacks_one = {k: blocks_until_notified for k in _ALL_CALLBACK_NAMES}
    callbacks_two = {k: notifies_when_called for k in _ALL_CALLBACK_NAMES}
    subscriber.async_subscribe(HarmonyCallback(**callbacks_one))
    subscriber.async_subscribe(HarmonyCallback(**callbacks_two))

    subscriber._connected()
    await notifier_event_two.wait()
    blocker_event.set()
    await notifier_event_one.wait()


async def test_callbacks.opp):
    """Ensure we handle non-async callbacks."""
    subscriber = HarmonySubscriberMixin.opp)

    callbacks = {k: MagicMock() for k in _ALL_CALLBACK_NAMES}
    subscriber.async_subscribe(HarmonyCallback(**callbacks))
    _call_all_callbacks(subscriber)
    await opp.async_block_till_done()

    for callback_name in _NO_PARAM_CALLBACKS.keys():
        callback_mock = callbacks[callback_name]
        callback_mock.assert_called_once()

    for callback_name in _ACTIVITY_CALLBACKS.keys():
        callback_mock = callbacks[callback_name]
        callback_mock.assert_called_once_with(_ACTIVITY_TUPLE)


async def test_subscribe_unsubscribe.opp):
    """Ensure we handle subscriptions and unsubscriptions correctly."""
    subscriber = HarmonySubscriberMixin.opp)

    callback_one = {k: MagicMock() for k in _ALL_CALLBACK_NAMES}
    unsub_one = subscriber.async_subscribe(HarmonyCallback(**callback_one))
    callback_two = {k: MagicMock() for k in _ALL_CALLBACK_NAMES}
    _ = subscriber.async_subscribe(HarmonyCallback(**callback_two))
    callback_three = {k: MagicMock() for k in _ALL_CALLBACK_NAMES}
    unsub_three = subscriber.async_subscribe(HarmonyCallback(**callback_three))

    unsub_one()
    unsub_three()

    _call_all_callbacks(subscriber)
    await opp.async_block_till_done()

    for callback_name in _NO_PARAM_CALLBACKS.keys():
        callback_one[callback_name].assert_not_called()
        callback_two[callback_name].assert_called_once()
        callback_three[callback_name].assert_not_called()

    for callback_name in _ACTIVITY_CALLBACKS.keys():
        callback_one[callback_name].assert_not_called()
        callback_two[callback_name].assert_called_once_with(_ACTIVITY_TUPLE)
        callback_three[callback_name].assert_not_called()


def _call_all_callbacks(subscriber):
    for callback_method in _NO_PARAM_CALLBACKS.values():
        to_call = getattr(subscriber, callback_method)
        to_call()

    for callback_method in _ACTIVITY_CALLBACKS.values():
        to_call = getattr(subscriber, callback_method)
        to_call(_ACTIVITY_TUPLE)
