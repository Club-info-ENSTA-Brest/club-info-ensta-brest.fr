import os

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()


def render(template):
    return render_template(template, htmx=request.headers.get("HX-Request"))


@app.route("/")
def home():
    return render("home.html")


@app.route("/tutos")
def tutos():
    return render("tutos.html")


@app.route("/reseaux")
def resea():
    return render("reseaux.html")


@app.route("/projets_enstasiens")
def projets():
    return render("projets_enstasiens.html")


if __name__ == "__main__":
    app.run(debug=True)
