import os
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from app.main import app


# TO RUN ALL TESTS:             python -m pytest tests/test_ai.py -p no:warnings
# TO RUN A SPECIFIC TEST:       python -m pytest tests/test_ai.py::test_name_of_test -p no:warnings




load_dotenv()

TEST_USER_ID = os.getenv("TEST_USER_ID")

client = TestClient(app)


### INTEGRATION TESTS FOR AI-RELATED FEATURES - DATABASE OPERATIONS AND AI API OPERATIONS ###


### DATABASE OPERATIONS ###


# GET QUIZ RESULTS
def test_get_quiz_results():
    # Create Document First
    create_response = client.post(
        "/documents",
        json={
            "user_id": TEST_USER_ID,
            "file_name": "Test AI Document 1.pdf",
            "file_location": "Test Location",
            "module": "Test Module"
        }
    )
    # Create Quiz Result First
    create_response = client.post(
        "/ai/quiz_result",
        json={
            "user_id": TEST_USER_ID,
            "file_name": "Test AI Document 1.pdf",
            "score": 0,
            "total_questions": 10
        }
    )

    get_response = client.get("/quiz_results?user_id=" + str(TEST_USER_ID))

    assert get_response.status_code == 200

    payload = get_response.json()
    assert (isinstance(payload, list) and any(((item["file_name"] == "Test AI Document 1.pdf") and (item["score"] == 0)) for item in payload))


# GET AI JOURNALS
def test_get_ai_journals():
    # Create Journal First
    create_response = client.post(
        "/journals",
        json={
            "user_id": TEST_USER_ID,
            "date": "2026-03-01",
            "entry": "Test AI Entry 1"
        }
    )
    # Perform Journal Analysis First (Creates An AI Journal Row)
    create_response = client.post(
        "/ai/journal_analysis",
        json={
            "user_id": TEST_USER_ID,
            "date": "2026-03-01",
            "entry": "Test AI Entry 1"
        }
    )

    get_response = client.get("/ai_journals?user_id=" + str(TEST_USER_ID))

    assert get_response.status_code == 200

    payload = get_response.json()
    assert (isinstance(payload, list) and any(item["date"] == "2026-03-01" for item in payload))


# GET JOURNALING TRENDS
def test_get_journaling_trends():
    # Create Journal First
    create_response = client.post(
        "/journals",
        json={
            "user_id": TEST_USER_ID,
            "date": "2026-03-02",
            "entry": "I feel great today"
        }
    )
    # Perform Journal Analysis First (Creates An AI Journal Row)
    create_response = client.post(
        "/ai/journal_analysis",
        json={
            "user_id": TEST_USER_ID,
            "date": "2026-03-02",
            "entry": "I feel great today"
        }
    )

    get_response = client.get("/ai/journaling_trends?user_id=" + str(TEST_USER_ID))

    assert get_response.status_code == 200

    payload = get_response.json()
    assert (isinstance(payload, dict) and isinstance(payload["mood_history"], list))


# GET ACADEMIC TRENDS
def test_get_academic_trends():
    # Create Document First
    create_response = client.post(
        "/documents",
        json={
            "user_id": TEST_USER_ID,
            "file_name": "Test AI Document 2.pdf",
            "file_location": "Test Location",
            "module": "Test Module"
        }
    )
    # Create Quiz Result First
    create_response = client.post(
        "/ai/quiz_result",
        json={
            "user_id": TEST_USER_ID,
            "file_name": "Test AI Document 2.pdf",
            "score": 5,
            "total_questions": 10
        }
    )

    get_response = client.get("/ai/academic_trends?user_id=" + str(TEST_USER_ID))

    assert get_response.status_code == 200

    payload = get_response.json()
    assert (isinstance(payload, dict) and isinstance(payload["module_scores_history"], dict) and isinstance(payload["module_scores_averages"], list))


# GET DOCUMENT AI CONTENT
def test_get_document_ai_content():
    # Create Document First
    create_response = client.post(
        "/documents",
        json={
            "user_id": TEST_USER_ID,
            "file_name": "Test AI Document 3.pdf",
            "file_location": "Test Location",
            "module": "Test Module"
        }
    )

    get_response = client.get("/ai/Test AI Document 3.pdf")

    assert get_response.status_code == 200

    payload = get_response.json()
    assert isinstance(payload, dict)


# UPLOAD QUIZ RESULT
def test_upload_quiz_result():
    # Create Document First
    response = client.post(
        "/documents",
        json={
            "user_id": TEST_USER_ID,
            "file_name": "Test AI Document 4.pdf",
            "file_location": "Test Location",
            "module": "Test Module"
        }
    )
    response = client.post(
        "/ai/quiz_result",
        json={
            "user_id": TEST_USER_ID,
            "file_name": "Test AI Document 4.pdf",
            "score": 10,
            "total_questions": 10
        }
    )

    assert response.status_code == 200

    payload = response.json()
    assert (payload["file_name"] == "Test AI Document 4.pdf") and (payload["score"] == 10)




