import os
import sqlite3
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from flask import Flask, g, redirect, render_template, request, url_for

DATABASE = "database.db"

# à remplacer par une vraie DB plus tard
NEWS = [
    [
        {
            "type": "event",
            "text": "Atelier : faire sa première WebApp avec Flask en 1h",
        },
        {
            "type": "news",
            "text": "Une IA de chez OpenAi résout une importante conjecture vielle de 80ans !",
        },
        {"type": "event", "text": "Prochain hackathon sur Brest le ..."},
    ]
]

GITLAB_API_URL = "https://gitlab.ensta-bretagne.fr/api/v4/projects"
GITLAB_CACHE_TTL = timedelta(hours=6)
GITLAB_MAX_PAGES = 5
GITLAB_PER_PAGE = 100



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


def init_db():
    conn = sqlite3.connect(DATABASE)
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

    c.execute("""
    CREATE TABLE IF NOT EXISTS gitlab_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gitlab_id INTEGER UNIQUE NOT NULL,
        title TEXT,
        description TEXT,
        author TEXT,
        date TEXT,
        image TEXT,
        type TEXT DEFAULT 'gitlab',
        link TEXT,
        path_with_namespace TEXT,
        topics TEXT,
        fetched_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS cache_state (
        key TEXT PRIMARY KEY,
        fetched_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def get_gitlab_cache_age():
    db = get_db()
    row = db.execute(
        "SELECT fetched_at FROM cache_state WHERE key = ?", ("gitlab_projects",)
    ).fetchone()
    if not row or not row["fetched_at"]:
        return None
    try:
        return datetime.now() - datetime.fromisoformat(row["fetched_at"])
    except ValueError:
        return None


def fetch_gitlab_projects():
    projects = []
    for page in range(1, GITLAB_MAX_PAGES + 1):
        response = requests.get(
            GITLAB_API_URL,
            params={
                "visibility": "public",
                "order_by": "last_activity_at",
                "sort": "desc",
                "per_page": GITLAB_PER_PAGE,
                "page": page,
            },
            timeout=8,
        )
        response.raise_for_status()
        page_projects = response.json()
        if not page_projects:
            break
        projects.extend(page_projects)
    return projects


def upsert_gitlab_projects(projects):
    db = get_db()
    fetched_at = datetime.now().isoformat(timespec="seconds")

    for project in projects:
        db.execute(
            """
            INSERT INTO gitlab_projects (
                gitlab_id, title, description, author, date, image, type, link,
                path_with_namespace, topics, fetched_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(gitlab_id) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                author = excluded.author,
                date = excluded.date,
                image = excluded.image,
                type = excluded.type,
                link = excluded.link,
                path_with_namespace = excluded.path_with_namespace,
                topics = excluded.topics,
                fetched_at = excluded.fetched_at
            """,
            (
                project.get("id"),
                project.get("name"),
                project.get("description"),
                project.get("namespace", {}).get("name")
                or project.get("name_with_namespace", "").split(" / ")[0]
                or project.get("namespace", {}).get("full_path"),
                (project.get("last_activity_at") or project.get("created_at") or "")[:10],
                project.get("avatar_url"),
                "gitlab",
                project.get("web_url"),
                project.get("path_with_namespace"),
                ", ".join(project.get("topics") or project.get("tag_list") or []),
                fetched_at,
            ),
        )

    db.execute(
        """
        INSERT INTO cache_state (key, fetched_at) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET fetched_at = excluded.fetched_at
        """,
        ("gitlab_projects", fetched_at),
    )
    db.commit()


def refresh_gitlab_projects_if_needed(force=False):
    cache_age = get_gitlab_cache_age()
    if not force and cache_age is not None and cache_age < GITLAB_CACHE_TTL:
        return

    try:
        upsert_gitlab_projects(fetch_gitlab_projects())
    except requests.RequestException as error:
        print(f"Failed to refresh GitLab projects: {error}")


def create_db():
    if os.path.exists("database.db"):
        try:
            os.remove(os.path.abspath("database.db"))
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


# add a projet to the database
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
                INSERT INTO projects (title, description, author, date, image, type, link)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (title, description, author, now, None, type, link),
            )

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error inserting project: {e}")


# only run once to create the database, or re-run if the DB is fucked up
# create_db()


### FLASK ###

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()
init_db()


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


def fuzzy_match_score(query, project):
    query = (query or "").strip().lower()
    if not query:
        return 1

    searchable_fields = [
        project["title"],
        project["description"],
        project["author"],
        project["date"],
        project["type"],
        project["link"],
    ]
    haystack = " ".join(str(field or "") for field in searchable_fields).lower()

    if query in haystack:
        return 1

    query_words = query.split()
    haystack_words = haystack.split()

    word_scores = [
        max(
            SequenceMatcher(None, query_word, haystack_word).ratio()
            for haystack_word in haystack_words
        )
        for query_word in query_words
        if haystack_words
    ]

    if word_scores:
        return sum(word_scores) / len(word_scores)

    return SequenceMatcher(None, query, haystack).ratio()


def get_enstasien_projects(search_query=""):
    refresh_gitlab_projects_if_needed()

    db = get_db()
    local_projects = [
        dict(project)
        for project in db.execute(
            "SELECT title, description, author, date, image, type, link FROM projects WHERE type = ?",
            ("partage",),
        ).fetchall()
    ]
    gitlab_projects = [
        dict(project)
        for project in db.execute(
            """
            SELECT title, description, author, date, image, type, link
            FROM gitlab_projects
            ORDER BY date DESC
            LIMIT 200
            """
        ).fetchall()
    ]

    projects = local_projects + gitlab_projects
    search_query = (search_query or "").strip()
    if not search_query:
        return projects[:80]

    scored_projects = [
        (fuzzy_match_score(search_query, project), project) for project in projects
    ]

    return [
        project
        for score, project in sorted(
            scored_projects, key=lambda item: item[0], reverse=True
        )
        if score >= 0.65
    ][:80]


@app.route("/")
def home():
    return render("home.html", data=NEWS)


@app.route("/tutos")
def tutos():
    return render("tutos.html")


@app.route("/reseaux")
def reseaux():
    return render("reseaux.html")


@app.route("/projets_enstasiens")
def projets_enstasiens():
    return render("projets_enstasiens.html", data=get_enstasien_projects())


@app.route("/projets_enstasiens/search")
def search_projets_enstasiens():
    projects = get_enstasien_projects(request.args.get("q", ""))
    return render_template("_project_cards.html", data=projects)


# handle requests
@app.route("/feed", methods=["GET", "POST"])
def feed():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        author = request.form.get("author")
        link = request.form.get("link")
        type_input = request.form.get("type-input")

        # Assuming you handle image upload separately
        insert_project(title, description, author, link, type_input)

        return redirect(url_for("feed"))

    db = get_db()
    projects = db.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    return render(
        "feed.html",
        data=[
            projects,
            [{"title": "Titre", "description": "Description", "date": "01/01/2026"}],
        ],
    )


if __name__ == "__main__":
    app.run(debug=True)
