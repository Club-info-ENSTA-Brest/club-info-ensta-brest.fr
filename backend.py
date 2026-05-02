import os
import sqlite3
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from flask import Flask, g, redirect, render_template, request, url_for

DATABASE = "database.db"


# handling methods for image data retrieval
def get_image_data(link):
    if not link:
        return None

    # -------------------------
    # 1. Local file → ignore (or handle differently if you want)
    # -------------------------
    if os.path.isfile(link):
        return None  # or return a static path

    # -------------------------
    # 2. URL handling
    # -------------------------
    if link.startswith("http"):
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            r = requests.get(link, headers=headers, timeout=3)

            # -------------------------
            # 2A. If it's already an image → return directly
            # -------------------------
            content_type = r.headers.get("Content-Type", "")
            if "image" in content_type:
                return link

            # -------------------------
            # 2B. Parse HTML for best favicon
            # -------------------------
            soup = BeautifulSoup(r.text, "html.parser")

            icon_tags = soup.find_all("link", rel=lambda x: x and "icon" in x.lower())

            # Prefer SVG if available 👇
            for tag in icon_tags:
                href = tag.get("href")
                if href and href.endswith(".svg"):
                    return urljoin(link, href)

            # Otherwise take first valid icon
            for tag in icon_tags:
                href = tag.get("href")
                if href:
                    return urljoin(link, href)

            # -------------------------
            # 2C. Fallback → /favicon.ico
            # -------------------------
            parsed = urlparse(link)
            return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

        except Exception:
            return None

    return None


# handling database operations
def create_db():
    if os.path.exists("database.db"):
        try:
            os.remove(os.path("dababase.db"))
        except Exception:
            print("Failed to remove existing database")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        author TEXT,
        date TEXT,
        image TEXT,
        type TEXT,
        link TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_project(title, description, author, link, type):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        now = datetime.now().strftime("%Y-%m-%d")

        # Assuming `link` will be used as an image URL or file path
        if link is not None:
            image_data = get_image_data(link)

            c.execute(
                """
                INSERT INTO projects (title, description, author, date, image, type, link)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (title, description, author, now, image_data, type, link),
            )
        else:
            c.execute(
                """
                INSERT INTO projects (title, description, author, date, image, type, likn)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (title, description, author, now, None, type, link),
            )

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error inserting project: {e}")


# only run once to create the database
create_db()


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


# @app.route("/")
# def home():
#    db = get_db()
#    projects = db.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
#    return render("home.html", data=projects)


@app.route("/tutos")
def tutos():
    return render("tutos.html")


@app.route("/reseaux")
def resea():
    return render("reseaux.html")


@app.route("/projets_enstasiens")
def projets_enstasiens():
    return render("projets_enstasiens.html")


# handle requests
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        author = request.form.get("author")
        link = request.form.get("link")
        type_input = request.form.get("type-input")

        # Assuming you handle image upload separately
        insert_project(title, description, author, link, type_input)

        return redirect(url_for("home"))

    db = get_db()
    projects = db.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    return render("home.html", data=projects)


if __name__ == "__main__":
    app.run(debug=True)
