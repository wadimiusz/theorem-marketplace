#!/usr/bin/env python3
"""Estimate the Chainlink node's Infura credit burn from its Prometheus metrics.

Run from the repo root on your machine:

    ssh root@216.128.145.16 'docker exec chainlink curl -s localhost:6688/metrics' \
        | python3 scripts/infura_usage.py

Counters are cumulative since the node started, so a fresh restart overstates the
rate (startup backfill); the estimate settles after an hour or so of uptime.
"""

import re
import sys
import time

# https://docs.infura.io/get-started/pricing/credit-cost/
FREE_TIER_CREDITS_PER_DAY = 3_000_000
NEW_HEADS_EVENT_CREDITS = 50
# rpcCallName (the node's Go client method) -> credits of the JSON-RPC call it makes.
# CallContext is a generic wrapper; in steady state it carries eth_getBlockByNumber,
# eth_getBlockByHash and web3_clientVersion, which all cost the default 80.
CALL_CREDITS = {
    "FilterLogs": 255,
    "EstimateGas": 300,
    "EthSubscribe": 5,
    "SubscribeFilterLogs": 5,
}
DEFAULT_CALL_CREDITS = 80

SAMPLE = re.compile(r"^(\w+)(?:\{([^}]*)\})? (\S+)$")
LABEL = re.compile(r'(\w+)="([^"]*)"')


def parse(text: str) -> list[tuple[str, dict[str, str], float]]:
    samples = []
    for line in text.splitlines():
        if match := SAMPLE.match(line):
            name, labels, value = match.groups()
            samples.append((name, dict(LABEL.findall(labels or "")), float(value)))
    return samples


def verdict(credits_per_day: float, uptime_hours: float) -> str:
    """One-line answer to "is it safe to stay on Infura's free tier?"."""
    if uptime_hours < 1:
        return (
            "Too early to judge: startup backfill inflates the rate for the first hour."
        )
    share = credits_per_day / FREE_TIER_CREDITS_PER_DAY
    # Hitting the cap means HTTP 402 until 00:00 UTC, i.e. the oracle silently stops,
    # so keep headroom for batch elements and anything else these metrics can't see.
    if share < 0.7:
        return "OK for the free tier."
    if share < 0.9:
        return "Tight: fits the free tier, but a busy day could hit the cap."
    return "Not safe: at this rate the oracle may stop answering before the day ends."


def main() -> None:
    samples = parse(sys.stdin.read())
    if not samples:
        sys.exit("No metrics on stdin — is the chainlink container running?")

    start = next(v for n, _, v in samples if n == "process_start_time_seconds")
    uptime_s = time.time() - start
    per_day = 86400 / uptime_s

    # Only the primary (WS) node is Infura; SendOnly nodes are other providers.
    calls: dict[str, float] = {}
    for name, labels, value in samples:
        if (
            name == "evm_pool_rpc_node_rpc_call_time_count"
            and labels["isSendOnly"] == "false"
        ):
            calls[labels["rpcCallName"]] = calls.get(labels["rpcCallName"], 0) + value

    # One newHeads subscription feeds the node pool, another the head tracker.
    new_heads = sum(
        v
        for n, _, v in samples
        if n in ("pool_rpc_node_num_seen_blocks", "head_tracker_heads_received")
    )

    rows = [
        (name, count, count * CALL_CREDITS.get(name, DEFAULT_CALL_CREDITS) * per_day)
        for name, count in calls.items()
    ]
    rows.append(
        ("newHeads events", new_heads, new_heads * NEW_HEADS_EVENT_CREDITS * per_day)
    )
    rows.sort(key=lambda row: -row[2])
    total = sum(row[2] for row in rows)

    print(f"Node uptime: {uptime_s / 3600:.1f} h\n")
    print(f"{'call':24} {'since start':>12} {'credits/day':>12}")
    for name, count, credits in rows:
        mark = " (lower bound)" if name == "BatchCallContext" else ""
        print(f"{name:24} {count:12.0f} {credits:12,.0f}{mark}")
    print(
        f"\nTOTAL ≈ {total / 1e6:.2f}M credits/day "
        f"= {total / FREE_TIER_CREDITS_PER_DAY:.0%} of the free tier"
    )
    if message := verdict(total, uptime_s / 3600):
        print(message)


if __name__ == "__main__":
    main()
