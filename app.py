"""A small task manager backed by SQLite."""
import os
import sqlite3
from pathlib import Path

from flask import Flask, g, jsonify, render_template, request
from werkzeug.exceptions import HTTPException


def create_app(database=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=str(database or os.getenv("DATABASE_PATH", "data/tasks.db")),
        MAX_CONTENT_LENGTH=16 * 1024,
    )
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"], timeout=10)
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_error):
        connection = g.pop("db", None)
        if connection is not None:
            connection.close()

    with app.app_context():
        db().execute("PRAGMA journal_mode=WAL")
        db().execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
        """)
        db().commit()

    def serialize(row):
        task = dict(row)
        task["completed"] = bool(task["completed"])
        return task

    def get_task(task_id):
        return db().execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    def validate():
        data = request.get_json()
        if not isinstance(data, dict):
            return None, "Request body must be a JSON object."
        if set(data) - {"title", "description", "completed"}:
            return None, "Allowed fields: title, description, completed."
        title = data.get("title")
        description = data.get("description", "")
        completed = data.get("completed", False)
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
            return None, "Title must contain 1–120 characters."
        if not isinstance(description, str) or len(description) > 2000:
            return None, "Description must be text with at most 2000 characters."
        if not isinstance(completed, bool):
            return None, "Completed must be true or false."
        return (title.strip(), description.strip(), int(completed)), None

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        db().execute("SELECT 1 FROM tasks LIMIT 1")
        return jsonify(status="ok")

    @app.get("/api/tasks")
    def list_tasks():
        rows = db().execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
        return jsonify([serialize(row) for row in rows])

    @app.get("/api/tasks/<int:task_id>")
    def read_task(task_id):
        row = get_task(task_id)
        if row is None:
            return jsonify(error="Task not found."), 404
        return jsonify(serialize(row))

    @app.post("/api/tasks")
    def create_task():
        values, error = validate()
        if error:
            return jsonify(error=error), 400
        cursor = db().execute(
            "INSERT INTO tasks (title, description, completed) VALUES (?, ?, ?)", values
        )
        db().commit()
        return jsonify(serialize(get_task(cursor.lastrowid))), 201

    @app.put("/api/tasks/<int:task_id>")
    def update_task(task_id):
        values, error = validate()
        if error:
            return jsonify(error=error), 400
        cursor = db().execute(
            "UPDATE tasks SET title = ?, description = ?, completed = ? WHERE id = ?",
            (*values, task_id),
        )
        db().commit()
        if cursor.rowcount == 0:
            return jsonify(error="Task not found."), 404
        return jsonify(serialize(get_task(task_id)))

    @app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id):
        cursor = db().execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        db().commit()
        if cursor.rowcount == 0:
            return jsonify(error="Task not found."), 404
        return "", 204

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=8000)
