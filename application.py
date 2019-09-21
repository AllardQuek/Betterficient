from cs50 import SQL
from flask import Flask, jsonify, redirect, render_template, request, session, flash
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

import datetime
import requests


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded when changes are made to them
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    sex_row = db.execute("SELECT sex FROM users WHERE id = :id", id=session['user_id'])
    sex = sex_row[0]["sex"]


    row = db.execute("SELECT username FROM users WHERE id = :id", id=session['user_id'])
    # for single row, remeber to index at 0 to get at the one and only item, THEN get its attribute
    my_username = row[0]["username"]
    rows = db.execute("SELECT * FROM feedbacks WHERE user_to = :user_to", user_to=my_username)
    return render_template("index.html", rows=rows, username=my_username, sex=sex)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # validate user input; all fields filled and password matches confirmation password
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirmation"):
            return apology("Please fill up all fields", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match", 400)

        # generate hash of user's password
        hash = generate_password_hash(request.form.get("password"))
        sex = request.form.get("sex")
        print(sex)

        # add data to db, if failed to insert return apology
        result = db.execute("INSERT INTO users (username, hash, sex) VALUES (:username, :hash, :sex)", username=request.form.get("username"), hash=hash, sex=sex)

        if not result:
            return apology("Sorry, username taken", 400)

        # do user a favour, log him in by storing their id in session["user_id"]
        user_id = db.execute("SELECT id FROM users WHERE username= :username", username = request.form.get("username"))
        session["user_id"] = user_id[0]["id"]

        # redirect to homepage
        flash('Registration successful!')
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # Validate user input
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Please provide a username", 400)
        elif not request.form.get("password"):
            return apology("Please enter a password", 400)

        # Check for match in db
        rows = db.execute("SELECT * FROM users WHERE username=:username", username=request.form.get("username"))
        print(rows)

        # if username doesn't exist, or password wrong
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Invalid username and/or password", 400)

        # Remember which uesr logged in, store id inside session["user_id"]
        session["user_id"] = rows[0]["id"]

        # if match, redirect to homepage
        flash('Login successful!')
        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/todo", methods=["GET", "POST"])
@login_required
def todo():

    # when user submits a task through form
    if request.method == "POST":

        if not request.form.get("task") or not request.form.get("deadline"):
            return apology("Please enter task/deadline", 400)

        addrow = db.execute("INSERT INTO tasks (task, deadline, userID) VALUES (:task, :deadline, :userID)", task=request.form.get("task"), deadline=request.form.get("deadline"), userID=session['user_id'])
        rows = db.execute("SELECT task, deadline FROM tasks WHERE userID= :id GROUP BY deadline", id=session['user_id'])
        print(rows)


        return render_template("todo.html", rows=rows)
        # how to settle the tick?? checkbox

    else:
        rows = db.execute("SELECT task, deadline FROM tasks WHERE userID= :id GROUP BY deadline", id=session['user_id'])
        print(rows)
        return render_template("todo.html", rows=rows)

@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "GET":
        users = db.execute("SELECT username FROM users")
        return render_template("feedback.html", users=users)
    else:
        # validate form input
        if not request.form.get("user_to") or not request.form.get("feedback") or not request.form.get("title"):
            return apology("Please fill in all fields", 400)

        row = db.execute("SELECT username FROM users WHERE id = :id", id=session['user_id'])
        my_username = row[0]["username"]
        user_to = request.form.get("user_to")
        feedback = request.form.get("feedback")
        title = request.form.get("title")

        # add new feedback to table
        new_feedback = db.execute("INSERT INTO feedbacks (user_from, user_to, feedback, datetime, title) VALUES (:user_from, :user_to, :feedback, :datetime, :title)",
                        user_from=my_username, user_to=user_to, feedback=feedback, datetime=datetime.datetime.now(), title=title)

        flash("Feedback sent!")
        return redirect("/feedback")

@app.route("/motivation")
@login_required
def motivation():

    r = requests.get('http://quotes.rest/qod.json')
    Quote = r.json()

    try:
        text = text = Quote["contents"]["quotes"][0]["quote"]
    except:
        text = Quote["error"]["message"]
    # print(Quote)
    # print(text)
    return render_template("motivation.html", text=text)