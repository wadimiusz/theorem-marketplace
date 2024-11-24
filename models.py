from datetime import datetime

from app import db


class Bounty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    theorem = db.Column(db.Text, nullable=False)
    bounty_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)


class ProofSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bounty_id = db.Column(db.Integer, db.ForeignKey("bounty.id"), nullable=False)
    user_address = db.Column(db.String(42), nullable=False)
    proof = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)
    verification_result = db.Column(db.String(20), default="pending")
