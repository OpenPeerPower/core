"""Script variables."""
from typing import Any, Dict, Mapping, Optional

from openpeerpower.core import OpenPeerPower, callback

from . import template


class ScriptVariables:
    """Class to hold and render script variables."""

    def __init__(self, variables: Dict[str, Any]):
        """Initialize script variables."""
        self.variables = variables
        self._has_template: Optional[bool] = None

    @callback
    def async_render(
        self,
        opp: OpenPeerPower,
        run_variables: Optional[Mapping[str, Any]],
        *,
        render_as_defaults: bool = True,
        limited: bool = False,
    ) -> Dict[str, Any]:
        """Render script variables.

        The run variables are used to compute the static variables.

        If `render_as_defaults` is True, the run variables will not be overridden.

        """
        if self._has_template is None:
            self._has_template = template.is_complex(self.variables)
            template.attach(opp, self.variables)

        if not self._has_template:
            if render_as_defaults:
                rendered_variables = dict(self.variables)

                if run_variables is not None:
                    rendered_variables.update(run_variables)
            else:
                rendered_variables = (
                    {} if run_variables is None else dict(run_variables)
                )
                rendered_variables.update(self.variables)

            return rendered_variables

        rendered_variables = {} if run_variables is None else dict(run_variables)

        for key, value in self.variables.items():
            # We can skip if we're going to override this key with
            # run variables anyway
            if render_as_defaults and key in rendered_variables:
                continue

            rendered_variables[key] = template.render_complex(
                value, rendered_variables, limited
            )

        return rendered_variables

    def as_dict(self) -> dict:
        """Return dict version of this class."""
        return self.variables
