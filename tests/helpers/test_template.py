"""Test Open Peer Power template helper methods."""
from datetime import datetime
import math
import random
from unittest.mock import patch

import pytest
import pytz
import voluptuous as vol

from openpeerpower.components import group
from openpeerpower.config import async_process_op_core_config
from openpeerpower.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    LENGTH_METERS,
    MASS_GRAMS,
    PRESSURE_PA,
    TEMP_CELSIUS,
    VOLUME_LITERS,
)
from openpeerpower.exceptions import TemplateError
from openpeerpower.helpers import template
from openpeerpower.setup import async_setup_component
import openpeerpower.util.dt as dt_util
from openpeerpower.util.unit_system import UnitSystem

from tests.common import MockConfigEntry, mock_device_registry, mock_registry


def _set_up_units(opp):
    """Set up the tests."""
    opp.config.units = UnitSystem(
        "custom", TEMP_CELSIUS, LENGTH_METERS, VOLUME_LITERS, MASS_GRAMS, PRESSURE_PA
    )


def render_to_info(opp, template_str, variables=None):
    """Create render info from template."""
    tmp = template.Template(template_str, opp)
    return tmp.async_render_to_info(variables)


def extract_entities(opp, template_str, variables=None):
    """Extract entities from a template."""
    info = render_to_info(opp, template_str, variables)
    return info.entities


def assert_result_info(info, result, entities=None, domains=None, all_states=False):
    """Check result info."""
    assert info.result() == result
    assert info.all_states == all_states
    assert info.filter("invalid_entity_name.somewhere") == all_states
    if entities is not None:
        assert info.entities == frozenset(entities)
        assert all([info.filter(entity) for entity in entities])
        if not all_states:
            assert not info.filter("invalid_entity_name.somewhere")
    else:
        assert not info.entities
    if domains is not None:
        assert info.domains == frozenset(domains)
        assert all([info.filter(domain + ".entity") for domain in domains])
    else:
        assert not hasattr(info, "_domains")


def test_template_equality():
    """Test template comparison and hashing."""
    template_one = template.Template("{{ template_one }}")
    template_one_1 = template.Template("{{ template_one }}")
    template_two = template.Template("{{ template_two }}")

    assert template_one == template_one_1
    assert template_one != template_two
    assert hash(template_one) == hash(template_one_1)
    assert hash(template_one) != hash(template_two)

    assert str(template_one_1) == 'Template("{{ template_one }}")'

    with pytest.raises(TypeError):
        template.Template(["{{ template_one }}"])


def test_invalid_template(opp):
    """Invalid template raises error."""
    tmpl = template.Template("{{", opp)

    with pytest.raises(TemplateError):
        tmpl.ensure_valid()

    with pytest.raises(TemplateError):
        tmpl.async_render()

    info = tmpl.async_render_to_info()
    with pytest.raises(TemplateError):
        assert info.result() == "impossible"

    tmpl = template.Template("{{states(keyword)}}", opp)

    tmpl.ensure_valid()

    with pytest.raises(TemplateError):
        tmpl.async_render()


def test_referring_states_by_entity_id(opp):
    """Test referring states by entity id."""
    opp.states.async_set("test.object", "happy")
    assert (
        template.Template("{{ states.test.object.state }}", opp).async_render()
        == "happy"
    )

    assert (
        template.Template('{{ states["test.object"].state }}', opp).async_render()
        == "happy"
    )

    assert (
        template.Template('{{ states("test.object") }}', opp).async_render() == "happy"
    )


def test_invalid_entity_id(opp):
    """Test referring states by entity id."""
    with pytest.raises(TemplateError):
        template.Template('{{ states["big.fat..."] }}', opp).async_render()
    with pytest.raises(TemplateError):
        template.Template('{{ states.test["big.fat..."] }}', opp).async_render()
    with pytest.raises(TemplateError):
        template.Template('{{ states["invalid/domain"] }}', opp).async_render()


def test_raise_exception_on_error(opp):
    """Test raising an exception on error."""
    with pytest.raises(TemplateError):
        template.Template("{{ invalid_syntax").ensure_valid()


def test_iterating_all_states(opp):
    """Test iterating all states."""
    tmpl_str = "{% for state in states %}{{ state.state }}{% endfor %}"

    info = render_to_info(opp, tmpl_str)
    assert_result_info(info, "", all_states=True)
    assert info.rate_limit == template.ALL_STATES_RATE_LIMIT

    opp.states.async_set("test.object", "happy")
    opp.states.async_set("sensor.temperature", 10)

    info = render_to_info(opp, tmpl_str)
    assert_result_info(info, "10happy", entities=[], all_states=True)


def test_iterating_all_states_unavailable(opp):
    """Test iterating all states unavailable."""
    opp.states.async_set("test.object", "on")

    tmpl_str = "{{ states | selectattr('state', 'in', ['unavailable', 'unknown', 'none']) | list | count }}"

    info = render_to_info(opp, tmpl_str)

    assert info.all_states is True
    assert info.rate_limit == template.ALL_STATES_RATE_LIMIT

    opp.states.async_set("test.object", "unknown")
    opp.states.async_set("sensor.temperature", 10)

    info = render_to_info(opp, tmpl_str)
    assert_result_info(info, 1, entities=[], all_states=True)


def test_iterating_domain_states(opp):
    """Test iterating domain states."""
    tmpl_str = "{% for state in states.sensor %}{{ state.state }}{% endfor %}"

    info = render_to_info(opp, tmpl_str)
    assert_result_info(info, "", domains=["sensor"])
    assert info.rate_limit == template.DOMAIN_STATES_RATE_LIMIT

    opp.states.async_set("test.object", "happy")
    opp.states.async_set("sensor.back_door", "open")
    opp.states.async_set("sensor.temperature", 10)

    info = render_to_info(opp, tmpl_str)
    assert_result_info(
        info,
        "open10",
        entities=[],
        domains=["sensor"],
    )


def test_float(opp):
    """Test float."""
    opp.states.async_set("sensor.temperature", "12")

    assert (
        template.Template(
            "{{ float(states.sensor.temperature.state) }}", opp
        ).async_render()
        == 12.0
    )

    assert (
        template.Template(
            "{{ float(states.sensor.temperature.state) > 11 }}", opp
        ).async_render()
        is True
    )

    assert (
        template.Template("{{ float('forgiving') }}", opp).async_render() == "forgiving"
    )


def test_rounding_value(opp):
    """Test rounding value."""
    opp.states.async_set("sensor.temperature", 12.78)

    assert (
        template.Template(
            "{{ states.sensor.temperature.state | round(1) }}", opp
        ).async_render()
        == 12.8
    )

    assert (
        template.Template(
            "{{ states.sensor.temperature.state | multiply(10) | round }}", opp
        ).async_render()
        == 128
    )

    assert (
        template.Template(
            '{{ states.sensor.temperature.state | round(1, "floor") }}', opp
        ).async_render()
        == 12.7
    )

    assert (
        template.Template(
            '{{ states.sensor.temperature.state | round(1, "ceil") }}', opp
        ).async_render()
        == 12.8
    )

    assert (
        template.Template(
            '{{ states.sensor.temperature.state | round(1, "half") }}', opp
        ).async_render()
        == 13.0
    )


def test_rounding_value_get_original_value_on_error(opp):
    """Test rounding value get original value on error."""
    assert template.Template("{{ None | round }}", opp).async_render() is None

    assert (
        template.Template('{{ "no_number" | round }}', opp).async_render()
        == "no_number"
    )


def test_multiply(opp):
    """Test multiply."""
    tests = {None: None, 10: 100, '"abcd"': "abcd"}

    for inp, out in tests.items():
        assert (
            template.Template(
                "{{ %s | multiply(10) | round }}" % inp, opp
            ).async_render()
            == out
        )


def test_logarithm(opp):
    """Test logarithm."""
    tests = [
        (4, 2, 2.0),
        (1000, 10, 3.0),
        (math.e, "", 1.0),
        ('"invalid"', "_", "invalid"),
        (10, '"invalid"', 10.0),
    ]

    for value, base, expected in tests:
        assert (
            template.Template(
                f"{{{{ {value} | log({base}) | round(1) }}}}", opp
            ).async_render()
            == expected
        )

        assert (
            template.Template(
                f"{{{{ log({value}, {base}) | round(1) }}}}", opp
            ).async_render()
            == expected
        )


def test_sine(opp):
    """Test sine."""
    tests = [
        (0, 0.0),
        (math.pi / 2, 1.0),
        (math.pi, 0.0),
        (math.pi * 1.5, -1.0),
        (math.pi / 10, 0.309),
        ('"duck"', "duck"),
    ]

    for value, expected in tests:
        assert (
            template.Template("{{ %s | sin | round(3) }}" % value, opp).async_render()
            == expected
        )


def test_cos(opp):
    """Test cosine."""
    tests = [
        (0, 1.0),
        (math.pi / 2, 0.0),
        (math.pi, -1.0),
        (math.pi * 1.5, -0.0),
        (math.pi / 10, 0.951),
        ("'error'", "error"),
    ]

    for value, expected in tests:
        assert (
            template.Template("{{ %s | cos | round(3) }}" % value, opp).async_render()
            == expected
        )


