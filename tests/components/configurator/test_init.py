"""The tests for the Configurator component."""

import openpeerpower.components.configurator as configurator
from openpeerpower.const import ATTR_FRIENDLY_NAME, EVENT_TIME_CHANGED


async def test_request_least_info(opp):
    """Test request config with least amount of data."""
    request_id = configurator.async_request_config(opp, "Test Request", lambda _: None)

    assert (
        len(opp.services.async_services().get(configurator.DOMAIN, [])) == 1
    ), "No new service registered"

    states = opp.states.async_all()

    assert len(states) == 1, "Expected a new state registered"

    state = states[0]

    assert state.state == configurator.STATE_CONFIGURE
    assert state.attributes.get(configurator.ATTR_CONFIGURE_ID) == request_id


async def test_request_all_info(opp):
    """Test request config with all possible info."""
    exp_attr = {
        ATTR_FRIENDLY_NAME: "Test Request",
        configurator.ATTR_DESCRIPTION: """config description

[link name](link url)

![Description image](config image url)""",
        configurator.ATTR_SUBMIT_CAPTION: "config submit caption",
        configurator.ATTR_FIELDS: [],
        configurator.ATTR_ENTITY_PICTURE: "config entity picture",
        configurator.ATTR_CONFIGURE_ID: configurator.async_request_config(
            opp,
            name="Test Request",
            callback=lambda _: None,
            description="config description",
            description_image="config image url",
            submit_caption="config submit caption",
            fields=None,
            link_name="link name",
            link_url="link url",
            entity_picture="config entity picture",
        ),
    }

    states = opp.states.async_all()
    assert len(states) == 1
    state = states[0]

    assert state.state == configurator.STATE_CONFIGURE
    assert state.attributes == exp_attr


async def test_callback_called_on_configure(opp):
    """Test if our callback gets called when configure service called."""
    calls = []
    request_id = configurator.async_request_config(
        opp, "Test Request", lambda _: calls.append(1)
    )

    await opp.services.async_call(
        configurator.DOMAIN,
        configurator.SERVICE_CONFIGURE,
        {configurator.ATTR_CONFIGURE_ID: request_id},
    )

    await opp.async_block_till_done()
    assert len(calls) == 1, "Callback not called"


async def test_state_change_on_notify_errors(opp):
    """Test state change on notify errors."""
    request_id = configurator.async_request_config(opp, "Test Request", lambda _: None)
    error = "Oh no bad bad bad"
    configurator.async_notify_errors(opp, request_id, error)

    states = opp.states.async_all()
    assert len(states) == 1
    state = states[0]
    assert state.attributes.get(configurator.ATTR_ERRORS) == error


async def test_notify_errors_fail_silently_on_bad_request_id(opp):
    """Test if notify errors fails silently with a bad request id."""
    configurator.async_notify_errors(opp, 2015, "Try this error")


async def test_request_done_works(opp):
    """Test if calling request done works."""
    request_id = configurator.async_request_config(opp, "Test Request", lambda _: None)
    configurator.async_request_done(opp, request_id)
    assert len(opp.states.async_all()) == 1

    opp.bus.async_fire(EVENT_TIME_CHANGED)
    await opp.async_block_till_done()
    assert len(opp.states.async_all()) == 0


async def test_request_done_fail_silently_on_bad_request_id(opp):
    """Test that request_done fails silently with a bad request id."""
    configurator.async_request_done(opp, 2016)
