import json
import os
import traceback
from datetime import datetime

import requests
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql.psycopg2 import logger
from web3 import Web3

app = Flask(__name__)
db_password = os.environ["DATABASE_PASSWORD"]
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://theorem_user:{db_password}@theorem_postgres:5432/theorem_marketplace"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

metamask_developer_key = os.environ["METAMASK_DEVELOPER_KEY"]
w3 = Web3(Web3.HTTPProvider(f"https://sepolia.infura.io/v3/{metamask_developer_key}"))

with open("ABI.json") as f:
    contract_ABI = json.load(f)

contract = w3.eth.contract(address=os.environ["CONTRACT_ADDRESS"], abi=contract_ABI)


class Bounty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    theorem = db.Column(db.Text, unique=True, nullable=False)  # Make theorem unique
    bounty_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="open")
    proof = db.Column(db.Text, nullable=True)  # New field to store the proof
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


@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/declare_bounty", methods=["GET", "POST"])
def declare_bounty():
    if request.method == "POST":
        theorem = request.form.get("theorem")
        bounty_amount = request.form.get("bounty_amount")

        if not theorem or not bounty_amount:
            error = "Please fill out all fields."
            return render_template("declare_bounty.html", error=error)

        try:
            bounty_amount = float(bounty_amount)
        except ValueError:
            error = "Please enter a valid bounty amount."
            return render_template("declare_bounty.html", error=error)

        # Create a new bounty
        new_bounty = Bounty(theorem=theorem, bounty_amount=bounty_amount)
        db.session.add(new_bounty)
        db.session.commit()

        # Redirect to the bounties list
        return redirect(url_for("bounties"))
    else:
        return render_template("declare_bounty.html")


@app.route("/bounties")
def bounties():
    # Retrieve all open bounties
    found_bounties = Bounty.query.all()
    return render_template("bounties.html", bounties=found_bounties)


@app.route("/bounties/<int:bounty_id>")
def bounty_detail(bounty_id):
    # Retrieve the specific bounty or return 404
    bounty = Bounty.query.get_or_404(bounty_id)
    return render_template("bounty_detail.html", bounty=bounty)


@app.route("/api/add_bounty", methods=["POST"])
def add_bounty():
    data = request.get_json()
    theorem = data.get("theorem")
    transaction_hash = data.get("transaction_hash")

    # Validate input data
    if not all([theorem, transaction_hash]):
        return jsonify({"error": "Missing data"}), 400

    # Verify the transaction
    try:
        w3.eth.get_transaction(transaction_hash)
    except Exception as e:
        print("Error fetching transaction:", e)
        return jsonify({"error": "Invalid transaction hash"}), 400

    # Ensure the transaction was successful
    receipt = w3.eth.get_transaction_receipt(transaction_hash)
    if receipt.status != 1:
        return jsonify({"error": "Transaction failed"}), 400

    # Call the smart contract to get the latest bounty amount
    try:
        # Query the current bounty amount from the smart contract
        bounty_amount_wei = contract.functions.theoremBounties(theorem).call()
        logger.info(f"{bounty_amount_wei = }")
        bounty_amount_ether = w3.from_wei(
            bounty_amount_wei, "ether"
        )  # Convert to Ether
    except Exception:
        logger.error(traceback.format_exc())
        return jsonify({"message": "Failed to sync with the smart contract"}), 500

    # Sync with the database
    try:
        existing_bounty = Bounty.query.filter_by(theorem=theorem).first()
        if existing_bounty:
            # Update the existing bounty amount
            existing_bounty.bounty_amount = float(bounty_amount_ether)
            existing_bounty.updated_at = datetime.utcnow()
            action_name = "modified"
        else:
            # Add a new bounty entry
            new_bounty = Bounty(
                theorem=theorem, bounty_amount=float(bounty_amount_ether)
            )
            db.session.add(new_bounty)
            action_name = "created"
        db.session.commit()
    except Exception:
        logger.error(traceback.format_exc())
        return jsonify({"error": "Failed to update the database"}), 500

    return jsonify({"message": f"Bounty {action_name} successfully"}), 200


@app.route("/api/close_bounty", methods=["POST"])
def close_bounty():
    data = request.get_json()
    theorem = data.get("theorem")
    proof = data.get("proof")
    # Optionally, include additional verification data such as a signature or API key

    # Validate input data
    if not all([theorem, proof]):
        return jsonify({"error": "Missing data"}), 400

    # Find the bounty in the database
    try:
        bounty = Bounty.query.filter_by(theorem=theorem).first()
        if not bounty:
            return jsonify({"error": "Bounty not found"}), 404
    except Exception:
        logger.error(traceback.format_exc())
        return jsonify({"error": "Database error"}), 500

    # Update the bounty status and store the proof
    try:
        bounty.status = "closed"
        bounty.proof = proof
        bounty.updated_at = datetime.utcnow()
        db.session.commit()
    except Exception:
        logger.error(traceback.format_exc())
        return jsonify({"error": "Failed to update the bounty"}), 500

    return jsonify({"message": "Bounty closed successfully"}), 200


@app.route("/api/check_syntax", methods=["POST"])
def check_syntax():
    data = request.get_json()
    code = data.get("code")

    if not code:
        return jsonify({"success": False, "error": "No code provided"}), 400

    # Send the theorem to the external adapter for syntax checking
    try:
        response = requests.post(
            "http://safe-verify-adapter:8080/check-syntax", json={"code": code}
        )
        response_data = response.json()
        if response_data.get("success"):
            return jsonify({"success": True}), 200
        else:
            return (
                jsonify({"success": False, "message": response_data.get("stdout")}),
                200,
            )
    except Exception:
        print("Error communicating with the external adapter:", traceback.format_exc())
        return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
