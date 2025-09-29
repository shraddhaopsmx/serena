"""
Jinja2 template implementation for interprompt.

Security note:
This module provides template functionality for text-based prompts and
does not enable Jinja2's autoescape by default. When rendering content
that will be displayed in an HTML context, always use the 'escape_html'
filter to prevent XSS vulnerabilities:

Example: {{ user_content|escape_html }}
"""

from typing import Any

import jinja2
import jinja2.meta
import jinja2.nodes
import jinja2.visitor

from interprompt.util.class_decorators import singleton


class ParameterizedTemplateInterface:
    def get_parameters(self) -> list[str]: ...


@singleton
class _JinjaEnvProvider:
    def __init__(self) -> None:
        self._env: jinja2.Environment | None = None

    def get_env(self) -> jinja2.Environment:
        if self._env is None:
            # For prompts used in non-web contexts, we use autoescape=False (default),
            # but add a custom filter for escaping HTML when needed
            self._env = jinja2.Environment()
            # Add an 'escape_html' filter for cases where escaping is needed
            self._env.filters["escape_html"] = lambda s: jinja2.escape(s) if isinstance(s, str) else s
        return self._env


class JinjaTemplate(ParameterizedTemplateInterface):
    """A template implementation using Jinja2.

    For security when rendering user-provided content in HTML contexts,
    use the `escape_html` filter in your templates:

    Example: {{ user_content|escape_html }}
    """

    def __init__(self, template_string: str) -> None:
        self._template_string = template_string
        self._template = _JinjaEnvProvider().get_env().from_string(self._template_string)
        parsed_content = self._template.environment.parse(self._template_string)
        self._parameters = sorted(jinja2.meta.find_undeclared_variables(parsed_content))

    def render(self, **params: Any) -> str:
        """Renders the template with the given kwargs. You can find out which parameters are required by calling get_parameter_names()."""
        return self._template.render(**params)

    def get_parameters(self) -> list[str]:
        """A sorted list of parameter names that are extracted from the template string. It is impossible to know the types of the parameter
        values, they can be primitives, dicts or dict-like objects.

        :return: the list of parameter names
        """
        return self._parameters
