# Edson Task Manager

A simple CRUD project with a browser interface and REST API. Built with Python,
Flask, SQLite, and plain HTML/CSS/JavaScript. Docker runs the app with Gunicorn
as a non-root user; a named Docker volume keeps tasks across container recreation.

## Run with Docker

From this project directory:

```sh
docker compose up --build -d
```

Open http://localhost:8000. Create a task, edit its title or description, mark it
complete, or delete it. The app starts with an empty task list.

```sh
docker compose ps              # Check container health
docker compose logs -f        # View logs (Ctrl+C exits logs)
docker compose down           # Stop; saved tasks remain
```

If port 8000 is occupied, run `PORT=8001 docker compose up --build -d`, then open
http://localhost:8001. `docker compose down -v` permanently removes saved tasks.

This is a local learning project without accounts or authentication. Compose binds
the published port to localhost. Add authentication before exposing it publicly.

## Run without Docker

Requires Python 3.10 or later.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:8000. The development server stores data in `data/tasks.db`.
Set `DATABASE_PATH` to choose another file location.

## API

| Method | Route | Behavior |
| --- | --- | --- |
| GET | `/api/tasks` | List all tasks, newest first |
| GET | `/api/tasks/1` | Read one task |
| POST | `/api/tasks` | Create a task (201) |
| PUT | `/api/tasks/1` | Replace task fields (200) |
| DELETE | `/api/tasks/1` | Delete a task (204) |
| GET | `/health` | Check app and database availability |

POST and PUT accept JSON: required `title` (1–120 characters after trimming),
optional `description` (up to 2000 characters, default empty), and optional boolean
`completed` (default false). PUT replaces all editable fields; omitted optional
fields return to their defaults. Missing records return 404; invalid fields return
400. Malformed JSON returns 400, non-JSON bodies 415, and bodies over 16 KiB 413.

```sh
curl -X POST http://localhost:8000/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Learn Docker","description":"Run my CRUD project"}'

curl http://localhost:8000/api/tasks

curl -X PUT http://localhost:8000/api/tasks/1 \
  -H 'Content-Type: application/json' \
  -d '{"title":"Learn Docker","description":"Run my CRUD project","completed":true}'

curl -X DELETE http://localhost:8000/api/tasks/1
```

Use the ID returned by POST in subsequent requests.

## Tests

After installing requirements:

```sh
python -m unittest discover -s tests -v
```

Tests use temporary databases and cover CRUD, validation, missing records, safe
text storage, persistence across app instances, and the page/health endpoints.

## Files

- `app.py`: API, validation, database initialization, and web page route.
- `templates/index.html`: task manager page.
- `static/`: browser interactions and styling.
- `tests/test_app.py`: automated API tests.
- `Dockerfile`: container image and health check.
- `compose.yaml`: localhost port mapping and persistent database volume.

Deployment references: [Flask with Gunicorn](https://flask.palletsprojects.com/en/stable/deploying/gunicorn/)
and the [official Python Docker image](https://hub.docker.com/_/python).
