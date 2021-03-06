"""Useful functions for the IHC component."""

import asyncio

from openpeerpower.core import callback


async def async_pulse(opp, ihc_controller, ihc_id: int):
    """Send a short on/off pulse to an IHC controller resource."""
    await async_set_bool(opp, ihc_controller, ihc_id, True)
    await asyncio.sleep(0.1)
    await async_set_bool(opp, ihc_controller, ihc_id, False)


@callback
def async_set_bool(opp, ihc_controller, ihc_id: int, value: bool):
    """Set a bool value on an IHC controller resource."""
    return opp.async_add_executor_job(
        ihc_controller.set_runtime_value_bool, ihc_id, value
    )


@callback
def async_set_int(opp, ihc_controller, ihc_id: int, value: int):
    """Set a int value on an IHC controller resource."""
    return opp.async_add_executor_job(
        ihc_controller.set_runtime_value_int, ihc_id, value
    )
