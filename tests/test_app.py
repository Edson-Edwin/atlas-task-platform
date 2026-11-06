import tempfile
import unittest
from pathlib import Path

from app import create_app


class TaskTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / "tasks.db"
        self.app = create_app(self.database)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_full_crud(self):
        self.assertEqual(self.client.get("/api/tasks").json, [])
        response = self.client.post("/api/tasks", json={"title": " Learn Docker ", "description": "Build the app"})
        self.assertEqual(response.status_code, 201)
        task = response.json
        self.assertEqual(task["title"], "Learn Docker")
        self.assertIs(task["completed"], False)
        url = f'/api/tasks/{task["id"]}'
        self.assertEqual(self.client.get(url).json, task)
        self.assertEqual(len(self.client.get("/api/tasks").json), 1)
        updated = self.client.put(url, json={"title": "Docker learned", "description": "Done", "completed": True})
        self.assertEqual(updated.status_code, 200)
        self.assertIs(updated.json["completed"], True)
        self.assertEqual(updated.json["title"], "Docker learned")
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get("/api/tasks").json, [])

    def test_validation(self):
        for payload in [[], {}, {"title": " "}, {"title": "x" * 121},
                        {"title": "Task", "description": 42},
                        {"title": "Task", "description": "x" * 2001},
                        {"title": "Task", "completed": "false"},
                        {"title": "Task", "unknown": True}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/tasks", json=payload).status_code, 400)
        self.assertEqual(self.client.post("/api/tasks", data="{bad", content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/api/tasks", data="title=Task").status_code, 415)
        self.assertEqual(self.client.post("/api/tasks", json={"title": "x" * 20000}).status_code, 413)
        self.assertEqual(self.client.get("/api/tasks").json, [])

    def test_missing_records(self):
        self.assertEqual(self.client.get("/api/tasks/999").status_code, 404)
        self.assertEqual(self.client.put("/api/tasks/999", json={"title": "Test"}).status_code, 404)
        self.assertEqual(self.client.delete("/api/tasks/999").status_code, 404)

    def test_persistence(self):
        self.client.post("/api/tasks", json={"title": "Keep me"})
        fresh_client = create_app(self.database).test_client()
        self.assertEqual(fresh_client.get("/api/tasks").json[0]["title"], "Keep me")

    def test_invalid_update_keeps_existing_data(self):
        task = self.client.post("/api/tasks", json={"title": "Keep title"}).json
        url = f'/api/tasks/{task["id"]}'
        self.assertEqual(self.client.put(url, json={"title": ""}).status_code, 400)
        self.assertEqual(self.client.get(url).json, task)

    def test_sql_and_html_are_stored_as_text(self):
        title = "<script>alert(1)</script>'; DROP TABLE tasks; --"
        self.assertEqual(self.client.post("/api/tasks", json={"title": title}).status_code, 201)
        self.assertEqual(self.client.get("/api/tasks").json[0]["title"], title)

    def test_page_and_health(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        with self.client.get("/static/app.js") as response:
            self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/health").json, {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