### AI OPERATIONS ###

# A TEST DOCUMENT WAS MANUALLY UPLOADED TO THE TEST ACCOUNT BEFOREHAND FOR THE CONTENT GENERATION TESTS


# GENERATE SUMMARY
def test_generate_summary():
    response = client.post(
        "/ai",
        json={
            "file_name": "Security Engineering Week 2 Test.pdf",
            "type": "summary"
        }
    )

    assert response.status_code == 200

    payload = response.json()
    assert (isinstance(payload, dict) and isinstance(payload["summary"], str))
    

# GENERATE FLASHCARDS
def test_generate_flashcards():
    response = client.post(
        "/ai",
        json={
            "file_name": "Security Engineering Week 2 Test.pdf",
            "type": "flashcards"
        }
    )

    assert response.status_code == 200

    payload = response.json()
    assert (isinstance(payload, dict) and isinstance(payload["flashcards"], list))
    assert all((("question" in item) and ("answer" in item)) for item in payload["flashcards"])
    

# GENERATE QUIZ
def test_generate_quiz():
    response = client.post(
        "/ai",
        json={
            "file_name": "Security Engineering Week 2 Test.pdf",
            "type": "quiz"
        }
    )

    assert response.status_code == 200

    payload = response.json()
    assert (isinstance(payload, dict) and isinstance(payload["quiz"], list))
    assert all((("question" in item) and ("answer" in item) and ("options" in item)) for item in payload["quiz"])
    assert all((question_set["answer"] in ["A", "B", "C", "D"]) for question_set in payload["quiz"])
    assert all((all(letter in ''.join(question_set["options"]) for letter in ["A)", "B)", "C)", "D)"]) or all(letter in ''.join(question_set["options"]) for letter in ["A.", "B.", "C.", "D."])) for question_set in payload["quiz"])
    

# ASK AI QUESTION
def test_ask_question():
    response = client.post(
        "/ai/ask_question",
        json={
            "summary": """
Linear regression is a fundamental method used to model the relationship between inputs and outputs, assuming that outputs depend on inputs. It aims to approximate any function y = f(x), where x is a vector of input features. Among various regression techniques, linear regression is the simplest, expressing the output y as a weighted sum (linear combination) of input features. Mathematically, this is represented as y-hat = (w-transpose * x) + b, where w is a vector of weights, x is the input vector, and b is a bias term. Often, for simplicity, the bias is assumed to be zero.

When dealing with multiple examples, the input data is organized into a design matrix X, where each row corresponds to an example and each column to a feature. If there are n examples and d features, X is an n by d matrix. Multiplying X by the weight vector w produces a vector of predicted outputs y-hat for all examples simultaneously. Adding the bias term b (a scalar) is done through broadcasting. The actual outputs, called labels and stored in vector y, are what the model aims to predict accurately.

To create an effective model, we need to find the best weights w and bias b that minimize the difference between predicted outputs y-hat and actual outputs y. This requires a loss function, which measures the error between predictions and true values, and an optimization algorithm that adjusts the weights to reduce this loss. The most common loss function in linear regression is the squared error, which penalizes large deviations between predicted and actual values.

In the special case of a single feature (1D input), the model simplifies to y-hat = w * x + b, representing a line with slope w and intercept b. The goal is to find the best-fitting line. This can be solved analytically using the formula w* = (X-transpose * X)^-1 * X-transpose * y, which provides the optimal weights directly. This closed-form solution is possible because linear regression is simple and convex.

For more complex problems or when an analytic solution is not feasible, iterative optimization methods like Gradient Descent (GD) are used. GD starts with random initial weights and iteratively updates them in the direction that reduces the loss. The update rule is w_new = w_old - (learning_rate * gradient_of_loss), where the gradient indicates how the loss changes with respect to each weight. The learning rate controls the step size of each update. Since computing gradients over the entire dataset can be slow, a variant called Minibatch Stochastic Gradient Descent uses small subsets (batches) of data to approximate the gradient, making the process more efficient. Both learning rate and batch size are hyperparameters that need to be chosen carefully.
            """,
            "question": "What is the difference between linear regression and non-linear regression? Are they similar?"
        }
    )

    assert response.status_code == 200

    payload = response.json()
    assert (isinstance(payload, dict) and isinstance(payload["answer"], str))
    

# PROCESS JOURNAL ANALYSIS
def test_process_journal_analysis():
    # Create Journal First
    create_response = client.post(
        "/journals",
        json={
            "user_id": TEST_USER_ID,
            "date": "2026-02-01",
            "entry": "I feel really happy and productive today"
        }
    )
    
    response = client.post(
        "/ai/journal_analysis",
        json={
            "user_id": TEST_USER_ID,
            "date": "2026-02-01",
            "entry": "I feel really happy and productive today"
        }
    )

    assert response.status_code == 200

    payload = response.json()

    assert isinstance(payload, dict)
    assert (isinstance(payload["sentiment_score"], int) and (1 <= payload["sentiment_score"] <= 10))
