import os
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from app.main import app


# TO RUN ALL TESTS:             python -m pytest tests/test_journals.py -p no:warnings
# TO RUN A SPECIFIC TEST:       python -m pytest tests/test_journals.py::test_name_of_test -p no:warnings




load_dotenv()

TEST_USER_ID = os.getenv("TEST_USER_ID")

client = TestClient(app)


### INTEGRATION TESTS FOR JOURNALS - DATABASE OPERATIONS ###


# CREATE JOURNAL
def test_create_journal():
    response = client.post(
        "/journals",
        json={
            "user_id": TEST_USER_ID,
            "date": "2026-04-01",
            "entry": "Test Entry 1"
        }
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["entry"] == "Test Entry 1"


# CREATE INVALID JOURNAL (NO USER ID)
def test_create_journal_invalid():
    response = client.post(
        "/journals",
        json={
            "date": "2026-04-01",
            "entry": "Test Entry 0"
        }
    )

    assert response.status_code == 400


# GET JOURNAL BY DATE
def test_get_journal_by_date():
    # Create Journal First
    create_response = client.post(
        "/journals",
        json={
            "user_id": TEST_USER_ID,
            "date": "2026-04-02",
            "entry": "Test Entry 2"
        }
    )

    get_response = client.get("/journals/date/2026-04-02?user_id=" + str(TEST_USER_ID))

    assert get_response.status_code == 200

    payload = get_response.json()
    assert payload is not None


# GET INVALID JOURNAL BY DATE (DOES NOT EXIST)
def test_get_journal_by_date_invalid():
    response = client.get("/journals/date/2027-01-01?user_id=" + str(TEST_USER_ID))

    assert response.status_code == 200

    payload = response.json()
    assert payload is None or payload == {}


# UPDATE JOURNAL
def test_update_journal():
    # Create Journal First
    create_response = client.post(
        "/journals",
        json={
            "user_id": TEST_USER_ID,
            "date": "2026-04-03",
            "entry": "Test Entry 3"
        }
    )

    journal_id = create_response.json()["id"]

    update_response = client.put(
        "/journals/" + str(journal_id),
        json={
            "user_id": TEST_USER_ID,
            "date": "2026-04-03",
            "entry": "Test Entry 3 Updated"
        }
    )

    assert update_response.status_code == 200

    get_response = client.get("/journals/date/2026-04-03?user_id=" + str(TEST_USER_ID))
    payload = get_response.json()
    assert payload["entry"] == "Test Entry 3 Updated"


# DELETE JOURNAL
def test_delete_journal():
    # Create Journal First
    create_response = client.post(
        "/journals",
        json={
            "user_id": TEST_USER_ID,
            "date": "2026-04-04",
            "entry": "Test Entry 4"
        }
    )

    journal_id = create_response.json()["id"]

    delete_response = client.delete("/journals/" + str(journal_id))

    assert delete_response.status_code == 200

    get_response = client.get("/journals/date/2026-04-04?user_id=" + str(TEST_USER_ID))
    payload = get_response.json()
    assert payload is None or payload == {}