def test_tan(opp):
    """Test tangent."""
    tests = [
        (0, 0.0),
        (math.pi, -0.0),
        (math.pi / 180 * 45, 1.0),
        (math.pi / 180 * 90, "1.633123935319537e+16"),
        (math.pi / 180 * 135, -1.0),
        ("'error'", "error"),
    ]

    for value, expected in tests:
        assert (
            template.Template("{{ %s | tan | round(3) }}" % value, opp).async_render()
            == expected
        )


def test_sqrt(opp):
    """Test square root."""
    tests = [
        (0, 0.0),
        (1, 1.0),
        (2, 1.414),
        (10, 3.162),
        (100, 10.0),
        ("'error'", "error"),
    ]

    for value, expected in tests:
        assert (
            template.Template("{{ %s | sqrt | round(3) }}" % value, opp).async_render()
            == expected
        )


def test_arc_sine(opp):
    """Test arcus sine."""
    tests = [
        (-2.0, -2.0),  # value error
        (-1.0, -1.571),
        (-0.5, -0.524),
        (0.0, 0.0),
        (0.5, 0.524),
        (1.0, 1.571),
        (2.0, 2.0),  # value error
        ('"error"', "error"),
    ]

    for value, expected in tests:
        assert (
            template.Template("{{ %s | asin | round(3) }}" % value, opp).async_render()
            == expected
        )


def test_arc_cos(opp):
    """Test arcus cosine."""
    tests = [
        (-2.0, -2.0),  # value error
        (-1.0, 3.142),
        (-0.5, 2.094),
        (0.0, 1.571),
        (0.5, 1.047),
        (1.0, 0.0),
        (2.0, 2.0),  # value error
        ('"error"', "error"),
    ]

    for value, expected in tests:
        assert (
            template.Template("{{ %s | acos | round(3) }}" % value, opp).async_render()
            == expected
        )


def test_arc_tan(opp):
    """Test arcus tangent."""
    tests = [
        (-10.0, -1.471),
        (-2.0, -1.107),
        (-1.0, -0.785),
        (-0.5, -0.464),
        (0.0, 0.0),
        (0.5, 0.464),
        (1.0, 0.785),
        (2.0, 1.107),
        (10.0, 1.471),
        ('"error"', "error"),
    ]

    for value, expected in tests:
        assert (
            template.Template("{{ %s | atan | round(3) }}" % value, opp).async_render()
            == expected
        )


def test_arc_tan2(opp):
    """Test two parameter version of arcus tangent."""
    tests = [
        (-10.0, -10.0, -2.356),
        (-10.0, 0.0, -1.571),
        (-10.0, 10.0, -0.785),
        (0.0, -10.0, 3.142),
        (0.0, 0.0, 0.0),
        (0.0, 10.0, 0.0),
        (10.0, -10.0, 2.356),
        (10.0, 0.0, 1.571),
        (10.0, 10.0, 0.785),
        (-4.0, 3.0, -0.927),
        (-1.0, 2.0, -0.464),
        (2.0, 1.0, 1.107),
        ('"duck"', '"goose"', ("duck", "goose")),
    ]

    for y, x, expected in tests:
        assert (
            template.Template(
                f"{{{{ ({y}, {x}) | atan2 | round(3) }}}}", opp
            ).async_render()
            == expected
        )
        assert (
            template.Template(
                f"{{{{ atan2({y}, {x}) | round(3) }}}}", opp
            ).async_render()
            == expected
        )


def test_strptime(opp):
    """Test the parse timestamp method."""
    tests = [
        ("2016-10-19 15:22:05.588122 UTC", "%Y-%m-%d %H:%M:%S.%f %Z", None),
        ("2016-10-19 15:22:05.588122+0100", "%Y-%m-%d %H:%M:%S.%f%z", None),
        ("2016-10-19 15:22:05.588122", "%Y-%m-%d %H:%M:%S.%f", None),
        ("2016-10-19", "%Y-%m-%d", None),
        ("2016", "%Y", None),
        ("15:22:05", "%H:%M:%S", None),
        ("1469119144", "%Y", 1469119144),
        ("invalid", "%Y", "invalid"),
    ]

    for inp, fmt, expected in tests:
        if expected is None:
            expected = str(datetime.strptime(inp, fmt))

        temp = f"{{{{ strptime('{inp}', '{fmt}') }}}}"

        assert template.Template(temp, opp).async_render() == expected


def test_timestamp_custom(opp):
    """Test the timestamps to custom filter."""
    now = dt_util.utcnow()
    tests = [
        (None, None, None, None),
        (1469119144, None, True, "2016-07-21 16:39:04"),
        (1469119144, "%Y", True, 2016),
        (1469119144, "invalid", True, "invalid"),
        (dt_util.as_timestamp(now), None, False, now.strftime("%Y-%m-%d %H:%M:%S")),
    ]

    for inp, fmt, local, out in tests:
        if fmt:
            fil = f"timestamp_custom('{fmt}')"
        elif fmt and local:
            fil = f"timestamp_custom('{fmt}', {local})"
        else:
            fil = "timestamp_custom"

        assert template.Template(f"{{{{ {inp} | {fil} }}}}", opp).async_render() == out


def test_timestamp_local(opp):
    """Test the timestamps to local filter."""
    tests = {None: None, 1469119144: "2016-07-21 16:39:04"}

    for inp, out in tests.items():
        assert (
            template.Template("{{ %s | timestamp_local }}" % inp, opp).async_render()
            == out
        )


def test_as_local(opp):
    """Test converting time to local."""

    opp.states.async_set("test.object", "available")
    last_updated = opp.states.get("test.object").last_updated
    assert template.Template(
        "{{ as_local(states.test.object.last_updated) }}", opp
    ).async_render() == str(dt_util.as_local(last_updated))
    assert template.Template(
        "{{ states.test.object.last_updated | as_local }}", opp
    ).async_render() == str(dt_util.as_local(last_updated))


def test_to_json(opp):
    """Test the object to JSON string filter."""

    # Note that we're not testing the actual json.loads and json.dumps methods,
    # only the filters, so we don't need to be exhaustive with our sample JSON.
    expected_result = {"Foo": "Bar"}
    actual_result = template.Template(
        "{{ {'Foo': 'Bar'} | to_json }}", opp
    ).async_render()
    assert actual_result == expected_result


def test_from_json(opp):
    """Test the JSON string to object filter."""

    # Note that we're not testing the actual json.loads and json.dumps methods,
    # only the filters, so we don't need to be exhaustive with our sample JSON.
    expected_result = "Bar"
    actual_result = template.Template(
        '{{ (\'{"Foo": "Bar"}\' | from_json).Foo }}', opp
    ).async_render()
    assert actual_result == expected_result


def test_min(opp):
    """Test the min filter."""
    assert template.Template("{{ [1, 2, 3] | min }}", opp).async_render() == 1


def test_max(opp):
    """Test the max filter."""
    assert template.Template("{{ [1, 2, 3] | max }}", opp).async_render() == 3


def test_ord(opp):
    """Test the ord filter."""
    assert template.Template('{{ "d" | ord }}', opp).async_render() == 100


def test_base64_encode(opp):
    """Test the base64_encode filter."""
    assert (
        template.Template('{{ "openpeerpower" | base64_encode }}', opp).async_render()
        == "b3BlbnBlZXJwb3dlcg=="
    )


def test_base64_decode(opp):
    """Test the base64_decode filter."""
    assert (
        template.Template(
            '{{ "b3BlbnBlZXJwb3dlcg==" | base64_decode }}', opp
        ).async_render()
        == "openpeerpower"
    )


def test_ordinal(opp):
    """Test the ordinal filter."""
    tests = [
        (1, "1st"),
        (2, "2nd"),
        (3, "3rd"),
        (4, "4th"),
        (5, "5th"),
        (12, "12th"),
        (100, "100th"),
        (101, "101st"),
    ]

    for value, expected in tests:
        assert (
            template.Template("{{ %s | ordinal }}" % value, opp).async_render()
            == expected
        )


def test_timestamp_utc(opp):
    """Test the timestamps to local filter."""
    now = dt_util.utcnow()
    tests = {
        None: None,
        1469119144: "2016-07-21 16:39:04",
        dt_util.as_timestamp(now): now.strftime("%Y-%m-%d %H:%M:%S"),
    }

    for inp, out in tests.items():
        assert (
            template.Template("{{ %s | timestamp_utc }}" % inp, opp).async_render()
            == out
        )


def test_as_timestamp(opp):
    """Test the as_timestamp function."""
    assert (
        template.Template('{{ as_timestamp("invalid") }}', opp).async_render() is None
    )
    opp.mock = None
    assert (
        template.Template("{{ as_timestamp(states.mock) }}", opp).async_render() is None
    )

    tpl = (
        '{{ as_timestamp(strptime("2024-02-03T09:10:24+0000", '
        '"%Y-%m-%dT%H:%M:%S%z")) }}'
    )
    assert template.Template(tpl, opp).async_render() == 1706951424.0


