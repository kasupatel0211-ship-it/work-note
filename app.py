from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = "secret123"

# SQLite DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ---------------- DATABASE MODELS ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200))
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer)

# ---------------- HOME ----------------
@app.route("/")
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    tasks = Task.query.filter_by(
        user_id=session["user_id"]
    ).all()

    total_tasks = len(tasks)

    completed_tasks = len(
        [task for task in tasks if task.done]
    )

    pending_tasks = total_tasks - completed_tasks

    return render_template(
        "index.html",
        tasks=tasks,
        username=user.username,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks
    )
# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return render_template(
                "register.html",
                error="Username already exists!",
                username=username
            )

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        new_user = User(
            username=username,
            password=hashed_pw
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(f"/login?username={username}")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect("/")
        else:
            return "Invalid credentials ❌"

    username = request.args.get("username", "")
    return render_template("login.html", username=username)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/login")

# ---------------- ADD TASK ----------------
@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")

    task_text = request.form["task"]

    task = Task(text=task_text, user_id=session["user_id"])
    db.session.add(task)
    db.session.commit()

    return redirect("/")

# ---------------- DONE ----------------
@app.route("/done/<int:id>")
def done(id):
    task = Task.query.get(id)

    if task and task.user_id == session["user_id"]:
        task.done = not task.done
        db.session.commit()

    return redirect("/")

# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):
    task = Task.query.get(id)

    if task and task.user_id == session["user_id"]:
        db.session.delete(task)
        db.session.commit()

    return redirect("/")

# ---------------- INIT DB ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    if "user_id" not in session:
        return redirect("/login")

    task = Task.query.get_or_404(id)

    if task.user_id != session["user_id"]:
        return redirect("/")

    if request.method == "POST":
        task.text = request.form["task"]
        db.session.commit()
        return redirect("/")

    return render_template("edit.html", task=task)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)


