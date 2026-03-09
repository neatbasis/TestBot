"""Deprecated compatibility shim for answer rendering boundaries.

Canonical runtime imports must use :mod:`testbot.answer_rendering`.
This shim remains only for external compatibility with legacy references to
``src/testbot/answer_render.py`` and should not receive new logic.
"""

from __future__ import annotations

from testbot.answer_rendering import RenderedAnswer, render_answer

__all__ = ["RenderedAnswer", "render_answer"]