@patch.object(random, "choice")
def test_random_every_time(test_choice, opp):
    """Ensure the random filter runs every time, not just once."""
    tpl = template.Template("{{ [1,2] | random }}", opp)
    test_choice.return_value = "foo"
    assert tpl.async_render() == "foo"
    test_choice.return_value = "bar"
    assert tpl.async_render() == "bar"


def test_passing_vars_as_keywords(opp):
    """Test passing variables as keywords."""
    assert template.Template("{{ hello }}", opp).async_render(hello=127) == 127


def test_passing_vars_as_vars(opp):
    """Test passing variables as variables."""
    assert template.Template("{{ hello }}", opp).async_render({"hello": 127}) == 127


def test_passing_vars_as_list(opp):
    """Test passing variables as list."""
    assert template.render_complex(
        template.Template("{{ hello }}", opp), {"hello": ["foo", "bar"]}
    ) == ["foo", "bar"]


def test_passing_vars_as_list_element(opp):
    """Test passing variables as list."""
    assert (
        template.render_complex(
            template.Template("{{ hello[1] }}", opp), {"hello": ["foo", "bar"]}
        )
        == "bar"
    )


def test_passing_vars_as_dict_element(opp):
    """Test passing variables as list."""
    assert (
        template.render_complex(
            template.Template("{{ hello.foo }}", opp), {"hello": {"foo": "bar"}}
        )
        == "bar"
    )


def test_passing_vars_as_dict(opp):
    """Test passing variables as list."""
    assert template.render_complex(
        template.Template("{{ hello }}", opp), {"hello": {"foo": "bar"}}
    ) == {"foo": "bar"}


def test_render_with_possible_json_value_with_valid_json(opp):
    """Render with possible JSON value with valid JSON."""
    tpl = template.Template("{{ value_json.hello }}", opp)
    assert tpl.async_render_with_possible_json_value('{"hello": "world"}') == "world"


def test_render_with_possible_json_value_with_invalid_json(opp):
    """Render with possible JSON value with invalid JSON."""
    tpl = template.Template("{{ value_json }}", opp)
    assert tpl.async_render_with_possible_json_value("{ I AM NOT JSON }") == ""


def test_render_with_possible_json_value_with_template_error_value(opp):
    """Render with possible JSON value with template error value."""
    tpl = template.Template("{{ non_existing.variable }}", opp)
    assert tpl.async_render_with_possible_json_value("hello", "-") == "-"


def test_render_with_possible_json_value_with_missing_json_value(opp):
    """Render with possible JSON value with unknown JSON object."""
    tpl = template.Template("{{ value_json.goodbye }}", opp)
    assert tpl.async_render_with_possible_json_value('{"hello": "world"}') == ""


def test_render_with_possible_json_value_valid_with_is_defined(opp):
    """Render with possible JSON value with known JSON object."""
    tpl = template.Template("{{ value_json.hello|is_defined }}", opp)
    assert tpl.async_render_with_possible_json_value('{"hello": "world"}') == "world"


def test_render_with_possible_json_value_undefined_json(opp):
    """Render with possible JSON value with unknown JSON object."""
    tpl = template.Template("{{ value_json.bye|is_defined }}", opp)
    assert (
        tpl.async_render_with_possible_json_value('{"hello": "world"}')
        == '{"hello": "world"}'
    )


def test_render_with_possible_json_value_undefined_json_error_value(opp):
    """Render with possible JSON value with unknown JSON object."""
    tpl = template.Template("{{ value_json.bye|is_defined }}", opp)
    assert tpl.async_render_with_possible_json_value('{"hello": "world"}', "") == ""


def test_render_with_possible_json_value_non_string_value(opp):
    """Render with possible JSON value with non-string value."""
    tpl = template.Template(
        """
{{ strptime(value~'+0000', '%Y-%m-%d %H:%M:%S%z') }}
        """,
        opp,
    )
    value = datetime(2019, 1, 18, 12, 13, 14)
    expected = str(pytz.utc.localize(value))
    assert tpl.async_render_with_possible_json_value(value) == expected


def test_if_state_exists(opp):
    """Test if state exists works."""
    opp.states.async_set("test.object", "available")
    tpl = template.Template(
        "{% if states.test.object %}exists{% else %}not exists{% endif %}", opp
    )
    assert tpl.async_render() == "exists"


def test_is_state(opp):
    """Test is_state method."""
    opp.states.async_set("test.object", "available")
    tpl = template.Template(
        """
{% if is_state("test.object", "available") %}yes{% else %}no{% endif %}
        """,
        opp,
    )
    assert tpl.async_render() == "yes"

    tpl = template.Template(
        """
{{ is_state("test.noobject", "available") }}
        """,
        opp,
    )
    assert tpl.async_render() is False


def test_is_state_attr(opp):
    """Test is_state_attr method."""
    opp.states.async_set("test.object", "available", {"mode": "on"})
    tpl = template.Template(
        """
{% if is_state_attr("test.object", "mode", "on") %}yes{% else %}no{% endif %}
            """,
        opp,
    )
    assert tpl.async_render() == "yes"

    tpl = template.Template(
        """
{{ is_state_attr("test.noobject", "mode", "on") }}
            """,
        opp,
    )
    assert tpl.async_render() is False


def test_state_attr(opp):
    """Test state_attr method."""
    opp.states.async_set("test.object", "available", {"mode": "on"})
    tpl = template.Template(
        """
{% if state_attr("test.object", "mode") == "on" %}yes{% else %}no{% endif %}
            """,
        opp,
    )
    assert tpl.async_render() == "yes"

    tpl = template.Template(
        """
{{ state_attr("test.noobject", "mode") == None }}
            """,
        opp,
    )
    assert tpl.async_render() is True


def test_states_function(opp):
    """Test using states as a function."""
    opp.states.async_set("test.object", "available")
    tpl = template.Template('{{ states("test.object") }}', opp)
    assert tpl.async_render() == "available"

    tpl2 = template.Template('{{ states("test.object2") }}', opp)
    assert tpl2.async_render() == "unknown"


@patch(
    "openpeerpower.helpers.template.TemplateEnvironment.is_safe_callable",
    return_value=True,
)
def test_now(mock_is_safe, opp):
    """Test now method."""
    now = dt_util.now()
    with patch("openpeerpower.util.dt.now", return_value=now):
        info = template.Template("{{ now().isoformat() }}", opp).async_render_to_info()
        assert now.isoformat() == info.result()

    assert info.has_time is True


@patch(
    "openpeerpower.helpers.template.TemplateEnvironment.is_safe_callable",
    return_value=True,
)
def test_utcnow(mock_is_safe, opp):
    """Test now method."""
    utcnow = dt_util.utcnow()
    with patch("openpeerpower.util.dt.utcnow", return_value=utcnow):
        info = template.Template(
            "{{ utcnow().isoformat() }}", opp
        ).async_render_to_info()
        assert utcnow.isoformat() == info.result()

    assert info.has_time is True


