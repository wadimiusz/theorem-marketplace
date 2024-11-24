import os
from datetime import datetime

from flask import Flask, redirect, render_template, request, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
db_password = os.environ["DATABASE_PASSWORD"]
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://theorem_user:{db_password}@localhost:5433/theorem_marketplace"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
