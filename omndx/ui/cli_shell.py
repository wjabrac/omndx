"""Interactive command shell for OMNDX.

This module provides a small wrapper around :mod:`cmd` offering a few
commands that exercise the :class:`~omndx.core.TagLogger`.  The shell is
primarily intended for demonstrations and tests; it is intentionally
minimal yet showcases command parsing, tab completion and integration
with the core instrumentation utilities.
"""

from __future__ import annotations

import cmd
from typing import Iterable, List, Optional

from ..core import TagLogger


class CliShell(cmd.Cmd):
    """Simple interactive shell.

    Parameters
    ----------
    logger:
        Optional :class:`TagLogger` instance used for recording
        instrumentation data.  When omitted a new logger named ``"cli"``
        is created.
    """

    intro = "OMNDX CLI. Type help or ? to list commands."
    prompt = "(omndx) "

    def __init__(self, logger: Optional[TagLogger] = None) -> None:
        super().__init__()
        self.logger = logger or TagLogger("cli")
        self.started = False

        # Set of available command names used for completion.
        self._commands: List[str] = ["start", "metrics", "exit", "quit"]

    # ------------------------------------------------------------------
    # Command implementations
    # ------------------------------------------------------------------
    def do_start(self, arg: str) -> None:
        """Start the (mock) orchestration layer."""

        if not self.started:
            self.logger.info("starting", tag="start")
            self.started = True
            print("started")
        else:
            print("already started")

    def do_metrics(self, arg: str) -> None:
        """Display current instrumentation metrics."""

        metrics = self.logger.get_metrics()
        print(metrics)

    def do_exit(self, arg: str) -> bool:  # pragma: no cover - thin wrapper
        """Exit the shell."""

        print("bye")
        return True

    # Alias ``quit`` to ``exit``.
    do_quit = do_exit

    # ------------------------------------------------------------------
    # Tab completion helpers
    # ------------------------------------------------------------------
    def completenames(self, text: str, *ignored: Iterable[str]) -> List[str]:
        """Return command name completions for *text*."""

        return [name for name in self._commands if name.startswith(text)]


def run_shell(logger: Optional[TagLogger] = None) -> None:
    """Launch the interactive shell."""

    CliShell(logger).cmdloop()


__all__ = ["CliShell", "run_shell"]

