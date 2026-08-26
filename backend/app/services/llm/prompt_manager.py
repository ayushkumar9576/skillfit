"""
app/services/llm/prompt_manager.py
----------------------------------
Prompt template loading and rendering for the SkillFit LLM Integration Layer
(Phase 3.6).

Templates live in ``app/prompts/<name>.txt`` (path resolved relative to this
package, not the process CWD). Loaded templates are cached in memory so a
repeated request never re-reads disk.

Rendering uses the standard-library ``str.format`` — **no Jinja2 or any other
external templating dependency**. Because ``str.format`` treats ``{`` / ``}``
specially, prompt files must escape literal braces (e.g. JSON examples) as
``{{`` / ``}}``.
"""

import logging
import os
from typing import Dict, Optional

from app.services.llm.exceptions import PromptNotFoundError, PromptRenderError

logger = logging.getLogger(__name__)

# app/services/llm/prompt_manager.py -> app/services/llm -> app/services -> app
_APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_PROMPTS_DIR = os.path.join(_APP_DIR, "prompts")


class PromptManager:
    """
    Loads, caches, and renders prompt templates from a prompts directory.

    Versioning-ready: ``version`` selects ``<name>.<version>.txt`` when given,
    otherwise ``<name>.txt``.
    """

    def __init__(self, prompts_dir: str = DEFAULT_PROMPTS_DIR) -> None:
        self._prompts_dir = prompts_dir
        self._cache: Dict[str, str] = {}

    # -- internal helpers ---------------------------------------------------

    def _filename(self, name: str, version: Optional[str] = None) -> str:
        return f"{name}.{version}.txt" if version else f"{name}.txt"

    def _path(self, name: str, version: Optional[str] = None) -> str:
        return os.path.join(self._prompts_dir, self._filename(name, version))

    # -- public API ---------------------------------------------------------

    def load(self, name: str, version: Optional[str] = None) -> str:
        """
        Return the raw template text for ``name`` (optionally versioned).

        Cached after first read.

        Raises:
            PromptNotFoundError: if the template file does not exist or is unreadable.
        """
        key = self._filename(name, version)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        path = self._path(name, version)
        if not os.path.isfile(path):
            raise PromptNotFoundError(
                f"Prompt template {key!r} not found in prompts directory."
            )
        try:
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
        except OSError as exc:
            raise PromptNotFoundError(
                f"Prompt template {key!r} could not be read."
            ) from exc

        self._cache[key] = content
        logger.debug("Loaded prompt template %s (%d chars).", key, len(content))
        return content

    def render(self, name: str, version: Optional[str] = None, **kwargs) -> str:
        """
        Load a template and substitute ``{placeholder}`` fields via ``str.format``.

        Literal braces in the template must be escaped as ``{{`` / ``}}``.

        Args:
            name:    Template name.
            version: Optional template version.
            **kwargs: Values for the template's placeholders.

        Returns:
            The rendered prompt string.

        Raises:
            PromptNotFoundError: if the template does not exist.
            PromptRenderError:   if a required placeholder is missing (or an
                invalid/positional field is referenced).
        """
        template = self.load(name, version)
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError) as exc:
            raise PromptRenderError(
                f"Prompt {self._filename(name, version)!r} is missing a required "
                f"placeholder: {exc}."
            ) from exc

    def exists(self, name: str, version: Optional[str] = None) -> bool:
        """
        Return ``True`` if the template is available (cached or present on disk),
        ``False`` otherwise. Never raises — intended for pre-flight validation
        and health checks before an analyzer runs.
        """
        if self._filename(name, version) in self._cache:
            return True
        return os.path.isfile(self._path(name, version))

    # Alias — some call sites read more naturally as `has_prompt(...)`.
    has_prompt = exists


# Module-level default instance pointing at app/prompts. Constructing it does
# NOT read disk (the cache fills lazily on first load), so importing this module
# is side-effect free.
default_prompt_manager = PromptManager()
