import os
import requests
from dotenv import load_dotenv
import json

# load environment variables
load_dotenv()
API_URL = os.getenv("TES_API_URL")
API_KEY = os.getenv("TES_API_KEY")

headers = {
    "X-API-KEY": API_KEY,
    "Accept": "application/json"
}

def print_response(label, response):
    """Pretty print response with status and sample data"""
    print(f"\n{'='*50}")
    print(f"TEST: {label}")
    print(f"URL: {response.url}")
    print(f"Status: {response.status_code}")

    try:
        data = response.json()
        print("\nSample Response:")
        # print first 500 chars since the responses are really long
        print(json.dumps(data, indent=2)[:500])
        if isinstance(data, dict) and "entry" in data:
            print(f"\nFound {len(data['entry'])} items")
    except ValueError:
        print("Response (text):", response.text[:500])

def run_tests():
    # 1. get active ValueSets
    r = requests.get(f"{API_URL}/ValueSet?status=active", headers=headers)
    print_response("1. Get active ValueSets", r)

    # 2. search by code
    r = requests.get(f"{API_URL}/ValueSet?code=9991008", headers=headers)
    print_response("2. Search by code (9991008)", r)

    # 3. search by condition (Hepatitis B)
    r = requests.get(f"{API_URL}/ValueSet?context=http://snomed.info/sct|66071002", headers=headers)
    print_response("3. Search by condition (Hepatitis B)", r)

    # 4. search by title/description
    r = requests.get(f"{API_URL}/ValueSet?title=Hepatitis+B&status=active", headers=headers)
    print_response("4. Search by title (Hepatitis B)", r)

    r = requests.get(f"{API_URL}/ValueSet?description=Influenza", headers=headers)
    print_response("4. Search by description (Influenza)", r)

    # 5. find ValueSets from CodeSystem
    r = requests.get(f"{API_URL}/ValueSet?reference=http://loinc.org", headers=headers)
    print_response("5. Find ValueSets from LOINC", r)

    # 6. pagination example
    r = requests.get(f"{API_URL}/ValueSet?_count=5", headers=headers)
    print_response("6. Pagination (_count=5)", r)

    # 7. ValueSet operations (need real ValueSet IDs)
    # first find a real ValueSet ID from previous responses
    if r.status_code == 200:
        try:
            vs_id = r.json()["entry"][0]["resource"]["id"]
            r = requests.get(f"{API_URL}/ValueSet/{vs_id}/$expand", headers=headers)
            print_response(f"7a. $expand for ValueSet {vs_id}", r)

            # validate a sample code if expansion exists
            if r.status_code == 200:
                expanded = r.json()
                if "expansion" in expanded and "contains" in expanded["expansion"]:
                    sample_code = expanded["expansion"]["contains"][0]
                    code = sample_code["code"]
                    system = sample_code["system"]
                    r = requests.get(
                        f"{API_URL}/ValueSet/{vs_id}/$validate-code?code={code}&system={system}",
                        headers=headers
                    )
                    print_response(f"7b. Validate code {code} ({system})", r)
        except (KeyError, IndexError):
            print("\nSkipping operation tests - no valid ValueSet ID found")

if __name__ == "__main__":
    print("Starting TES API Validation...")
    print(f"Testing against: {API_URL}")
    run_tests()
    print("\nValidation complete!")
