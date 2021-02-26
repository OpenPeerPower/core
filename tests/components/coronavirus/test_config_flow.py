"""Test the Coronavirus config flow."""
from openpeerpower import config_entries, setup
from openpeerpower.components.coronavirus.const import DOMAIN, OPTION_WORLDWIDE


async def test_form(opp):
    """Test we get the form."""
    await setup.async_setup_component(opp, "persistent_notification", {})
    result = await opp.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    result2 = await opp.config_entries.flow.async_configure(
        result["flow_id"],
        {"country": OPTION_WORLDWIDE},
    )
    assert result2["type"] == "create_entry"
    assert result2["title"] == "Worldwide"
    assert result2["result"].unique_id == OPTION_WORLDWIDE
    assert result2["data"] == {
        "country": OPTION_WORLDWIDE,
    }
    await opp.async_block_till_done()
    assert len(opp.states.async_all()) == 4
