"""Helpers to check recorder."""


from openpeerpower.core import OpenPeerPower


async def async_migration_in_progress(opp: OpenPeerPower) -> bool:
    """Check to see if a recorder migration is in progress."""
    if "recorder" not in opp.config.components:
        return False
    from openpeerpower.components import (  # pylint: disable=import-outside-toplevel
        recorder,
    )

    return await recorder.async_migration_in_progress(opp)
