import os, time, sqlite3
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, g)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "koi-bhi-lamba-secret-123"

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
DB = os.path.join(app.root_path, "insta.db")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED = {"png", "jpg", "jpeg", "gif", "webp"}

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    d = g.pop("db", None)
    if d:
        d.close()

def init_db():
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        bio TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        image TEXT NOT NULL,
        caption TEXT);
    """)
    con.commit()
    con.close()

init_db()

def login_required(f):
    @wraps(f)
    def wrapper(*a, **k):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*a, **k)
    return wrapper

@app.route("/")
@login_required
def home():
    posts = db().execute(
        "SELECT posts.*, users.username FROM posts "
        "JOIN users ON users.id = posts.user_id "
        "ORDER BY posts.id DESC").fetchall()
    return render_template("index.html", posts=posts)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form["username"].strip()
        p = request.form["password"]
        if len(u) < 3 or len(p) < 4:
            flash("Username कम से कम 3 और password कम से कम 4 अक्षर का हो")
        else:
            try:
                db().execute("INSERT INTO users(username, password) VALUES(?, ?)",
                             (u, generate_password_hash(p)))
                db().commit()
                flash("Account बन गया, अब Login करो")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("ये username पहले से है")
    return render_template("auth.html", title="Register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"].strip()
        user = db().execute("SELECT * FROM users WHERE username = ?", (u,)).fetchone()
        if user and check_password_hash(user["password"], request.form["password"]):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))
        flash("Username या password गलत है")
    return render_template("auth.html", title="Login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("photo")
    caption = request.form.get("caption", "")
    if file and file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext in ALLOWED:
            name = f"{session['user_id']}_{int(time.time())}.{ext}"
            file.save(os.path.join(UPLOAD_FOLDER, name))
            db().execute("INSERT INTO posts(user_id, image, caption) VALUES(?, ?, ?)",
                         (session["user_id"], "uploads/" + name, caption))
            db().commit()
        else:
            flash("सिर्फ photo (jpg, png, gif, webp) चलेगी")
    return redirect(url_for("home"))

@app.route("/profile/<username>", methods=["GET", "POST"])
@login_required
def profile(username):
    user = db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        return "ऐसा user नहीं मिला", 404
    if request.method == "POST" and user["id"] == session["user_id"]:
        db().execute("UPDATE users SET bio = ? WHERE id = ?",
                     (request.form.get("bio", ""), user["id"]))
        db().commit()
        return redirect(url_for("profile", username=username))
    posts = db().execute("SELECT * FROM posts WHERE user_id = ? ORDER BY id DESC",
                         (user["id"],)).fetchall()
    return render_template("profile.html", user=user, posts=posts,
                           is_me=(user["id"] == session["user_id"]))

if __name__ == "__main__":
    app.run(debug=True)