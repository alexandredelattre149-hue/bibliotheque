from flask import Flask, render_template, request, redirect, session
import sqlite3, requests, os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_me")

DB = "database.db"

def init_db():
    with sqlite3.connect(DB) as con:
        # Table des livres
        con.execute("DROP TABLE IF EXISTS books")
        con.execute("""
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT UNIQUE,
            title TEXT,
            authors TEXT,
            publisher TEXT,
            published_year TEXT,
            pages INTEGER,
            description TEXT,
            cover TEXT,
            status TEXT DEFAULT 'bibliotheque',
            favorite INTEGER DEFAULT 0
        )
        """)

        # Table d'authentification (OBLIGATOIRE)
        con.execute("""
        CREATE TABLE IF NOT EXISTS auth (
            id INTEGER PRIMARY KEY,
            password TEXT
        )
        """)
        
        con.execute("""
        CREATE TABLE IF NOT EXISTS auth (
            id INTEGER PRIMARY KEY,
            password TEXT
        )""")

init_db()

@app.route("/", methods=["GET", "POST"])
def login():
    with sqlite3.connect(DB) as con:
        cur = con.cursor()
        cur.execute("SELECT password FROM auth WHERE id=1")
        row = cur.fetchone()

    if not row:
        if request.method == "POST":
            pwd = generate_password_hash(request.form["password"])
            with sqlite3.connect(DB) as con:
                con.execute("INSERT INTO auth VALUES (1, ?)", (pwd,))
            session["auth"] = True
            return redirect("/library")
        return render_template("login.html", first=True)

    if request.method == "POST":
        if check_password_hash(row[0], request.form["password"]):
            session["auth"] = True
            return redirect("/library")

    return render_template("login.html", first=False)

@app.route("/library", methods=["GET", "POST"])
def library():
    if not session.get("auth"):
        return redirect("/")

    if request.method == "POST":
        isbn = request.form["isbn"]
        r = requests.get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}")
        data = r.json()

        if data.get("items"):
            v = data["items"][0]["volumeInfo"]
            title = v.get("title", "")
authors = ", ".join(v.get("authors", []))
publisher = v.get("publisher", "")
published = v.get("publishedDate", "")[:4]
pages = v.get("pageCount", "")
description = v.get("description", "")
cover = v.get("imageLinks", {}).get("thumbnail", "")

           with sqlite3.connect(DB) as con:
    con.execute(
        """
        INSERT OR IGNORE INTO books 
        (isbn, title, authors, publisher, published_year, pages, description, cover)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            isbn,
            title,
            authors,
            publisher,
            published,
            pages,
            description,
            cover
        )
    )

    with sqlite3.connect(DB) as con:
        books = con.execute("SELECT * FROM books").fetchall()

    return render_template("index.html", books=books)

@app.route("/favorite/<int:id>")
def favorite(id):
    with sqlite3.connect(DB) as con:
        con.execute("UPDATE books SET favorite = 1 - favorite WHERE id=?", (id,))
    return redirect("/library")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run()
