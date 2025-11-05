import os
from datetime import datetime
from decimal import Decimal

from app import Bounty, app, contract, db, w3


def reconstruct_state(from_block: int = 0):
    """Reconstruct open / closed bounty mappings from emitted events."""
    declared_logs = contract.events.BountyDeclared.get_logs(from_block=from_block)
    paid_logs = contract.events.BountyPaid.get_logs(from_block=from_block)

    # Combine and sort chronologically
    all_logs = declared_logs + paid_logs
    # Sort by blockNumber then logIndex to keep deterministic order
    all_logs.sort(key=lambda log: (log["blockNumber"], log["logIndex"]))

    open_bounties = {}
    closed_bounties = {}

    for log in all_logs:
        # web3 v6 uses "event" attribute, but we already know by source
        # We'll inspect the event signature by dict keys
        if "value" in log["args"] and "theorem" in log["args"]:
            if "requestTxHash" in log["args"]:
                # This is BountyPaid
                theorem = log["args"]["theorem"]
                closed_bounties[theorem] = log["args"]["requestTxHash"].hex()
                open_bounties.pop(theorem, None)
            else:
                # BountyDeclared
                theorem = log["args"]["theorem"]
                value = int(log["args"]["value"])
                open_bounties[theorem] = open_bounties.get(theorem, 0) + value

    return open_bounties, closed_bounties


def wei_to_ether(wei: int) -> Decimal:
    return Decimal(w3.from_wei(wei, "ether"))


def sync_database(open_bounties: dict, closed_bounties: dict):
    """Persist reconstructed state into the Postgres database."""
    existing_bounties = {b.theorem: b for b in Bounty.query.all()}

    # Handle open bounties
    for theorem, wei_val in open_bounties.items():
        ether_val = float(wei_to_ether(wei_val))
        if theorem in existing_bounties:
            bounty = existing_bounties[theorem]
            bounty.status = "open"
            bounty.bounty_amount = ether_val
            bounty.updated_at = datetime.utcnow()
        else:
            bounty = Bounty(
                theorem=theorem,
                bounty_amount=ether_val,
                status="open",
                created_at=datetime.utcnow(),
            )
            db.session.add(bounty)

    # Handle closed bounties
    for theorem, req_tx_hash in closed_bounties.items():
        bounty = existing_bounties.get(theorem)
        if bounty:
            bounty.status = "closed"
            bounty.updated_at = datetime.utcnow()
            # Optionally store requestTxHash in proof field if proof is empty
            if not bounty.proof:
                bounty.proof = f"requestTxHash: {req_tx_hash}"
        else:
            # Closed bounty not present – create with zero amount
            bounty = Bounty(
                theorem=theorem,
                bounty_amount=0.0,
                status="closed",
                proof=f"requestTxHash: {req_tx_hash}",
                created_at=datetime.utcnow(),
            )
            db.session.add(bounty)

    # Any theorem not in open or closed should be considered orphaned – we leave untouched.
    db.session.commit()


if __name__ == "__main__":
    FROM_BLOCK = int(os.getenv("SYNC_FROM_BLOCK", "0"))
    with app.app_context():
        # Ensure all tables exist before we attempt to sync.
        db.create_all()
        open_bounties, closed_bounties = reconstruct_state(FROM_BLOCK)
        sync_database(open_bounties, closed_bounties)
        print(
            f"Sync completed – Open: {len(open_bounties)}, Closed: {len(closed_bounties)} entries processed."
        )
