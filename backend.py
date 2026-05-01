import os
import sqlite3

from flask import Flask, g, redirect, render_template, request, url_for

DATABASE = "database.db"


def create_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        author TEXT,
        date TEXT,
        image TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_project():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        """
    INSERT INTO projects (title, description, author, date, image)
    VALUES (?, ?, ?, ?, ?)
    """,
        ("My Project", "Cool idea", "Arnaud", "2026-05-01", ""),
    )

    conn.commit()
    conn.close()


# only run once to create the database
# create_db()
# insert_project()
# insert_project()
# insert_project()


app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def render(template, data=None):
    return render_template(template, data=data, htmx=request.headers.get("HX-Request"))


@app.route("/")
def home():
    db = get_db()
    projects = db.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    return render("home.html", data=projects)


@app.route("/tutos")
def tutos():
    return render("tutos.html")


@app.route("/reseaux")
def resea():
    return render("reseaux.html")


@app.route("/projets_enstasiens")
def projets_enstasiens():
    return render("projets_enstasiens.html")


if __name__ == "__main__":
    app.run(debug=True)
