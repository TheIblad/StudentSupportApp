import os
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from app.main import app


# TO RUN ALL TESTS:             python -m pytest tests/test_documents.py -p no:warnings
# TO RUN A SPECIFIC TEST:       python -m pytest tests/test_documents.py::test_name_of_test -p no:warnings




load_dotenv()

TEST_USER_ID = os.getenv("TEST_USER_ID")

client = TestClient(app)


### INTEGRATION TESTS FOR DOCUMENTS - DATABASE OPERATIONS ###


# CREATE DOCUMENT (METADATA)
def test_create_document():
    response = client.post(
        "/documents",
        json={
            "file_name": "Test Document 1.pdf",
            "file_location": "Test Location",
            "module": "Test Module",
            "user_id": TEST_USER_ID
        }
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["file_name"] == "Test Document 1.pdf"


# GET DOCUMENTS
def test_get_documents():
    # Create Document First
    create_response = client.post(
        "/documents",
        json={
            "file_name": "Test Document 2.pdf",
            "file_location": "Test Location",
            "module": "Test Module",
            "user_id": TEST_USER_ID
        }
	)

    get_response = client.get("/documents?user_id=" + str(TEST_USER_ID))

    assert get_response.status_code == 200

    payload = get_response.json()
    assert (isinstance(payload, list) and any(item["file_name"] == "Test Document 2.pdf" for item in payload))


# UPDATE DOCUMENT
def test_update_document():
    # Create Document First
    create_response = client.post(
        "/documents",
        json={
            "file_name": "Test Document 3.pdf",
            "file_location": "Test Location",
            "module": "Test Module",
            "user_id": TEST_USER_ID
        }
	)

    document_id = create_response.json()["id"]

    update_response = client.put(
        "/documents/" + str(document_id),
        json={
            "file_name": "Test Document 3 Updated.pdf",
            "file_location": "Test Location",
            "module": "Test Module",
            "user_id": TEST_USER_ID
        }
    )

    assert update_response.status_code == 200

    get_response = client.get("/documents?user_id=" + str(TEST_USER_ID))
    payload = get_response.json()

    assert any(item["file_name"] == "Test Document 3 Updated.pdf" for item in payload)


# DELETE DOCUMENT
def test_delete_document():
    # Create Document First
    create_response = client.post(
        "/documents",
        json={
            "file_name": "Test Document 4.pdf",
            "file_location": "Test Location",
            "module": "Test Module",
            "user_id": TEST_USER_ID
        }
	)

    document_id = create_response.json()["id"]

    delete_response = client.delete("/documents/" + str(document_id))

    assert delete_response.status_code == 200

    get_response = client.get("/documents?user_id=" + str(TEST_USER_ID))
    payload = get_response.json()

    assert not any(item["id"] == document_id for item in payload)
