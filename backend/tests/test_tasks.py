import os
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from app.main import app


# TO RUN ALL TESTS:             python -m pytest tests/test_tasks.py -p no:warnings
# TO RUN A SPECIFIC TEST:       python -m pytest tests/test_tasks.py::test_name_of_test -p no:warnings




load_dotenv()

TEST_USER_ID = os.getenv("TEST_USER_ID")

client = TestClient(app)


### INTEGRATION TESTS FOR TASKS - DATABASE OPERATIONS ###


# CREATE TASK
def test_create_task():
    response = client.post(
        "/tasks",
        json={
            "user_id": TEST_USER_ID,
            "name": "Test Task 1",
            "description": "Test Description",
            "due_date": "2026-04-01",
            "priority": "Low",
            "module" : "Test Module",
            "estimated_duration" : "60",
            "status": "Incomplete - Not Started"
        }
    )

    assert response.status_code == 200

    payload = response.json()
    assert ((payload["name"] == "Test Task 1") and (payload["user_id"] == TEST_USER_ID))


# CREATE INVALID TASK (NO USER ID)
def test_create_task_invalid():
    response = client.post(
        "/tasks",
        json={
            "name": "Test Task 0",
            "description": "Test Description",
            "due_date": "2026-04-01",
            "priority": "Low",
            "module" : "Test Module",
            "estimated_duration" : "60",
            "status": "Incomplete - Not Started"
        }
    )

    assert response.status_code == 400


# GET TASKS
def test_get_tasks():
    # Create Task First
    create_response = client.post(
        "/tasks",
        json={
            "user_id": TEST_USER_ID,
            "name": "Test Task 2",
            "description": "Test Description",
            "due_date": "2026-04-01",
            "priority": "Low",
            "module" : "Test Module",
            "estimated_duration" : "60",
            "status": "Incomplete - Not Started"
        }
    )

    get_response = client.get("/tasks?user_id=" + str(TEST_USER_ID))

    assert get_response.status_code == 200

    payload = get_response.json()
    assert (isinstance(payload, list) and any(item["name"] == "Test Task 2" for item in payload))


# UPDATE TASK
def test_update_task():
    # Create Task First
    create_response = client.post(
        "/tasks",
        json={
            "user_id": TEST_USER_ID,
            "name": "Test Task 3",
            "description": "Test Description",
            "due_date": "2026-04-01",
            "priority": "Low",
            "module" : "Test Module",
            "estimated_duration" : "60",
            "status": "Incomplete - Not Started"
        }
    )

    task_id = create_response.json()["id"]

    update_response = client.put(
        "/tasks/" + str(task_id),
        json={
            "user_id": TEST_USER_ID,
            "name": "Test Task 3 Updated",
            "description": "Test Description",
            "due_date": "2026-04-01",
            "priority": "Low",
            "module" : "Test Module",
            "estimated_duration" : "60",
            "status": "Incomplete - Not Started"
        }
    )

    assert update_response.status_code == 200

    get_response = client.get("/tasks?user_id=" + str(TEST_USER_ID))
    payload = get_response.json()
    assert any(item["name"] == "Test Task 3 Updated" for item in payload)


# DELETE TASK
def test_delete_task():
    # Create Task First
    create_response = client.post(
        "/tasks",
        json={
            "user_id": TEST_USER_ID,
            "name": "Test Task 4",
            "description": "Test Description",
            "due_date": "2026-04-01",
            "priority": "Low",
            "module" : "Test Module",
            "estimated_duration" : "60",
            "status": "Incomplete - Not Started"
        }
    )

    task_id = create_response.json()["id"]

    delete_response = client.delete("/tasks/" + str(task_id))

    assert delete_response.status_code == 200

    get_response = client.get("/tasks?user_id=" + str(TEST_USER_ID))
    payload = get_response.json()
    assert not (any(item["id"] == task_id for item in payload))


# DELETE INVALID TASK (DOES NOT EXIST)
def test_delete_task_invalid():
    response = client.delete("/tasks/0")

    assert response.status_code == 404
