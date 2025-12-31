
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_result(feature, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {feature}: {details}")

def test_backend():
    print("🚀 Starting Backend Feature Tests...\n")

    # 1. Test Chatbot
    try:
        response = requests.post(f"{BASE_URL}/chat", json={
            "message": "What is this document about?",
            "document_text": "This is a circular regarding the new pension scheme 2024.",
            "doc_id": "TEST-001"
        })
        data = response.json()
        print_result("Chatbot", data.get("success"), data.get("message")[:50] + "...")
    except Exception as e:
        print_result("Chatbot", False, str(e))

    # 2. Test Compliance
    try:
        response = requests.post(f"{BASE_URL}/compliance/check", json={
            "text": "Government of India\nF.No. 12/34/2024\nDated: 25/12/2024\nSubject: Test\n(Signed)\nDirector"
        })
        data = response.json()
        print_result("Compliance", data.get("success"), f"Score: {data.get('score')}")
    except Exception as e:
        print_result("Compliance", False, str(e))

    # 3. Test Comparison
    try:
        response = requests.post(f"{BASE_URL}/compare", json={
            "doc1_text": "This is version 1 of the circular.",
            "doc2_text": "This is version 2 of the circular with changes."
        })
        data = response.json()
        print_result("Comparison", data.get("success"), f"Similarity: {data.get('similarity_score')}%")
    except Exception as e:
        print_result("Comparison", False, str(e))

    # 4. Test Grievance
    try:
        # Register
        reg_response = requests.post(f"{BASE_URL}/grievance/register", json={
            "subject": "Test Grievance",
            "details": "Testing the system",
            "priority": "high",
            "department": "IT"
        })
        reg_data = reg_response.json()
        
        # List
        list_response = requests.get(f"{BASE_URL}/grievance/list")
        list_data = list_response.json()
        
        print_result("Grievance", reg_data.get("success") and list_data.get("success"), 
                     f"Registered ID: {reg_data.get('id')}")
    except Exception as e:
        print_result("Grievance", False, str(e))

    # 5. Test Workflow
    try:
        # Create
        create_response = requests.post(f"{BASE_URL}/workflow/create", json={
            "doc_id": "DOC-TEST-001",
            "title": "Test Workflow Document",
            "priority": "urgent"
        })
        create_data = create_response.json()

        # Get
        get_response = requests.get(f"{BASE_URL}/workflow/DOC-TEST-001")
        get_data = get_response.json()
        
        print_result("Workflow", create_data.get("success") and get_data.get("success"), 
                     f"Status: {get_data.get('current_status')}")
    except Exception as e:
        print_result("Workflow", False, str(e))

    print("\n✨ Test Complete!")

if __name__ == "__main__":
    test_backend()
