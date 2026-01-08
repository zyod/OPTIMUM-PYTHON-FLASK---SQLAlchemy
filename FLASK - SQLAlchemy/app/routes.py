from flask import request, jsonify
from .extensions import db
from .models import Library, Book

def register_routes(app):


    @app.post("/libraries")
    def create_library():
        data = request.get_json() or {}
        name = data.get("name")
        if not name:
            return jsonify({"error": "name is required"}), 400
        lib = Library(name=name)
        db.session.add(lib)
        db.session.commit()
        return jsonify({"id": lib.id, "name": lib.name}), 201

    @app.get("/libraries")
    def list_libraries():
        libs = Library.query.all()
        return jsonify([{"id": l.id, "name": l.name} for l in libs]), 200

    @app.put("/libraries/<int:library_id>")
    def update_library(library_id):
        lib = Library.query.get(library_id)
        if not lib:
            return jsonify({"error": "library not found"}), 404
        data = request.get_json() or {}
        name = data.get("name")
        if not name:
            return jsonify({"error": "name is required"}), 400
        lib.name = name
        db.session.commit()
        return jsonify({"id": lib.id, "name": lib.name}), 200

    @app.delete("/libraries/<int:library_id>")
    def delete_library(library_id):
        lib = Library.query.get(library_id)
        if not lib:
            return jsonify({"error": "library not found"}), 404
        db.session.delete(lib)
        db.session.commit()
        return jsonify({"message": "deleted"}), 200

    @app.get("/libraries/<int:library_id>/books")
    def books_under_library(library_id):
        lib = Library.query.get(library_id)
        if not lib:
            return jsonify({"error": "library not found"}), 404
        books = Book.query.filter_by(library_id=library_id).all()
        return jsonify([{
            "id": b.id, "title": b.title, "author": b.author,
            "library_id": b.library_id, "created_at": b.created_at.isoformat() + "Z"
        } for b in books]), 200


    @app.post("/books")
    def create_book():
        data = request.get_json() or {}
        title = data.get("title")
        author = data.get("author")
        library_id = data.get("library_id")
        if not title or not author or library_id is None:
            return jsonify({"error": "title, author, library_id are required"}), 400
        if not Library.query.get(library_id):
            return jsonify({"error": "library not found"}), 404
        book = Book(title=title, author=author, library_id=library_id)
        db.session.add(book)
        db.session.commit()
        return jsonify({
            "id": book.id, "title": book.title, "author": book.author,
            "library_id": book.library_id, "created_at": book.created_at.isoformat() + "Z"
        }), 201

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

        books = query.all()
        return jsonify([{
            "id": b.id, "title": b.title, "author": b.author,
            "library_id": b.library_id, "created_at": b.created_at.isoformat() + "Z"
        } for b in books]), 200

    @app.put("/books/<int:book_id>")
    def update_book(book_id):
        b = Book.query.get(book_id)
        if not b:
            return jsonify({"error": "book not found"}), 404
        data = request.get_json() or {}

        if "title" in data:
            b.title = data["title"]
        if "author" in data:
            b.author = data["author"]
        if "library_id" in data:
            if not Library.query.get(data["library_id"]):
                return jsonify({"error": "library not found"}), 404
            b.library_id = data["library_id"]

        db.session.commit()
        return jsonify({
            "id": b.id, "title": b.title, "author": b.author,
            "library_id": b.library_id, "created_at": b.created_at.isoformat() + "Z"
        }), 200

    @app.delete("/books/<int:book_id>")
    def delete_book(book_id):
        b = Book.query.get(book_id)
        if not b:
            return jsonify({"error": "book not found"}), 404
        db.session.delete(b)
        db.session.commit()
        return jsonify({"message": "deleted"}), 200
