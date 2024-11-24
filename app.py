from datetime import datetime

from flask import Flask, render_template

app = Flask(__name__)


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
