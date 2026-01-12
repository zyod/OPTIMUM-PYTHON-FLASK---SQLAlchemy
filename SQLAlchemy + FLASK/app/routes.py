from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
from .extensions import db
from .models import User, Library, Book


def register_routes(app):

    def book_json(b):
        return {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "library_id": b.library_id,
            "created_at": b.created_at.isoformat() + "Z",
        }

    # ---------------- Users CRUD ----------------

    @app.post("/users")
    def create_user():
        d = request.get_json() or {}
        if not d.get("username") or not d.get("library_name"):
            return jsonify({"error": "username and library_name are required"}), 400

        u = User(username=d["username"])
        db.session.add(u)
        db.session.flush()  # get u.id

        db.session.add(Library(name=d["library_name"], user_id=u.id))

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "username already exists"}), 409

        lib = Library.query.filter_by(user_id=u.id).first()
        return jsonify({
            "id": u.id,
            "username": u.username,
            "library": {"id": lib.id, "name": lib.name}
        }), 201

    @app.get("/users")
    def list_users():
        users = User.query.all()
        out = []
        for u in users:
            lib = Library.query.filter_by(user_id=u.id).first()
            out.append({
                "id": u.id,
                "username": u.username,
                "library": {"id": lib.id, "name": lib.name} if lib else None
            })
        return jsonify(out), 200

    @app.get("/users/<int:user_id>")
    def get_user(user_id):
        u = db.session.get(User, user_id)
        if not u:
            return jsonify({"error": "user not found"}), 404
        lib = Library.query.filter_by(user_id=user_id).first()
        return jsonify({
            "id": u.id,
            "username": u.username,
            "library": {"id": lib.id, "name": lib.name} if lib else None
        }), 200

    @app.put("/users/<int:user_id>")
    def update_user(user_id):
        u = db.session.get(User, user_id)
        if not u:
            return jsonify({"error": "user not found"}), 404

        d = request.get_json() or {}

        if "username" in d:
            if not d["username"]:
                return jsonify({"error": "username is required"}), 400
            u.username = d["username"]

        if "library_name" in d:
            if not d["library_name"]:
                return jsonify({"error": "library_name is required"}), 400
            lib = Library.query.filter_by(user_id=user_id).first()
            if lib:
                lib.name = d["library_name"]

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "username already exists"}), 409

        lib = Library.query.filter_by(user_id=user_id).first()
        return jsonify({
            "id": u.id,
            "username": u.username,
            "library": {"id": lib.id, "name": lib.name} if lib else None
        }), 200

    @app.delete("/users/<int:user_id>")
    def delete_user(user_id):
        u = db.session.get(User, user_id)
        if not u:
            return jsonify({"error": "user not found"}), 404

        lib = Library.query.filter_by(user_id=user_id).first()
        if lib:
            Book.query.filter_by(library_id=lib.id).delete()
            db.session.delete(lib)

        db.session.delete(u)
        db.session.commit()
        return jsonify({"message": "deleted"}), 200

    # count books in user's own library
    @app.get("/users/<int:user_id>/books/count")
    def user_books_count(user_id):
        lib = Library.query.filter_by(user_id=user_id).first()
        if not lib:
            return jsonify({"error": "user or library not found"}), 404

        count = Book.query.filter_by(library_id=lib.id).count()
        return jsonify({"user_id": user_id, "library_id": lib.id, "count": count}), 200

    # ---------------- Libraries ----------------

    @app.get("/libraries")
    def list_libraries():
        libs = Library.query.all()
        return jsonify([{"id": l.id, "name": l.name, "user_id": l.user_id} for l in libs]), 200

    @app.get("/libraries/<int:library_id>/books")
    def books_under_library(library_id):
        if not db.session.get(Library, library_id):
            return jsonify({"error": "library not found"}), 404
        books = Book.query.filter_by(library_id=library_id).all()
        return jsonify([book_json(b) for b in books]), 200

    # ---------------- Books CRUD + transfer ----------------

    @app.post("/books")
    def create_book():
        d = request.get_json() or {}
        if not d.get("title") or not d.get("author") or d.get("library_id") is None:
            return jsonify({"error": "title, author, library_id are required"}), 400
        if not db.session.get(Library, d["library_id"]):
            return jsonify({"error": "library not found"}), 404

        b = Book(title=d["title"], author=d["author"], library_id=d["library_id"])
        db.session.add(b)
        db.session.commit()
        return jsonify(book_json(b)), 201

    @app.get("/books")
    def list_books():
        library_id = request.args.get("library_id", type=int)
        q = request.args.get("q", type=str)

        query = Book.query
        if library_id is not None:
            query = query.filter_by(library_id=library_id)
        if q:
            like = f"%{q}%"
            query = query.filter((Book.title.ilike(like)) | (Book.author.ilike(like)))

        return jsonify([book_json(b) for b in query.all()]), 200

    @app.put("/books/<int:book_id>")
    def update_book(book_id):
        b = db.session.get(Book, book_id)
        if not b:
            return jsonify({"error": "book not found"}), 404

        d = request.get_json() or {}
        if "title" in d:
            b.title = d["title"]
        if "author" in d:
            b.author = d["author"]
        if "library_id" in d:
            if not db.session.get(Library, d["library_id"]):
                return jsonify({"error": "library not found"}), 404
            b.library_id = d["library_id"]

        db.session.commit()
        return jsonify(book_json(b)), 200

    @app.delete("/books/<int:book_id>")
    def delete_book(book_id):
        b = db.session.get(Book, book_id)
        if not b:
            return jsonify({"error": "book not found"}), 404
        db.session.delete(b)
        db.session.commit()
        return jsonify({"message": "deleted"}), 200

    @app.post("/books/<int:book_id>/transfer")
    def transfer_book(book_id):
        b = db.session.get(Book, book_id)
        if not b:
            return jsonify({"error": "book not found"}), 404

        d = request.get_json() or {}
        to_id = d.get("to_library_id")
        if to_id is None:
            return jsonify({"error": "to_library_id is required"}), 400
        if not db.session.get(Library, to_id):
            return jsonify({"error": "destination library not found"}), 404

        b.library_id = to_id
        db.session.commit()
        return jsonify({"message": "transferred", "book": book_json(b)}), 200
