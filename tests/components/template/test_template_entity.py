"""Test template entity."""
import pytest

from openpeerpower.components.template import template_entity
from openpeerpower.helpers import template


async def test_template_entity_requires_opp_set():
    """Test template entity requires opp.to be set before accepting templates."""
    entity = template_entity.TemplateEntity()

    with pytest.raises(AssertionError):
        entity.add_template_attribute("_hello", template.Template("Hello"))

    entity.opp = object()
    entity.add_template_attribute("_hello", template.Template("Hello", None))

    tpl_with_opp = template.Template("Hello", entity.opp)
    entity.add_template_attribute("_hello", tpl_with_opp)

    # Because opp is set in `add_template_attribute`, both templates match `tpl_with_opp.
    assert len(entity._template_attrs.get(tpl_with_opp, [])) == 2
