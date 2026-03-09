"""Compatibility shim for answer rendering boundaries.

This module exists to provide stable enforcement-point naming for governance
artifacts that reference ``src/testbot/answer_render.py``.
"""

from __future__ import annotations

from testbot.answer_rendering import RenderedAnswer, render_answer

__all__ = ["RenderedAnswer", "render_answer"]
