import os
from flask import *
from flask_bootstrap import Bootstrap
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import utils

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["MONGO_URI"] = os.getenv("MONGO_URI")

Bootstrap(app)
db = PyMongo(app).db.stitchpay


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/auth/register/")
def register():
    return render_template("register.html")


@app.route("/auth/register/", methods=["POST"])
def create_user():
    email = request.form.get("email")
    username = request.form.get("username")
    password = request.form.get("password")

    # check for empty params
    if None in [email, username, password]:
        flash("registration form fields cannot be empty", "danger")
        return redirect(url_for("register"))

    db.insert_one({
        "email": email,
        "username": username,
        "password": utils.hash_password(password)
    })
    flash("you have successfully created a stitchpay account", "success")
    return redirect(url_for("login"))


@app.route("/auth/login/")
def login():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)
