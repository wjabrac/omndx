"""OMNDX platform package.

This package provides a plug-and-play LLM mount and agent system. The
current repository contains only scaffolding. Each submodule outlines the
responsibilities and integration points required for a production-ready
platform as described in the architecture blueprint.
"""

from .agents.core_agent import CoreAgent  # re-export for convenience

__all__ = ["__version__", "CoreAgent"]
__version__ = "0.1.0"


