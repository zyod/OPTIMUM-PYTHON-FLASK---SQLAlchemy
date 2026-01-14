import unittest
from unittest.mock import MagicMock, patch
from app import create_app

class APIMainTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({"TESTING": True}).test_client()

    @patch("app.routes.Library")
    @patch("app.routes.User")
    @patch("app.routes.db")
    def test_user_add(self, db, User, Library):
        u = MagicMock(id=1, username="u1"); User.return_value = u
        lib = MagicMock(id=10, name="L1"); Library.return_value = lib
        Library.query.filter_by.return_value.first.return_value = lib
        r = self.client.post("/users", json={"username": "u1", "library_name": "L1"})
        self.assertEqual(r.status_code, 201)
        d = r.get_json()
        self.assertEqual((d["id"], d["username"], d["library"]["id"], d["library"]["name"]), (1, "u1", 10, "L1"))
        db.session.commit.assert_called_once()

    @patch("app.routes.Library")
    @patch("app.routes.db")
    def test_user_get(self, db, Library):
        db.session.get.return_value = MagicMock(id=1, username="u1")
        Library.query.filter_by.return_value.first.return_value = MagicMock(id=10, name="L1")
        r = self.client.get("/users/1")
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertEqual((d["id"], d["username"], d["library"]["id"]), (1, "u1", 10))

    @patch("app.routes.Library")
    @patch("app.routes.Book")
    @patch("app.routes.db")
    def test_user_delete(self, db, Book, Library):
        db.session.get.return_value = MagicMock(id=1)
        Library.query.filter_by.return_value.first.return_value = MagicMock(id=10)
        r = self.client.delete("/users/1")
        self.assertEqual(r.status_code, 200)
        db.session.commit.assert_called_once()

    @patch("app.routes.Book")
    @patch("app.routes.db")
    def test_book_add(self, db, Book):
        db.session.get.return_value = MagicMock(id=10)
        b = MagicMock(id=5, title="t", author="a", library_id=10, created_at=MagicMock())
        b.created_at.isoformat.return_value = "2026-01-01T00:00:00"
        Book.return_value = b
        r = self.client.post("/books", json={"title": "t", "author": "a", "library_id": 10})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["id"], 5)
        db.session.commit.assert_called_once()

    @patch("app.routes.Book")
    def test_book_list(self, Book):
        b = MagicMock(id=5, title="t", author="a", library_id=10, created_at=MagicMock())
        b.created_at.isoformat.return_value = "2026-01-01T00:00:00"
        Book.query.all.return_value = [b]
        r = self.client.get("/books")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()), 1)

    @patch("app.routes.db")
    def test_book_delete(self, db):
        db.session.get.return_value = MagicMock(id=5)
        r = self.client.delete("/books/5")
        self.assertEqual(r.status_code, 200)
        db.session.commit.assert_called_once()

    @patch("app.routes.Book")
    @patch("app.routes.Library")
    def test_user_books_count(self, Library, Book):
        Library.query.filter_by.return_value.first.return_value = MagicMock(id=10)
        Book.query.filter_by.return_value.count.return_value = 2
        r = self.client.get("/users/1/books/count")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["count"], 2)

    @patch("app.routes.db")
    def test_transfer_book(self, db):
        book = MagicMock(id=5, title="t", author="a", library_id=10, created_at=MagicMock())
        book.created_at.isoformat.return_value = "2026-01-01T00:00:00"
        db.session.get.side_effect = [book, MagicMock(id=20)]
        r = self.client.post("/books/5/transfer", json={"to_library_id": 20})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["book"]["library_id"], 20)
        db.session.commit.assert_called_once()

if __name__ == "__main__":
    unittest.main()
