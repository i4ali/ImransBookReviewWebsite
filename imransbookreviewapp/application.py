import os
import requests

from flask import Flask, session, render_template, request, redirect, session, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    # if user logged in
    if session.get('logged_in') == True:
        return render_template("main.html")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for("index"))


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("name")
    password = request.form.get("password")
    # if user doesn't exist in database, add him
    if db.execute("SELECT * from users where name = :name", {"name": name}).rowcount == 0:
        db.execute("INSERT INTO users(name,password) VALUES(:name,:password)", {"name": name, "password": password})
        db.commit()
    # set logged_in variable to true
    session['logged_in'] = True
    return redirect(url_for("index"))

@app.route("/search", methods=["POST"])
def books():
    search = request.form.get("search")
    # search doesnt return any result
    if db.execute("SELECT * from books where isbn = :search", {"search":search}).rowcount == 0:
        return render_template("error.html", text="no results found")
    books=db.execute("SELECT * from books where isbn = :search", {"search": search}).fetchall()
    return render_template("books.html", books=books)





if __name__ == '__main__':
    app.run(host='0.0.0.0')