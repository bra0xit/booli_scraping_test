"""
Test if Hittamäklare has an API we can use
"""
import requests

# Try to get agent data via potential API endpoints
agent_id = "11542"  # Otilia Håkansson
agency_id = "32"    # Skandiamäklarna

print("Testing potential Hittamäklare API endpoints...")

# Try different endpoint patterns
endpoints = [
    f"https://www.hittamaklare.se/api/agent/{agent_id}",
    f"https://www.hittamaklare.se/api/agents/{agent_id}",
    f"https://www.hittamaklare.se/api/maklare/{agent_id}",
    f"https://api.hittamaklare.se/agent/{agent_id}",
    f"https://api.hittamaklare.se/maklare/{agent_id}",
]

for endpoint in endpoints:
    print(f"\nTrying: {endpoint}")
    try:
        response = requests.get(endpoint, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"SUCCESS! Response: {response.text[:500]}")
        elif response.status_code == 404:
            print("Not found")
        else:
            print(f"Other status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

# Try agency endpoints
print("\n" + "="*80)
print("Testing agency endpoints...")
print("="*80)

agency_endpoints = [
    f"https://www.hittamaklare.se/api/agency/{agency_id}",
    f"https://www.hittamaklare.se/api/maklarbyra/{agency_id}",
    f"https://api.hittamaklare.se/agency/{agency_id}",
]

for endpoint in agency_endpoints:
    print(f"\nTrying: {endpoint}")
    try:
        response = requests.get(endpoint, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"SUCCESS! Response: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
