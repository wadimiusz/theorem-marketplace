import json
import os
import traceback
from datetime import datetime

import boto3
import requests
from botocore.exceptions import ClientError
from eth_account.messages import encode_defunct
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
    default_limits=["200 per day", "50 per hour"],
)

alchemy_api_key = os.environ["ALCHEMY_API_KEY"]
w3 = Web3(Web3.HTTPProvider(f"https://eth-sepolia.g.alchemy.com/v2/{alchemy_api_key}"))

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
    # Retrieve open bounties
    open_bounties = (
        Bounty.query.filter_by(status="open").order_by(Bounty.created_at.desc()).all()
    )
    # Retrieve closed bounties
    closed_bounties = (
        Bounty.query.filter(Bounty.status != "open")
        .order_by(Bounty.created_at.desc())
        .all()
    )
    return render_template(
        "bounties.html", open_bounties=open_bounties, closed_bounties=closed_bounties
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/bounties/<int:bounty_id>")
def bounty_detail(bounty_id):
    # Retrieve the specific bounty or return 404
    bounty = Bounty.query.get_or_404(bounty_id)
    return render_template("bounty_detail.html", bounty=bounty)


@app.route("/api/add_bounty", methods=["POST"])
@limiter.limit("20 per hour")
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

    if receipt.to != contract.address:
        return (
            jsonify({"error": "Transaction was not sent to the correct contract"}),
            400,
        )

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
@limiter.limit("20 per hour")
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
            return jsonify({"message": "Bounty already absent"}), 200
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
@limiter.limit("30 per hour")
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


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/api/contact", methods=["POST"])
@limiter.limit("5 per hour")
def submit_contact():
    data = request.get_json()
    subject = data.get("subject")
    message = data.get("message")
    email = data.get("email", "")  # Optional email field
    wallet_address = data.get("walletAddress")
    signature = data.get("signature")
    timestamp = data.get("timestamp")  # Get timestamp from frontend

    # Validate input data
    if not all([subject, message, wallet_address, signature, timestamp]):
        return jsonify({"error": "Missing required fields"}), 400

    # Verify signature using web3
    try:
        # Recreate the message that was signed
        message_to_verify = (
            f"Contact Form Submission\nWallet: {wallet_address}\nTimestamp: {timestamp}"
        )

        # Convert message to the format used by eth_sign
        message_hash = encode_defunct(text=message_to_verify)

        # Recover the address from the signature
        recovered_address = w3.eth.account.recover_message(
            message_hash, signature=signature
        )

        # Verify that the recovered address matches the claimed address
        if recovered_address.lower() != wallet_address.lower():
            print(
                f"Signature verification failed: {recovered_address} vs {wallet_address}"
            )
            return jsonify({"error": "Invalid signature"}), 403

    except Exception:
        print(f"Signature verification error: {traceback.format_exc()}")
        return jsonify({"error": "Failed to verify signature"}), 400

    # Format the email
    email_subject = f"[Theorem Marketplace] {subject}"

    email_body = f"""
New message from the Theorem Marketplace:

Subject: {subject}
From Wallet: {wallet_address}
{f"Contact Email: {email}" if email else "No email provided for reply"}

Message:
{message}

Signature verified: Yes
Timestamp: {datetime.fromtimestamp(int(timestamp)/1000).strftime('%Y-%m-%d %H:%M:%S UTC')}
    """

    # Get email configuration from environment variables
    admin_email = os.environ["ADMIN_EMAIL"]
    sender_email = os.environ["SENDER_EMAIL"]
    aws_region = os.environ["AWS_REGION"]

    try:
        # Create a new SES client
        ses_client = boto3.client("ses", region_name=aws_region)

        # Configure reply-to header if email was provided
        email_args = {
            "Destination": {
                "ToAddresses": [admin_email],
            },
            "Message": {
                "Body": {
                    "Text": {
                        "Charset": "UTF-8",
                        "Data": email_body,
                    },
                },
                "Subject": {
                    "Charset": "UTF-8",
                    "Data": email_subject,
                },
            },
            "Source": sender_email,
        }

        # Add Reply-To header if email was provided
        if email:
            email_args["ReplyToAddresses"] = [email]

        # Send the email using Amazon SES
        response = ses_client.send_email(**email_args)

        print(f"Email sent! Message ID: {response['MessageId']}")
        return jsonify({"message": "Contact form submitted successfully"}), 200

    except ClientError as e:
        error_message = e.response["Error"]["Message"]
        print(f"Error sending email: {error_message}")
        return jsonify({"error": "Failed to send your message. Please try again."}), 500
    except Exception:
        print(f"Unexpected error sending email: {traceback.format_exc()}")
        return (
            jsonify({"error": "An unexpected error occurred. Please try again."}),
            500,
        )


@app.errorhandler(429)
def ratelimit_handler(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Too Many Requests"}), 429
    return "Too Many Requests", 429


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
