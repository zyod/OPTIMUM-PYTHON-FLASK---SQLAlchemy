def test_create_user(client):
    r = client.post("/users", json={"username": "u1", "library_name": "L1"})
    assert r.status_code == 201
    data = r.get_json()
    assert data["username"] == "u1"
    assert "library" in data


def test_transfer_book(client):
    u1 = client.post("/users", json={"username": "u2", "library_name": "LibA"}).get_json()
    u2 = client.post("/users", json={"username": "u3", "library_name": "LibB"}).get_json()

    lib_a = u1["library"]["id"]
    lib_b = u2["library"]["id"]

    b = client.post("/books", json={"title": "t", "author": "a", "library_id": lib_a})
    assert b.status_code == 201
    book_id = b.get_json()["id"]

    tr = client.post(f"/books/{book_id}/transfer", json={"to_library_id": lib_b})
    assert tr.status_code == 200
    assert tr.get_json()["book"]["library_id"] == lib_b
