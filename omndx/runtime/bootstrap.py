"""Runtime bootstrap utilities.

This module initialises application configuration, logging and the
primary :mod:`asyncio` event loop used by agents. The configuration is
loaded from ``settings.toml`` located next to this file. Logging is
configured using a basic stream handler honouring the ``logging.level``
field from the configuration file.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Tuple

try:  # Python 3.11+
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - fallback for older versions
    import tomli as tomllib  # type: ignore[import-not-found]

# ---------------------------------------------------------------------------
# Configuration handling
# ---------------------------------------------------------------------------
DEFAULT_CONFIG_PATH = Path(__file__).with_name("settings.toml")


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load configuration from *path* if it exists.

    Parameters
    ----------
    path:
        The path to a TOML configuration file.

    Returns
    -------
    dict
        Parsed configuration or an empty dictionary when the file is
        missing or invalid.
    """

    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except FileNotFoundError:
        return {}
    except Exception:  # pragma: no cover - defensive safeguard
        return {}


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def init_logging(config: Dict[str, Any]) -> logging.Logger:
    """Initialise logging according to *config* and return a logger.

    The configuration may contain a ``level`` entry (e.g. ``"INFO"``).
    """

    level_name = str(config.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    return logging.getLogger("omndx.runtime")


# ---------------------------------------------------------------------------
# Event loop helpers
# ---------------------------------------------------------------------------

def create_event_loop() -> asyncio.AbstractEventLoop:
    """Create and set the main asyncio event loop."""

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


# ---------------------------------------------------------------------------
# Public bootstrap API
# ---------------------------------------------------------------------------

def bootstrap(
    config_path: Path | None = None,
) -> Tuple[Dict[str, Any], logging.Logger, asyncio.AbstractEventLoop]:
    """Bootstrap the runtime environment.

    Parameters
    ----------
    config_path:
        Optional path to a configuration file. When omitted the default
        ``settings.toml`` next to this module is used.

    Returns
    -------
    tuple
        A tuple of ``(config, logger, event_loop)``.
    """

    cfg_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    config = load_config(cfg_path)
    logger = init_logging(config.get("logging", {}))
    loop = create_event_loop()
    logger.info("Runtime initialised")
    return config, logger, loop


__all__ = ["bootstrap", "create_event_loop", "init_logging", "load_config"]
