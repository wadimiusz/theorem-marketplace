import os
import traceback
from datetime import datetime

import requests
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from web3 import Web3

app = Flask(__name__)
db_password = os.environ["DATABASE_PASSWORD"]
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://theorem_user:{db_password}@localhost:5433/theorem_marketplace"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

metamask_developer_key = os.environ["METAMASK_DEVELOPER_KEY"]
w3 = Web3(Web3.HTTPProvider(f"https://sepolia.infura.io/v3/{metamask_developer_key}"))


class Bounty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    theorem = db.Column(db.Text, nullable=False)
    bounty_amount = db.Column(db.Float, nullable=False)
    user_address = db.Column(db.String(42), nullable=False)
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
    found_bounties = Bounty.query.filter_by(status="open").all()
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
    bounty_amount = data.get("bounty_amount")
    transaction_hash = data.get("transaction_hash")
    user_address = data.get("user_address")

    # Validate input data
    if not all([theorem, bounty_amount, transaction_hash, user_address]):
        return jsonify({"error": "Missing data"}), 400

    # Verify the transaction
    try:
        tx = w3.eth.get_transaction(transaction_hash)
    except Exception as e:
        print("Error fetching transaction:", e)
        return jsonify({"error": "Invalid transaction hash"}), 400

    # Check if the transaction corresponds to the declareBounty function call
    # and that it was sent by the user_address
    if tx["from"].lower() != user_address.lower():
        return jsonify({"error": "Transaction sender does not match user address"}), 400

    # Additional verification: Check if the transaction was to the correct contract and method
    # For more advanced check, decode input data to verify method and parameters

    # TODO: Implement input data decoding and method verification if necessary

    # Create a new Bounty in the database
    new_bounty = Bounty(
        theorem=theorem,
        bounty_amount=bounty_amount,
        user_address=user_address,
        status="open",
    )
    db.session.add(new_bounty)
    db.session.commit()

    return jsonify({"message": "Bounty added successfully"}), 200


@app.route("/api/check_syntax", methods=["POST"])
def check_syntax():
    data = request.get_json()
    code = data.get("code")

    if not code:
        return jsonify({"success": False, "error": "No code provided"}), 400

    # Send the theorem to the external adapter for syntax checking
    try:
        response = requests.post(
            "http://127.0.0.1:8081/check-syntax", json={"code": code}
        )
        response_data = response.json()
        if response_data.get("success"):
            return jsonify({"success": True}), 200
        else:
            return (
                jsonify({"success": False, "message": response_data.get("stderr")}),
                200,
            )
    except Exception:
        print("Error communicating with the external adapter:", traceback.format_exc())
        return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
