# Production TODOs

This document enumerates outstanding work required for a production-ready OMNDX platform. Each area lists tasks around telemetry, metrics, security, and resiliency.

## Agents
- Telemetry: unify agent logging and trace contexts.
- Metrics: benchmark throughput and accuracy of each agent.
- Security: validate inputs and enforce sandboxed execution.
- Resiliency: add retries and circuit breakers for agent failures.

## Contribution & Access Control
- Telemetry: audit credit changes and access decisions.
- Metrics: expose credit consumption rates and trust score trends.
- Security: protect stored balances and policies from tampering.
- Resiliency: replicate trackers and gates for high availability.

## Mesh Networking
- Telemetry: trace peer connections and message routing.
- Metrics: monitor bandwidth, latency, and node counts.
- Security: encrypt traffic and verify peer identities.
- Resiliency: handle peer churn, retries, and state recovery.

## Security Modules
- Telemetry: centralize alerts from filters and sandboxes.
- Metrics: track incidents and response times.
- Security: migrate toy implementations to hardened libraries.
- Resiliency: support key rotation and fail-closed policies.

## Runtime & UI
- Telemetry: standardize event reporting across entry points and interfaces.
- Metrics: measure startup time, request latency, and user interactions.
- Security: sandbox user-provided data and enforce auth.
- Resiliency: provide graceful shutdown and offline modes.

## Storage
- Telemetry: log data access and mutation events.
- Metrics: collect storage latency and capacity stats.
- Security: encrypt data at rest and during transport.
- Resiliency: implement backups and replication.

