import os
import datetime
from functools import wraps
from flask import *
from flask_bootstrap import Bootstrap
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import utils
import stitch

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["MONGO_URI"] = os.getenv("MONGO_URI")

Bootstrap(app)
db = PyMongo(app).db


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # redirect if not logged in
        if "session_id" not in session:
            return redirect(url_for("login"))

        session_id = db.session_ids.find_one(
            {"session_id": session["session_id"]})

        # redirect if session not found or has expired
        if session_id is None or session_id["expiry_date"] <= datetime.datetime.now():
            session.clear()
            return redirect(url_for("login"))

        user_details = db.users.find_one({"email": session_id["user_email"]})

        # redirect if user not found
        if user_details is None:
            session.clear()
            return redirect(url_for("login"))

        return f(user_details, *args, **kwargs)

    return decorated


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/auth/register/")
def register():
    return render_template("register.html")


@app.route("/auth/register/", methods=["POST"])
def create_user():
    email = request.form.get("email", "").lower()
    username = request.form.get("username", "").lower()
    password = request.form.get("password", "")

    # check for empty params
    if "" in [email, username, password]:
        flash("registration form fields cannot be empty", "danger")
        return redirect(url_for("register"))

    # check for data conflicts
    query = {"$or": [{"email": email, "username": username}]}
    if db.users.find_one(query) is not None:
        flash("you cannot create multiple accounts with the same details", "danger")
        return redirect(url_for("register"))

    db.users.insert_one({
        "email": email,
        "username": username,
        "password": utils.hash_password(password)
    })
    flash("you have successfully created your StitchPay account", "success")
    return redirect(url_for("login"))


@app.route("/auth/login/")
def login():
    if "session_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/auth/login/", methods=["POST"])
def authenticate_user():
    email = request.form.get("email", "").lower()
    password = request.form.get("password", "")

    # check for empty params
    if "" in [email, password]:
        flash("login form fields cannot be empty", "danger")
        return redirect(url_for("login"))

    # fetch user details
    user_details = db.users.find_one({"email": email})

    # validate user info
    if user_details is None or not utils.verify_hash(password, user_details["password"]):
        flash("you have supplied invalid login credentials", "danger")
        return redirect(url_for("login"))

    # generate session id
    session_id = utils.gensalt().decode()
    session["session_id"] = session_id
    db.session_ids.insert_one({
        "session_id": session_id,
        "user_email": user_details["email"],
        "expiry_date": datetime.datetime.now() + datetime.timedelta(days=3)
    })
    return redirect(url_for("dashboard"))


@app.route("/dashboard/")
@login_required
def dashboard(user_details):
    return "dashboard"


@app.route("/pay/<string:username>/", methods=["GET", "POST"])
def pay(username):
    username = username.lower()

    # throw error is username not found
    if db.users.find_one({"username": username}) is None:
        abort(404)

    if request.method == "POST":
        amount = request.form.get("amount", "0")
        reference = request.form.get("reference", "stitch test")

        # redirect if reference is more than 12 chars
        if len(reference) > 12:
            flash("payment reference cannot exceed 12 characters", "danger")
            return redirect(url_for("pay", username=username))

        # redirect is amount is not a valid number
        try:
            amount = int(amount)
        except ValueError:
            flash("please supply a valid transaction amount", "danger")
            return redirect(url_for("pay", username=username))

        # redirect if the amount is lower than 100 NGN
        if amount < 100:
            flash("you cannot transact lower than 100 NGN", "danger")
            return redirect(url_for("pay", username=username))

        payment_url = stitch.generate_pay_page()
        return redirect(payment_url)

    return render_template("pay.html", username=username)


if __name__ == "__main__":
    app.run(debug=True)
