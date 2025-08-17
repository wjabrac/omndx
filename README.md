# OMNDX

## Overview

OMNDX is an experimental platform for orchestrating modular AI agents. It
provides a collection of lightweight components—planners, taggers, security
utilities, contribution tracking and simple user interfaces—that can be
combined into larger workflows. The codebase targets production readiness with
unit tests and metrics instrumentation for critical paths.

## Licensing & Commercial Use

OMNDX is AGPL-3.0 licensed for non-commercial use. All commercial use requires
a separate license. Contact abraczinskas@hotmail.com for details.

## Documentation

Additional documentation is available in the `docs/` directory, including
[Agent Forge](docs/agent_forge.md) which covers registering agent templates,
`symbolic_planner.md` describing goal planning and runtime helper guides. Run
`pytest` to execute the full test suite. Outstanding work items are tracked in
`docs/todo.md` and inline module TODOs covering telemetry, metrics, security,
and resiliency.
