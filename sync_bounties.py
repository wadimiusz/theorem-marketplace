import os
from datetime import datetime
from decimal import Decimal
from typing import TypedDict

from web3.datastructures import AttributeDict

from app import Bounty, app, contract, db, w3


class ClosedBountyProperties(TypedDict):
    requestTxHash: str
    value: int
    proof: str
    closed_at: datetime


class OpenBountyProperties(TypedDict):
    value: int
    created_at: datetime


def get_transaction_or_log_datetime(entity: AttributeDict) -> datetime:
    block = w3.eth.get_block(entity.blockNumber)
    return datetime.fromtimestamp(block.timestamp)


def get_open_bounty_properties(log: AttributeDict) -> OpenBountyProperties:
    return OpenBountyProperties(
        value=wei_to_ether(log.args.value),
        created_at=get_transaction_or_log_datetime(log),
    )


def get_closed_bounty_properties(log: AttributeDict) -> ClosedBountyProperties:

    transaction = w3.eth.get_transaction(log.args.requestTxHash.hex())
    _, decoded_input = contract.decode_function_input(transaction.input)

    return ClosedBountyProperties(
        requestTxHash=log.args.requestTxHash.hex(),
        value=wei_to_ether(log.args.value),
        proof=decoded_input["proof"],
        closed_at=get_transaction_or_log_datetime(transaction),
    )


def reconstruct_state(from_block: int = 0):
    """Reconstruct open / closed bounty mappings from emitted events."""
    declared_logs = contract.events.BountyDeclared.get_logs(from_block=from_block)
    paid_logs = contract.events.BountyPaid.get_logs(from_block=from_block)

    declared_theorems: set[str] = {log.args.theorem for log in declared_logs}
    closed_bounties: dict[str, ClosedBountyProperties] = {
        log.args.theorem: get_closed_bounty_properties(log) for log in paid_logs
    }
    open_bounties: dict[str, OpenBountyProperties] = {
        log.args.theorem: get_open_bounty_properties(log)
        for log in declared_logs
        if log.args.theorem in declared_theorems - closed_bounties.keys()
    }

    return open_bounties, closed_bounties


def wei_to_ether(wei: int) -> Decimal:
    return Decimal(w3.from_wei(wei, "ether"))


def sync_database(open_bounties: dict, closed_bounties: dict):
    """Persist reconstructed state into the Postgres database."""
    existing_bounties = {b.theorem: b for b in Bounty.query.all()}

    # Handle open bounties
    for theorem, open_bounty_properties in open_bounties.items():
        if theorem in existing_bounties:
            bounty = existing_bounties[theorem]
            bounty.status = "open"
            bounty.bounty_amount = open_bounty_properties["value"]
            bounty.updated_at = open_bounty_properties["created_at"]
        else:
            bounty = Bounty(
                theorem=theorem,
                bounty_amount=open_bounty_properties["value"],
                status="open",
                created_at=open_bounty_properties["created_at"],
            )
            db.session.add(bounty)

    # Handle closed bounties
    for theorem, closed_bounty_properties in closed_bounties.items():
        bounty = existing_bounties.get(theorem)
        if bounty:
            bounty.status = "closed"
            bounty.updated_at = closed_bounty_properties["closed_at"]
        else:
            bounty = Bounty(
                theorem=theorem,
                bounty_amount=closed_bounty_properties["value"],
                status="closed",
                proof=closed_bounty_properties["proof"],
                created_at=closed_bounty_properties["closed_at"],
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
