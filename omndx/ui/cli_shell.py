"""Minimal interactive shell.

TODO:
- Telemetry: capture command usage patterns.
- Metrics: record session durations and error counts.
- Security: sandbox executed commands.
- Resiliency: handle unexpected input gracefully.
"""
from __future__ import annotations


def repl() -> None:
    print("OMNDX shell. Type 'exit' to quit.")
    while True:
        cmd = input("> ")
        if cmd.strip().lower() in {"exit", "quit"}:
            break
        print(f"unknown command: {cmd}")


if __name__ == "__main__":  # pragma: no cover
    repl()
