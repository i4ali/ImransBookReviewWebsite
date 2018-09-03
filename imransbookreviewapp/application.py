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
    if session.get('logged_in'):
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
    # TODO instead of seeing if doesnt exists in DB and add him/her directly create a registration
    # page and have user registered there
    if db.execute("SELECT * from users where name = :name", {"name": name}).rowcount == 0:
        db.execute("INSERT INTO users(name,password) VALUES(:name,:password)", {"name": name, "password": password})
        db.commit()
    # set logged_in variable to true
    session['logged_in'] = True
    session['user'] = name
    return redirect(url_for("index"))


@app.route("/search", methods=["POST"])
def books():
    search = request.form.get("search")
    # search doesnt return any result
    #TODO add search by title, author
    if db.execute("SELECT * from books where isbn = :search", {"search":search}).rowcount == 0:
        return render_template("error.html", text="no results found")
    books = db.execute("SELECT * from books where isbn = :search", {"search": search}).fetchall()
    return render_template("books.html", books=books)


@app.route("/bookdetails/<string:title>", methods=["GET", "POST"])
def bookdetails(title):
    if request.method == "POST":
        review = request.form.get("review")
        user_id = db.execute("SELECT id from users where name = :name", {"name":session['user']}).fetchone()
        book_id = db.execute("SELECT id from books where title = :title", {"title": title}).fetchone()
        db.execute("INSERT INTO book_users VALUES(:book_id,:user_id,:comment,:rating)", {"book_id":book_id[0], "user_id":user_id[0],
                                                                                       "comment":review,"rating":0})
        db.commit()
        return redirect(url_for("bookdetails", title = title))
    elif request.method == "GET":
        book = db.execute("SELECT * from books where title = :title", {"title": title}).fetchone()
        # reviews = db.execute("SELECT user_id,comment,rating from book_users where book_id = :book_id and comment is not NULL", {"book_id": book.id}).fetchall()
        reviews = db.execute("SELECT BU.user_id, U.name, BU.comment, BU.rating from book_users BU JOIN "
                   "users U ON BU.user_id = U.id and BU.comment is not NULL and BU.book_id = :book_id", {"book_id": book.id}).fetchall()
        return render_template("bookdetails.html", bookandreviews=[book, reviews])


if __name__ == '__main__':
    app.run(host='0.0.0.0')