@patch(
    "openpeerpower.helpers.template.TemplateEnvironment.is_safe_callable",
    return_value=True,
)
def test_relative_time(mock_is_safe, opp):
    """Test relative_time method."""
    now = datetime.strptime("2000-01-01 10:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
    with patch("openpeerpower.util.dt.now", return_value=now):
        assert (
            "1 hour"
            == template.Template(
                '{{relative_time(strptime("2000-01-01 09:00:00", "%Y-%m-%d %H:%M:%S"))}}',
                opp,
            ).async_render()
        )
        assert (
            "2 hours"
            == template.Template(
                '{{relative_time(strptime("2000-01-01 09:00:00 +01:00", "%Y-%m-%d %H:%M:%S %z"))}}',
                opp,
            ).async_render()
        )
        assert (
            "1 hour"
            == template.Template(
                '{{relative_time(strptime("2000-01-01 03:00:00 -06:00", "%Y-%m-%d %H:%M:%S %z"))}}',
                opp,
            ).async_render()
        )
        assert (
            str(template.strptime("2000-01-01 11:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z"))
            == template.Template(
                '{{relative_time(strptime("2000-01-01 11:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z"))}}',
                opp,
            ).async_render()
        )
        assert (
            "string"
            == template.Template(
                '{{relative_time("string")}}',
                opp,
            ).async_render()
        )


@patch(
    "openpeerpower.helpers.template.TemplateEnvironment.is_safe_callable",
    return_value=True,
)
def test_timedelta(mock_is_safe, opp):
    """Test relative_time method."""
    now = datetime.strptime("2000-01-01 10:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
    with patch("openpeerpower.util.dt.now", return_value=now):
        assert (
            "0:02:00"
            == template.Template(
                "{{timedelta(seconds=120)}}",
                opp,
            ).async_render()
        )
        assert (
            "1 day, 0:00:00"
            == template.Template(
                "{{timedelta(seconds=86400)}}",
                opp,
            ).async_render()
        )
        assert (
            "1 day, 4:00:00"
            == template.Template(
                "{{timedelta(days=1, hours=4)}}",
                opp,
            ).async_render()
        )
        assert (
            "1 hour"
            == template.Template(
                "{{relative_time(now() - timedelta(seconds=3600))}}",
                opp,
            ).async_render()
        )
        assert (
            "1 day"
            == template.Template(
                "{{relative_time(now() - timedelta(seconds=86400))}}",
                opp,
            ).async_render()
        )
        assert (
            "1 day"
            == template.Template(
                "{{relative_time(now() - timedelta(seconds=86401))}}",
                opp,
            ).async_render()
        )
        assert (
            "15 days"
            == template.Template(
                "{{relative_time(now() - timedelta(weeks=2, days=1))}}",
                opp,
            ).async_render()
        )


def test_regex_match(opp):
    """Test regex_match method."""
    tpl = template.Template(
        r"""
{{ '123-456-7890' | regex_match('(\\d{3})-(\\d{3})-(\\d{4})') }}
            """,
        opp,
    )
    assert tpl.async_render() is True

    tpl = template.Template(
        """
{{ 'Open Peer Power test' | regex_match('open', True) }}
            """,
        opp,
    )
    assert tpl.async_render() is True

    tpl = template.Template(
        """
    {{ 'Another Open Peer Power test' | regex_match('Open') }}
                    """,
        opp,
    )
    assert tpl.async_render() is False

    tpl = template.Template(
        """
{{ ['Open Peer Power test'] | regex_match('.*Peer') }}
            """,
        opp,
    )
    assert tpl.async_render() is True


def test_regex_search(opp):
    """Test regex_search method."""
    tpl = template.Template(
        r"""
{{ '123-456-7890' | regex_search('(\\d{3})-(\\d{3})-(\\d{4})') }}
            """,
        opp,
    )
    assert tpl.async_render() is True

    tpl = template.Template(
        """
{{ 'Open Peer Power test' | regex_search('open', True) }}
            """,
        opp,
    )
    assert tpl.async_render() is True

    tpl = template.Template(
        """
    {{ 'Another Open Peer Power test' | regex_search('Open') }}
                    """,
        opp,
    )
    assert tpl.async_render() is True

    tpl = template.Template(
        """
{{ ['Open Peer Power test'] | regex_search('Power') }}
            """,
        opp,
    )
    assert tpl.async_render() is True


def test_regex_replace(opp):
    """Test regex_replace method."""
    tpl = template.Template(
        r"""
{{ 'Hello World' | regex_replace('(Hello\\s)',) }}
            """,
        opp,
    )
    assert tpl.async_render() == "World"

    tpl = template.Template(
        """
{{ ['Open Peer hinderer test'] | regex_replace('hinder', 'Pow') }}
            """,
        opp,
    )
    assert tpl.async_render() == ["Open Peer Power test"]


def test_regex_findall_index(opp):
    """Test regex_findall_index method."""
    tpl = template.Template(
        """
{{ 'Flight from JFK to LHR' | regex_findall_index('([A-Z]{3})', 0) }}
            """,
        opp,
    )
    assert tpl.async_render() == "JFK"

    tpl = template.Template(
        """
{{ 'Flight from JFK to LHR' | regex_findall_index('([A-Z]{3})', 1) }}
            """,
        opp,
    )
    assert tpl.async_render() == "LHR"

    tpl = template.Template(
        """
{{ ['JFK', 'LHR'] | regex_findall_index('([A-Z]{3})', 1) }}
            """,
        opp,
    )
    assert tpl.async_render() == "LHR"


def test_bitwise_and(opp):
    """Test bitwise_and method."""
    tpl = template.Template(
        """
{{ 8 | bitwise_and(8) }}
            """,
        opp,
    )
    assert tpl.async_render() == 8 & 8
    tpl = template.Template(
        """
{{ 10 | bitwise_and(2) }}
            """,
        opp,
    )
    assert tpl.async_render() == 10 & 2
    tpl = template.Template(
        """
{{ 8 | bitwise_and(2) }}
            """,
        opp,
    )
    assert tpl.async_render() == 8 & 2


def test_bitwise_or(opp):
    """Test bitwise_or method."""
    tpl = template.Template(
        """
{{ 8 | bitwise_or(8) }}
            """,
        opp,
    )
    assert tpl.async_render() == 8 | 8
    tpl = template.Template(
        """
{{ 10 | bitwise_or(2) }}
            """,
        opp,
    )
    assert tpl.async_render() == 10 | 2
    tpl = template.Template(
        """
{{ 8 | bitwise_or(2) }}
            """,
        opp,
    )
    assert tpl.async_render() == 8 | 2


def test_distance_function_with_1_state(opp):
    """Test distance function with 1 state."""
    _set_up_units(opp)
    opp.states.async_set(
        "test.object", "happy", {"latitude": 32.87336, "longitude": -117.22943}
    )
    tpl = template.Template("{{ distance(states.test.object) | round }}", opp)
    assert tpl.async_render() == 187


def test_distance_function_with_2_states(opp):
    """Test distance function with 2 states."""
    _set_up_units(opp)
    opp.states.async_set(
        "test.object", "happy", {"latitude": 32.87336, "longitude": -117.22943}
    )
    opp.states.async_set(
        "test.object_2",
        "happy",
        {"latitude": opp.config.latitude, "longitude": opp.config.longitude},
    )
    tpl = template.Template(
        "{{ distance(states.test.object, states.test.object_2) | round }}", opp
    )
    assert tpl.async_render() == 187


def test_distance_function_with_1_coord(opp):
    """Test distance function with 1 coord."""
    _set_up_units(opp)
    tpl = template.Template('{{ distance("32.87336", "-117.22943") | round }}', opp)
    assert tpl.async_render() == 187


def test_distance_function_with_2_coords(opp):
    """Test distance function with 2 coords."""
    _set_up_units(opp)
    assert (
        template.Template(
            '{{ distance("32.87336", "-117.22943", %s, %s) | round }}'
            % (opp.config.latitude, opp.config.longitude),
            opp,
        ).async_render()
        == 187
    )


def test_distance_function_with_1_state_1_coord(opp):
    """Test distance function with 1 state 1 coord."""
    _set_up_units(opp)
    opp.states.async_set(
        "test.object_2",
        "happy",
        {"latitude": opp.config.latitude, "longitude": opp.config.longitude},
    )
    tpl = template.Template(
        '{{ distance("32.87336", "-117.22943", states.test.object_2) ' "| round }}",
        opp,
    )
    assert tpl.async_render() == 187

    tpl2 = template.Template(
        '{{ distance(states.test.object_2, "32.87336", "-117.22943") ' "| round }}",
        opp,
    )
    assert tpl2.async_render() == 187


def test_distance_function_return_none_if_invalid_state(opp):
    """Test distance function return None if invalid state."""
    opp.states.async_set("test.object_2", "happy", {"latitude": 10})
    tpl = template.Template("{{ distance(states.test.object_2) | round }}", opp)
    assert tpl.async_render() is None


def test_distance_function_return_none_if_invalid_coord(opp):
    """Test distance function return None if invalid coord."""
    assert template.Template('{{ distance("123", "abc") }}', opp).async_render() is None

    assert template.Template('{{ distance("123") }}', opp).async_render() is None

    opp.states.async_set(
        "test.object_2",
        "happy",
        {"latitude": opp.config.latitude, "longitude": opp.config.longitude},
    )
    tpl = template.Template('{{ distance("123", states.test_object_2) }}', opp)
    assert tpl.async_render() is None


def test_distance_function_with_2_entity_ids(opp):
    """Test distance function with 2 entity ids."""
    _set_up_units(opp)
    opp.states.async_set(
        "test.object", "happy", {"latitude": 32.87336, "longitude": -117.22943}
    )
    opp.states.async_set(
        "test.object_2",
        "happy",
        {"latitude": opp.config.latitude, "longitude": opp.config.longitude},
    )
    tpl = template.Template(
        '{{ distance("test.object", "test.object_2") | round }}', opp
    )
    assert tpl.async_render() == 187


def test_distance_function_with_1_entity_1_coord(opp):
    """Test distance function with 1 entity_id and 1 coord."""
    _set_up_units(opp)
    opp.states.async_set(
        "test.object",
        "happy",
        {"latitude": opp.config.latitude, "longitude": opp.config.longitude},
    )
    tpl = template.Template(
        '{{ distance("test.object", "32.87336", "-117.22943") | round }}', opp
    )
    assert tpl.async_render() == 187


def test_closest_function_home_vs_domain(opp):
    """Test closest function home vs domain."""
    opp.states.async_set(
        "test_domain.object",
        "happy",
        {
            "latitude": opp.config.latitude + 0.1,
            "longitude": opp.config.longitude + 0.1,
        },
    )

    opp.states.async_set(
        "not_test_domain.but_closer",
        "happy",
        {"latitude": opp.config.latitude, "longitude": opp.config.longitude},
    )

    assert (
        template.Template(
            "{{ closest(states.test_domain).entity_id }}", opp
        ).async_render()
        == "test_domain.object"
    )

    assert (
        template.Template(
            "{{ (states.test_domain | closest).entity_id }}", opp
        ).async_render()
        == "test_domain.object"
    )


def test_closest_function_home_vs_all_states(opp):
    """Test closest function home vs all states."""
    opp.states.async_set(
        "test_domain.object",
        "happy",
        {
            "latitude": opp.config.latitude + 0.1,
            "longitude": opp.config.longitude + 0.1,
        },
    )

    opp.states.async_set(
        "test_domain_2.and_closer",
        "happy",
        {"latitude": opp.config.latitude, "longitude": opp.config.longitude},
    )

    assert (
        template.Template("{{ closest(states).entity_id }}", opp).async_render()
        == "test_domain_2.and_closer"
    )

    assert (
        template.Template("{{ (states | closest).entity_id }}", opp).async_render()
        == "test_domain_2.and_closer"
    )


async def test_closest_function_home_vs_group_entity_id(opp):
    """Test closest function home vs group entity id."""
    opp.states.async_set(
        "test_domain.object",
        "happy",
        {
            "latitude": opp.config.latitude + 0.1,
            "longitude": opp.config.longitude + 0.1,
        },
    )

    opp.states.async_set(
        "not_in_group.but_closer",
        "happy",
        {"latitude": opp.config.latitude, "longitude": opp.config.longitude},
    )

    assert await async_setup_component(opp, "group", {})
    await opp.async_block_till_done()
    await group.Group.async_create_group(opp, "location group", ["test_domain.object"])

    info = render_to_info(opp, '{{ closest("group.location_group").entity_id }}')
    assert_result_info(
        info, "test_domain.object", {"group.location_group", "test_domain.object"}
    )
    assert info.rate_limit is None


async def test_closest_function_home_vs_group_state(opp):
    """Test closest function home vs group state."""
    opp.states.async_set(
        "test_domain.object",
        "happy",
        {
            "latitude": opp.config.latitude + 0.1,
            "longitude": opp.config.longitude + 0.1,
        },
    )

    opp.states.async_set(
        "not_in_group.but_closer",
        "happy",
        {"latitude": opp.config.latitude, "longitude": opp.config.longitude},
    )

    assert await async_setup_component(opp, "group", {})
    await opp.async_block_till_done()
    await group.Group.async_create_group(opp, "location group", ["test_domain.object"])

    info = render_to_info(opp, '{{ closest("group.location_group").entity_id }}')
    assert_result_info(
        info, "test_domain.object", {"group.location_group", "test_domain.object"}
    )
    assert info.rate_limit is None

    info = render_to_info(opp, "{{ closest(states.group.location_group).entity_id }}")
    assert_result_info(
        info, "test_domain.object", {"test_domain.object", "group.location_group"}
    )
    assert info.rate_limit is None


async def test_expand(opp):
    """Test expand function."""
    info = render_to_info(opp, "{{ expand('test.object') }}")
    assert_result_info(info, [], ["test.object"])
    assert info.rate_limit is None

    info = render_to_info(opp, "{{ expand(56) }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    opp.states.async_set("test.object", "happy")

    info = render_to_info(
        opp, "{{ expand('test.object') | map(attribute='entity_id') | join(', ') }}"
    )
    assert_result_info(info, "test.object", ["test.object"])
    assert info.rate_limit is None

    info = render_to_info(
        opp,
        "{{ expand('group.new_group') | map(attribute='entity_id') | join(', ') }}",
    )
    assert_result_info(info, "", ["group.new_group"])
    assert info.rate_limit is None

    info = render_to_info(
        opp, "{{ expand(states.group) | map(attribute='entity_id') | join(', ') }}"
    )
    assert_result_info(info, "", [], ["group"])
    assert info.rate_limit == template.DOMAIN_STATES_RATE_LIMIT

    assert await async_setup_component(opp, "group", {})
    await opp.async_block_till_done()
    await group.Group.async_create_group(opp, "new group", ["test.object"])

    info = render_to_info(
        opp,
        "{{ expand('group.new_group') | map(attribute='entity_id') | join(', ') }}",
    )
    assert_result_info(info, "test.object", {"group.new_group", "test.object"})
    assert info.rate_limit is None

    info = render_to_info(
        opp, "{{ expand(states.group) | map(attribute='entity_id') | join(', ') }}"
    )
    assert_result_info(info, "test.object", {"test.object"}, ["group"])
    assert info.rate_limit == template.DOMAIN_STATES_RATE_LIMIT

    info = render_to_info(
        opp,
        "{{ expand('group.new_group', 'test.object')"
        " | map(attribute='entity_id') | join(', ') }}",
    )
    assert_result_info(info, "test.object", {"test.object", "group.new_group"})

    info = render_to_info(
        opp,
        "{{ ['group.new_group', 'test.object'] | expand"
        " | map(attribute='entity_id') | join(', ') }}",
    )
    assert_result_info(info, "test.object", {"test.object", "group.new_group"})
    assert info.rate_limit is None

    opp.states.async_set("sensor.power_1", 0)
    opp.states.async_set("sensor.power_2", 200.2)
    opp.states.async_set("sensor.power_3", 400.4)

    assert await async_setup_component(opp, "group", {})
    await opp.async_block_till_done()
    await group.Group.async_create_group(
        opp, "power sensors", ["sensor.power_1", "sensor.power_2", "sensor.power_3"]
    )

    info = render_to_info(
        opp,
        "{{ states.group.power_sensors.attributes.entity_id | expand | map(attribute='state')|map('float')|sum  }}",
    )
    assert_result_info(
        info,
        200.2 + 400.4,
        {"group.power_sensors", "sensor.power_1", "sensor.power_2", "sensor.power_3"},
    )
    assert info.rate_limit is None


async def test_device_entities(opp):
    """Test expand function."""
    config_entry = MockConfigEntry(domain="light")
    device_registry = mock_device_registry(opp)
    entity_registry = mock_registry(opp)

    # Test non existing device ids
    info = render_to_info(opp, "{{ device_entities('abc123') }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(opp, "{{ device_entities(56) }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Test device without entities
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={("mac", "12:34:56:AB:CD:EF")},
    )
    info = render_to_info(opp, f"{{{{ device_entities('{device_entry.id}') }}}}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Test device with single entity, which has no state
    entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        device_id=device_entry.id,
    )
    info = render_to_info(opp, f"{{{{ device_entities('{device_entry.id}') }}}}")
    assert_result_info(info, ["light.hue_5678"], [])
    assert info.rate_limit is None
    info = render_to_info(
        opp,
        f"{{{{ device_entities('{device_entry.id}') | expand | map(attribute='entity_id') | join(', ') }}}}",
    )
    assert_result_info(info, "", ["light.hue_5678"])
    assert info.rate_limit is None

    # Test device with single entity, with state
    opp.states.async_set("light.hue_5678", "happy")
    info = render_to_info(
        opp,
        f"{{{{ device_entities('{device_entry.id}') | expand | map(attribute='entity_id') | join(', ') }}}}",
    )
    assert_result_info(info, "light.hue_5678", ["light.hue_5678"])
    assert info.rate_limit is None

    # Test device with multiple entities, which have a state
    entity_registry.async_get_or_create(
        "light",
        "hue",
        "ABCD",
        config_entry=config_entry,
        device_id=device_entry.id,
    )
    opp.states.async_set("light.hue_abcd", "camper")
    info = render_to_info(opp, f"{{{{ device_entities('{device_entry.id}') }}}}")
    assert_result_info(info, ["light.hue_5678", "light.hue_abcd"], [])
    assert info.rate_limit is None
    info = render_to_info(
        opp,
        f"{{{{ device_entities('{device_entry.id}') | expand | map(attribute='entity_id') | join(', ') }}}}",
    )
    assert_result_info(
        info, "light.hue_5678, light.hue_abcd", ["light.hue_5678", "light.hue_abcd"]
    )
    assert info.rate_limit is None


def test_closest_function_to_coord(opp):
    """Test closest function to coord."""
    opp.states.async_set(
        "test_domain.closest_home",
        "happy",
        {
            "latitude": opp.config.latitude + 0.1,
            "longitude": opp.config.longitude + 0.1,
        },
    )

    opp.states.async_set(
        "test_domain.closest_zone",
        "happy",
        {
            "latitude": opp.config.latitude + 0.2,
            "longitude": opp.config.longitude + 0.2,
        },
    )

    opp.states.async_set(
        "zone.far_away",
        "zoning",
        {
            "latitude": opp.config.latitude + 0.3,
            "longitude": opp.config.longitude + 0.3,
        },
    )

    tpl = template.Template(
        '{{ closest("%s", %s, states.test_domain).entity_id }}'
        % (opp.config.latitude + 0.3, opp.config.longitude + 0.3),
        opp,
    )

    assert tpl.async_render() == "test_domain.closest_zone"

    tpl = template.Template(
        '{{ (states.test_domain | closest("%s", %s)).entity_id }}'
        % (opp.config.latitude + 0.3, opp.config.longitude + 0.3),
        opp,
    )

    assert tpl.async_render() == "test_domain.closest_zone"


def test_async_render_to_info_with_branching(opp):
    """Test async_render_to_info function by domain."""
    opp.states.async_set("light.a", "off")
    opp.states.async_set("light.b", "on")
    opp.states.async_set("light.c", "off")

    info = render_to_info(
        opp,
        """
{% if states.light.a == "on" %}
  {{ states.light.b.state }}
{% else %}
  {{ states.light.c.state }}
{% endif %}
""",
    )
    assert_result_info(info, "off", {"light.a", "light.c"})
    assert info.rate_limit is None

    info = render_to_info(
        opp,
        """
            {% if states.light.a.state == "off" %}
            {% set domain = "light" %}
            {{ states[domain].b.state }}
            {% endif %}
""",
    )
    assert_result_info(info, "on", {"light.a", "light.b"})
    assert info.rate_limit is None


def test_async_render_to_info_with_complex_branching(opp):
    """Test async_render_to_info function by domain."""
    opp.states.async_set("light.a", "off")
    opp.states.async_set("light.b", "on")
    opp.states.async_set("light.c", "off")
    opp.states.async_set("vacuum.a", "off")
    opp.states.async_set("device_tracker.a", "off")
    opp.states.async_set("device_tracker.b", "off")
    opp.states.async_set("lock.a", "off")
    opp.states.async_set("sensor.a", "off")
    opp.states.async_set("binary_sensor.a", "off")

    info = render_to_info(
        opp,
        """
{% set domain = "vacuum" %}
{%      if                 states.light.a == "on" %}
  {{ states.light.b.state }}
{% elif  states.light.a == "on" %}
  {{ states.device_tracker }}
{%     elif     states.light.a == "on" %}
  {{ states[domain] | list }}
{%         elif     states('light.b') == "on" %}
  {{ states[otherdomain] | map(attribute='entity_id') | list }}
{% elif states.light.a == "on" %}
  {{ states["nonexist"] | list }}
{% else %}
  else
{% endif %}
""",
        {"otherdomain": "sensor"},
    )

    assert_result_info(info, ["sensor.a"], {"light.a", "light.b"}, {"sensor"})
    assert info.rate_limit == template.DOMAIN_STATES_RATE_LIMIT


async def test_async_render_to_info_with_wildcard_matching_entity_id(opp):
    """Test tracking template with a wildcard."""
    template_complex_str = r"""

{% for state in states.cover %}
  {% if state.entity_id | regex_match('.*\.office_') %}
    {{ state.entity_id }}={{ state.state }}
  {% endif %}
{% endfor %}

"""
    opp.states.async_set("cover.office_drapes", "closed")
    opp.states.async_set("cover.office_window", "closed")
    opp.states.async_set("cover.office_skylight", "open")
    info = render_to_info(opp, template_complex_str)

    assert info.domains == {"cover"}
    assert info.entities == set()
    assert info.all_states is False
    assert info.rate_limit == template.DOMAIN_STATES_RATE_LIMIT


async def test_async_render_to_info_with_wildcard_matching_state(opp):
    """Test tracking template with a wildcard."""
    template_complex_str = """

{% for state in states %}
  {% if state.state | regex_match('ope.*') %}
    {{ state.entity_id }}={{ state.state }}
  {% endif %}
{% endfor %}

"""
    opp.states.async_set("cover.office_drapes", "closed")
    opp.states.async_set("cover.office_window", "closed")
    opp.states.async_set("cover.office_skylight", "open")
    opp.states.async_set("cover.x_skylight", "open")
    opp.states.async_set("binary_sensor.door", "open")
    await opp.async_block_till_done()

    info = render_to_info(opp, template_complex_str)

    assert not info.domains
    assert info.entities == set()
    assert info.all_states is True
    assert info.rate_limit == template.ALL_STATES_RATE_LIMIT

    opp.states.async_set("binary_sensor.door", "closed")
    info = render_to_info(opp, template_complex_str)

    assert not info.domains
    assert info.entities == set()
    assert info.all_states is True
    assert info.rate_limit == template.ALL_STATES_RATE_LIMIT

    template_cover_str = """

{% for state in states.cover %}
  {% if state.state | regex_match('ope.*') %}
    {{ state.entity_id }}={{ state.state }}
  {% endif %}
{% endfor %}

"""
    opp.states.async_set("cover.x_skylight", "closed")
    info = render_to_info(opp, template_cover_str)

    assert info.domains == {"cover"}
    assert info.entities == set()
    assert info.all_states is False
    assert info.rate_limit == template.DOMAIN_STATES_RATE_LIMIT


def test_nested_async_render_to_info_case(opp):
    """Test a deeply nested state with async_render_to_info."""

    opp.states.async_set("input_select.picker", "vacuum.a")
    opp.states.async_set("vacuum.a", "off")

    info = render_to_info(
        opp, "{{ states[states['input_select.picker'].state].state }}", {}
    )
    assert_result_info(info, "off", {"input_select.picker", "vacuum.a"})
    assert info.rate_limit is None


def test_result_as_boolean(opp):
    """Test converting a template result to a boolean."""

    assert template.result_as_boolean(True) is True
    assert template.result_as_boolean(" 1 ") is True
    assert template.result_as_boolean(" true ") is True
    assert template.result_as_boolean(" TrUE ") is True
    assert template.result_as_boolean(" YeS ") is True
    assert template.result_as_boolean(" On ") is True
    assert template.result_as_boolean(" Enable ") is True
    assert template.result_as_boolean(1) is True
    assert template.result_as_boolean(-1) is True
    assert template.result_as_boolean(500) is True
    assert template.result_as_boolean(0.5) is True
    assert template.result_as_boolean(0.389) is True
    assert template.result_as_boolean(35) is True

    assert template.result_as_boolean(False) is False
    assert template.result_as_boolean(" 0 ") is False
    assert template.result_as_boolean(" false ") is False
    assert template.result_as_boolean(" FaLsE ") is False
    assert template.result_as_boolean(" no ") is False
    assert template.result_as_boolean(" off ") is False
    assert template.result_as_boolean(" disable ") is False
    assert template.result_as_boolean(0) is False
    assert template.result_as_boolean(0.0) is False
    assert template.result_as_boolean("0.00") is False
    assert template.result_as_boolean(None) is False


def test_closest_function_to_entity_id(opp):
    """Test closest function to entity id."""
    opp.states.async_set(
        "test_domain.closest_home",
        "happy",
        {
            "latitude": opp.config.latitude + 0.1,
            "longitude": opp.config.longitude + 0.1,
        },
    )

    opp.states.async_set(
        "test_domain.closest_zone",
        "happy",
        {
            "latitude": opp.config.latitude + 0.2,
            "longitude": opp.config.longitude + 0.2,
        },
    )

    opp.states.async_set(
        "zone.far_away",
        "zoning",
        {
            "latitude": opp.config.latitude + 0.3,
            "longitude": opp.config.longitude + 0.3,
        },
    )

    info = render_to_info(
        opp,
        "{{ closest(zone, states.test_domain).entity_id }}",
        {"zone": "zone.far_away"},
    )

    assert_result_info(
        info,
        "test_domain.closest_zone",
        ["test_domain.closest_home", "test_domain.closest_zone", "zone.far_away"],
        ["test_domain"],
    )

    info = render_to_info(
        opp,
        "{{ ([states.test_domain, 'test_domain.closest_zone'] "
        "| closest(zone)).entity_id }}",
        {"zone": "zone.far_away"},
    )

    assert_result_info(
        info,
        "test_domain.closest_zone",
        ["test_domain.closest_home", "test_domain.closest_zone", "zone.far_away"],
        ["test_domain"],
    )


def test_closest_function_to_state(opp):
    """Test closest function to state."""
    opp.states.async_set(
        "test_domain.closest_home",
        "happy",
        {
            "latitude": opp.config.latitude + 0.1,
            "longitude": opp.config.longitude + 0.1,
        },
    )

    opp.states.async_set(
        "test_domain.closest_zone",
        "happy",
        {
            "latitude": opp.config.latitude + 0.2,
            "longitude": opp.config.longitude + 0.2,
        },
    )

    opp.states.async_set(
        "zone.far_away",
        "zoning",
        {
            "latitude": opp.config.latitude + 0.3,
            "longitude": opp.config.longitude + 0.3,
        },
    )

    assert (
        template.Template(
            "{{ closest(states.zone.far_away, states.test_domain).entity_id }}", opp
        ).async_render()
        == "test_domain.closest_zone"
    )


def test_closest_function_invalid_state(opp):
    """Test closest function invalid state."""
    opp.states.async_set(
        "test_domain.closest_home",
        "happy",
        {
            "latitude": opp.config.latitude + 0.1,
            "longitude": opp.config.longitude + 0.1,
        },
    )

    for state in ("states.zone.non_existing", '"zone.non_existing"'):
        assert (
            template.Template("{{ closest(%s, states) }}" % state, opp).async_render()
            is None
        )


def test_closest_function_state_with_invalid_location(opp):
    """Test closest function state with invalid location."""
    opp.states.async_set(
        "test_domain.closest_home",
        "happy",
        {"latitude": "invalid latitude", "longitude": opp.config.longitude + 0.1},
    )

    assert (
        template.Template(
            "{{ closest(states.test_domain.closest_home, states) }}", opp
        ).async_render()
        is None
    )


def test_closest_function_invalid_coordinates(opp):
    """Test closest function invalid coordinates."""
    opp.states.async_set(
        "test_domain.closest_home",
        "happy",
        {
            "latitude": opp.config.latitude + 0.1,
            "longitude": opp.config.longitude + 0.1,
        },
    )

    assert (
        template.Template(
            '{{ closest("invalid", "coord", states) }}', opp
        ).async_render()
        is None
    )
    assert (
        template.Template(
            '{{ states | closest("invalid", "coord") }}', opp
        ).async_render()
        is None
    )


def test_closest_function_no_location_states(opp):
    """Test closest function without location states."""
    assert (
        template.Template("{{ closest(states).entity_id }}", opp).async_render() == ""
    )


def test_generate_filter_iterators(opp):
    """Test extract entities function with none entities stuff."""
    info = render_to_info(
        opp,
        """
        {% for state in states %}
        {{ state.entity_id }}
        {% endfor %}
        """,
    )
    assert_result_info(info, "", all_states=True)

    info = render_to_info(
        opp,
        """
        {% for state in states.sensor %}
        {{ state.entity_id }}
        {% endfor %}
        """,
    )
    assert_result_info(info, "", domains=["sensor"])

    opp.states.async_set("sensor.test_sensor", "off", {"attr": "value"})

    # Don't need the entity because the state is not accessed
    info = render_to_info(
        opp,
        """
        {% for state in states.sensor %}
        {{ state.entity_id }}
        {% endfor %}
        """,
    )
    assert_result_info(info, "sensor.test_sensor", domains=["sensor"])

    # But we do here because the state gets accessed
    info = render_to_info(
        opp,
        """
        {% for state in states.sensor %}
        {{ state.entity_id }}={{ state.state }},
        {% endfor %}
        """,
    )
    assert_result_info(info, "sensor.test_sensor=off,", [], ["sensor"])

    info = render_to_info(
        opp,
        """
        {% for state in states.sensor %}
        {{ state.entity_id }}={{ state.attributes.attr }},
        {% endfor %}
        """,
    )
    assert_result_info(info, "sensor.test_sensor=value,", [], ["sensor"])


def test_generate_select(opp):
    """Test extract entities function with none entities stuff."""
    template_str = """
{{ states.sensor|selectattr("state","equalto","off")
|join(",", attribute="entity_id") }}
        """

    tmp = template.Template(template_str, opp)
    info = tmp.async_render_to_info()
    assert_result_info(info, "", [], [])
    assert info.domains_lifecycle == {"sensor"}

    opp.states.async_set("sensor.test_sensor", "off", {"attr": "value"})
    opp.states.async_set("sensor.test_sensor_on", "on")

    info = tmp.async_render_to_info()
    assert_result_info(
        info,
        "sensor.test_sensor",
        [],
        ["sensor"],
    )
    assert info.domains_lifecycle == {"sensor"}


async def test_async_render_to_info_in_conditional(opp):
    """Test extract entities function with none entities stuff."""
    template_str = """
{{ states("sensor.xyz") == "dog" }}
        """

    tmp = template.Template(template_str, opp)
    info = tmp.async_render_to_info()
    assert_result_info(info, False, ["sensor.xyz"], [])

    opp.states.async_set("sensor.xyz", "dog")
    opp.states.async_set("sensor.cow", "True")
    await opp.async_block_till_done()

    template_str = """
{% if states("sensor.xyz") == "dog" %}
  {{ states("sensor.cow") }}
{% else %}
  {{ states("sensor.pig") }}
{% endif %}
        """

    tmp = template.Template(template_str, opp)
    info = tmp.async_render_to_info()
    assert_result_info(info, True, ["sensor.xyz", "sensor.cow"], [])

    opp.states.async_set("sensor.xyz", "sheep")
    opp.states.async_set("sensor.pig", "oink")

    await opp.async_block_till_done()

    tmp = template.Template(template_str, opp)
    info = tmp.async_render_to_info()
    assert_result_info(info, "oink", ["sensor.xyz", "sensor.pig"], [])


def test_jinja_namespace(opp):
    """Test Jinja's namespace command can be used."""
    test_template = template.Template(
        (
            "{% set ns = namespace(a_key='') %}"
            "{% set ns.a_key = states.sensor.dummy.state %}"
            "{{ ns.a_key }}"
        ),
        opp,
    )

    opp.states.async_set("sensor.dummy", "a value")
    assert test_template.async_render() == "a value"

    opp.states.async_set("sensor.dummy", "another value")
    assert test_template.async_render() == "another value"


def test_state_with_unit(opp):
    """Test the state_with_unit property helper."""
    opp.states.async_set("sensor.test", "23", {ATTR_UNIT_OF_MEASUREMENT: "beers"})
    opp.states.async_set("sensor.test2", "wow")

    tpl = template.Template("{{ states.sensor.test.state_with_unit }}", opp)

    assert tpl.async_render() == "23 beers"

    tpl = template.Template("{{ states.sensor.test2.state_with_unit }}", opp)

    assert tpl.async_render() == "wow"

    tpl = template.Template(
        "{% for state in states %}{{ state.state_with_unit }} {% endfor %}", opp
    )

    assert tpl.async_render() == "23 beers wow"

    tpl = template.Template("{{ states.sensor.non_existing.state_with_unit }}", opp)

    assert tpl.async_render() == ""


def test_length_of_states(opp):
    """Test fetching the length of states."""
    opp.states.async_set("sensor.test", "23")
    opp.states.async_set("sensor.test2", "wow")
    opp.states.async_set("climate.test2", "cooling")

    tpl = template.Template("{{ states | length }}", opp)
    assert tpl.async_render() == 3

    tpl = template.Template("{{ states.sensor | length }}", opp)
    assert tpl.async_render() == 2


def test_render_complex_handling_non_template_values(opp):
    """Test that we can render non-template fields."""
    assert template.render_complex(
        {True: 1, False: template.Template("{{ hello }}", opp)}, {"hello": 2}
    ) == {True: 1, False: 2}


def test_urlencode(opp):
    """Test the urlencode method."""
    tpl = template.Template(
        ("{% set dict = {'foo': 'x&y', 'bar': 42} %}" "{{ dict | urlencode }}"),
        opp,
    )
    assert tpl.async_render() == "foo=x%26y&bar=42"
    tpl = template.Template(
        ("{% set string = 'the quick brown fox = true' %}" "{{ string | urlencode }}"),
        opp,
    )
    assert tpl.async_render() == "the%20quick%20brown%20fox%20%3D%20true"


async def test_cache_garbage_collection():
    """Test caching a template."""
    template_string = (
        "{% set dict = {'foo': 'x&y', 'bar': 42} %} {{ dict | urlencode }}"
    )
    tpl = template.Template(
        (template_string),
    )
    tpl.ensure_valid()
    assert template._NO_OPP_ENV.template_cache.get(
        template_string
    )  # pylint: disable=protected-access

    tpl2 = template.Template(
        (template_string),
    )
    tpl2.ensure_valid()
    assert template._NO_OPP_ENV.template_cache.get(
        template_string
    )  # pylint: disable=protected-access

    del tpl
    assert template._NO_OPP_ENV.template_cache.get(
        template_string
    )  # pylint: disable=protected-access
    del tpl2
    assert not template._NO_OPP_ENV.template_cache.get(
        template_string
    )  # pylint: disable=protected-access


def test_is_template_string():
    """Test is template string."""
    assert template.is_template_string("{{ x }}") is True
    assert template.is_template_string("{% if x == 2 %}1{% else %}0{%end if %}") is True
    assert template.is_template_string("{# a comment #} Hey") is True
    assert template.is_template_string("1") is False
    assert template.is_template_string("Some Text") is False


async def test_protected_blocked(opp):
    """Test accessing __getattr__ produces a template error."""
    tmp = template.Template('{{ states.__getattr__("any") }}', opp)
    with pytest.raises(TemplateError):
        tmp.async_render()

    tmp = template.Template('{{ states.sensor.__getattr__("any") }}', opp)
    with pytest.raises(TemplateError):
        tmp.async_render()

    tmp = template.Template('{{ states.sensor.any.__getattr__("any") }}', opp)
    with pytest.raises(TemplateError):
        tmp.async_render()


async def test_demo_template(opp):
    """Test the demo template works as expected."""
    opp.states.async_set("sun.sun", "above", {"elevation": 50, "next_rising": "later"})
    for i in range(2):
        opp.states.async_set(f"sensor.sensor{i}", "on")

    demo_template_str = """
{## Imitate available variables: ##}
{% set my_test_json = {
  "temperature": 25,
  "unit": "°C"
} %}

The temperature is {{ my_test_json.temperature }} {{ my_test_json.unit }}.

{% if is_state("sun.sun", "above_horizon") -%}
  The sun rose {{ relative_time(states.sun.sun.last_changed) }} ago.
{%- else -%}
  The sun will rise at {{ as_timestamp(strptime(state_attr("sun.sun", "next_rising"), "")) | timestamp_local }}.
{%- endif %}

For loop example getting 3 entity values:

{% for states in states | slice(3) -%}
  {% set state = states | first %}
  {%- if loop.first %}The {% elif loop.last %} and the {% else %}, the {% endif -%}
  {{ state.name | lower }} is {{state.state_with_unit}}
{%- endfor %}.
"""
    tmp = template.Template(demo_template_str, opp)

    result = tmp.async_render()
    assert "The temperature is 25" in result
    assert "is on" in result
    assert "sensor0" in result
    assert "sensor1" in result
    assert "sun" in result


async def test_slice_states(opp):
    """Test iterating states with a slice."""
    opp.states.async_set("sensor.test", "23")

    tpl = template.Template(
        "{% for states in states | slice(1) -%}{% set state = states | first %}{{ state.entity_id }}{%- endfor %}",
        opp,
    )
    assert tpl.async_render() == "sensor.test"


async def test_lifecycle(opp):
    """Test that we limit template render info for lifecycle events."""
    opp.states.async_set("sun.sun", "above", {"elevation": 50, "next_rising": "later"})
    for i in range(2):
        opp.states.async_set(f"sensor.sensor{i}", "on")
    opp.states.async_set("sensor.removed", "off")

    await opp.async_block_till_done()

    opp.states.async_set("sun.sun", "below", {"elevation": 60, "next_rising": "later"})
    for i in range(2):
        opp.states.async_set(f"sensor.sensor{i}", "off")

    opp.states.async_set("sensor.new", "off")
    opp.states.async_remove("sensor.removed")

    await opp.async_block_till_done()

    tmp = template.Template("{{ states | count }}", opp)

    info = tmp.async_render_to_info()
    assert info.all_states is False
    assert info.all_states_lifecycle is True
    assert info.rate_limit is None
    assert info.has_time is False

    assert info.entities == set()
    assert info.domains == set()
    assert info.domains_lifecycle == set()

    assert info.filter("sun.sun") is False
    assert info.filter("sensor.sensor1") is False
    assert info.filter_lifecycle("sensor.new") is True
    assert info.filter_lifecycle("sensor.removed") is True


async def test_template_timeout(opp):
    """Test to see if a template will timeout."""
    for i in range(2):
        opp.states.async_set(f"sensor.sensor{i}", "on")

    tmp = template.Template("{{ states | count }}", opp)
    assert await tmp.async_render_will_timeout(3) is False

    tmp2 = template.Template("{{ error_invalid + 1 }}", opp)
    assert await tmp2.async_render_will_timeout(3) is False

    tmp3 = template.Template("static", opp)
    assert await tmp3.async_render_will_timeout(3) is False

    tmp4 = template.Template("{{ var1 }}", opp)
    assert await tmp4.async_render_will_timeout(3, {"var1": "ok"}) is False

    slow_template_str = """
{% for var in range(1000) -%}
  {% for var in range(1000) -%}
    {{ var }}
  {%- endfor %}
{%- endfor %}
"""
    tmp5 = template.Template(slow_template_str, opp)
    assert await tmp5.async_render_will_timeout(0.000001) is True


async def test_lights(opp):
    """Test we can sort lights."""

    tmpl = """
          {% set lights_on = states.light|selectattr('state','eq','on')|map(attribute='name')|list %}
          {% if lights_on|length == 0 %}
            No lights on. Sleep well..
          {% elif lights_on|length == 1 %}
            The {{lights_on[0]}} light is on.
          {% elif lights_on|length == 2 %}
            The {{lights_on[0]}} and {{lights_on[1]}} lights are on.
          {% else %}
            The {{lights_on[:-1]|join(', ')}}, and {{lights_on[-1]}} lights are on.
          {% endif %}
    """
    states = []
    for i in range(10):
        states.append(f"light.sensor{i}")
        opp.states.async_set(f"light.sensor{i}", "on")

    tmp = template.Template(tmpl, opp)
    info = tmp.async_render_to_info()
    assert info.entities == set()
    assert info.domains == {"light"}

    assert "lights are on" in info.result()
    for i in range(10):
        assert f"sensor{i}" in info.result()


async def test_template_errors(opp):
    """Test template rendering wraps exceptions with TemplateError."""

    with pytest.raises(TemplateError):
        template.Template("{{ now() | rando }}", opp).async_render()

    with pytest.raises(TemplateError):
        template.Template("{{ utcnow() | rando }}", opp).async_render()

    with pytest.raises(TemplateError):
        template.Template("{{ now() | random }}", opp).async_render()

    with pytest.raises(TemplateError):
        template.Template("{{ utcnow() | random }}", opp).async_render()


async def test_state_attributes(opp):
    """Test state attributes."""
    opp.states.async_set("sensor.test", "23")

    tpl = template.Template(
        "{{ states.sensor.test.last_changed }}",
        opp,
    )
    assert tpl.async_render() == str(opp.states.get("sensor.test").last_changed)

    tpl = template.Template(
        "{{ states.sensor.test.object_id }}",
        opp,
    )
    assert tpl.async_render() == opp.states.get("sensor.test").object_id

    tpl = template.Template(
        "{{ states.sensor.test.domain }}",
        opp,
    )
    assert tpl.async_render() == opp.states.get("sensor.test").domain

    tpl = template.Template(
        "{{ states.sensor.test.context.id }}",
        opp,
    )
    assert tpl.async_render() == opp.states.get("sensor.test").context.id

    tpl = template.Template(
        "{{ states.sensor.test.state_with_unit }}",
        opp,
    )
    assert tpl.async_render() == 23

    tpl = template.Template(
        "{{ states.sensor.test.invalid_prop }}",
        opp,
    )
    assert tpl.async_render() == ""

    tpl = template.Template(
        "{{ states.sensor.test.invalid_prop.xx }}",
        opp,
    )
    with pytest.raises(TemplateError):
        tpl.async_render()


async def test_unavailable_states(opp):
    """Test watching unavailable states."""

    for i in range(10):
        opp.states.async_set(f"light.sensor{i}", "on")

    opp.states.async_set("light.unavailable", "unavailable")
    opp.states.async_set("light.unknown", "unknown")
    opp.states.async_set("light.none", "none")

    tpl = template.Template(
        "{{ states | selectattr('state', 'in', ['unavailable','unknown','none']) | map(attribute='entity_id') | list | join(', ') }}",
        opp,
    )
    assert tpl.async_render() == "light.none, light.unavailable, light.unknown"

    tpl = template.Template(
        "{{ states.light | selectattr('state', 'in', ['unavailable','unknown','none']) | map(attribute='entity_id') | list | join(', ') }}",
        opp,
    )
    assert tpl.async_render() == "light.none, light.unavailable, light.unknown"


async def test_legacy_templates(opp):
    """Test if old template behavior works when legacy templates are enabled."""
    opp.states.async_set("sensor.temperature", "12")

    assert (
        template.Template("{{ states.sensor.temperature.state }}", opp).async_render()
        == 12
    )

    await async_process_op_core_config(opp, {"legacy_templates": True})
    assert (
        template.Template("{{ states.sensor.temperature.state }}", opp).async_render()
        == "12"
    )


async def test_no_result_parsing(opp):
    """Test if templates results are not parsed."""
    opp.states.async_set("sensor.temperature", "12")

    assert (
        template.Template("{{ states.sensor.temperature.state }}", opp).async_render(
            parse_result=False
        )
        == "12"
    )

    assert (
        template.Template("{{ false }}", opp).async_render(parse_result=False)
        == "False"
    )

    assert (
        template.Template("{{ [1, 2, 3] }}", opp).async_render(parse_result=False)
        == "[1, 2, 3]"
    )


async def test_is_static_still_ast_evals(opp):
    """Test is_static still convers to native type."""
    tpl = template.Template("[1, 2]", opp)
    assert tpl.is_static
    assert tpl.async_render() == [1, 2]


async def test_result_wrappers(opp):
    """Test result wrappers."""
    for text, native, orig_type, schema in (
        ("[1, 2]", [1, 2], list, vol.Schema([int])),
        ("{1, 2}", {1, 2}, set, vol.Schema({int})),
        ("(1, 2)", (1, 2), tuple, vol.ExactSequence([int, int])),
        ('{"hello": True}', {"hello": True}, dict, vol.Schema({"hello": bool})),
    ):
        tpl = template.Template(text, opp)
        result = tpl.async_render()
        assert isinstance(result, orig_type)
        assert isinstance(result, template.ResultWrapper)
        assert result == native
        assert result.render_result == text
        schema(result)  # should not raise
        # Result with render text stringifies to original text
        assert str(result) == text
        # Result without render text stringifies same as original type
        assert str(template.RESULT_WRAPPERS[orig_type](native)) == str(
            orig_type(native)
        )


async def test_parse_result(opp):
    """Test parse result."""
    for tpl, result in (
        ('{{ "{{}}" }}', "{{}}"),
        ("not-something", "not-something"),
        ("2a", "2a"),
        ("123E5", "123E5"),
        ("1j", "1j"),
        ("1e+100", "1e+100"),
        ("0xface", "0xface"),
        ("123", 123),
        ("10", 10),
        ("123.0", 123.0),
        (".5", 0.5),
        ("0.5", 0.5),
        ("-1", -1),
        ("-1.0", -1.0),
        ("+1", 1),
        ("5.", 5.0),
        ("123_123_123", "123_123_123"),
        # ("+48100200300", "+48100200300"),  # phone number
        ("010", "010"),
        ("0011101.00100001010001", "0011101.00100001010001"),
    ):
        assert template.Template(tpl, opp).async_render() == result
