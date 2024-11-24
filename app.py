import os
from datetime import datetime

from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
db_password = os.environ["DATABASE_PASSWORD"]
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://theorem_user:{db_password}@/theorem_marketplace"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/declare_bounty", methods=["GET", "POST"])
def declare_bounty():
    return render_template("declare_bounty.html")


@app.route("/bounties")
def bounties():
    return render_template("bounties.html")


@app.route("/bounties/<int:bounty_id>", methods=["GET", "POST"])
def bounty_detail(bounty_id):
    return render_template("bounty_detail.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
