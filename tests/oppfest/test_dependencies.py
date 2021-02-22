"""Tests for.oppfest dependency finder."""
import ast

import pytest

from script.oppfest.dependencies import ImportCollector


@pytest.fixture
def mock_collector():
    """Fixture with import collector that adds all referenced nodes."""
    collector = ImportCollector(None)
    collector.unfiltered_referenced = set()
    collector._add_reference = collector.unfiltered_referenced.add
    return collector


def test_child_import(mock_collector):
    """Test detecting a child_import reference."""
    mock_collector.visit(
        ast.parse(
            """
from openpeerpower.components import child_import
"""
        )
    )
    assert mock_collector.unfiltered_referenced == {"child_import"}


def test_subimport(mock_collector):
    """Test detecting a subimport reference."""
    mock_collector.visit(
        ast.parse(
            """
from openpeerpower.components.subimport.smart_home import EVENT_ALEXA_SMART_HOME
"""
        )
    )
    assert mock_collector.unfiltered_referenced == {"subimport"}


def test_child_import_field(mock_collector):
    """Test detecting a child_import_field reference."""
    mock_collector.visit(
        ast.parse(
            """
from openpeerpower.components.child_import_field import bla
"""
        )
    )
    assert mock_collector.unfiltered_referenced == {"child_import_field"}


def test_renamed_absolute(mock_collector):
    """Test detecting a renamed_absolute reference."""
    mock_collector.visit(
        ast.parse(
            """
import openpeerpower.components.renamed_absolute as hue
"""
        )
    )
    assert mock_collector.unfiltered_referenced == {"renamed_absolute"}


def test.opp_components_var(mock_collector):
    """Test detecting a.opp_components_var reference."""
    mock_collector.visit(
        ast.parse(
            """
def bla.opp):
    opp.components.opp_components_var.async_do_something()
"""
        )
    )
    assert mock_collector.unfiltered_referenced == {.opp_components_var"}


def test.opp_components_class(mock_collector):
    """Test detecting a.opp_components_class reference."""
    mock_collector.visit(
        ast.parse(
            """
class Hello:
    def something(self):
        self.opp.components.opp_components_class.async_yo()
"""
        )
    )
    assert mock_collector.unfiltered_referenced == {.opp_components_class"}


def test_all_imports(mock_collector):
    """Test all imports together."""
    mock_collector.visit(
        ast.parse(
            """
from openpeerpower.components import child_import

from openpeerpower.components.subimport.smart_home import EVENT_ALEXA_SMART_HOME

from openpeerpower.components.child_import_field import bla

import openpeerpower.components.renamed_absolute as hue

def bla.opp):
    opp.components.opp_components_var.async_do_something()

class Hello:
    def something(self):
        self.opp.components.opp_components_class.async_yo()
"""
        )
    )
    assert mock_collector.unfiltered_referenced == {
        "child_import",
        "subimport",
        "child_import_field",
        "renamed_absolute",
         opp.components_var",
         opp.components_class",
    }
