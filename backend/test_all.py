from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def run_tests():
    print("\n=== Test 1: Health check ===")
    response = client.get("/health")
    print(response.json())

    print("\n=== Test 2: Initialize trip ===")
    response = client.post("/api/trip/initialize", json={
        "cities": [{"name": "Beijing", "days": 3}, {"name": "Shanghai", "days": 2}],
        "start_date": "2025-04-01"
    })
    print(response.json())

    print("\n=== Test 3: Chat for POIs ===")
    response = client.post("/api/chat", json={
        "message": "Find 3 popular attractions in Beijing",
        "conversation_history": []
    })
    res_json = response.json()
    print("Widget:", res_json.get("widget"))
    places = res_json.get("data", {}).get("places", [])
    print(f"Found {len(places)} places")
    if places and len(places) > 0:
        print("First place image URL:", places[0].get("image_url"))

    print("\n=== Test 4: Chat for trains ===")
    response = client.post("/api/chat", json={
        "message": "Find trains from Beijing to Shanghai on April 4, 2025",
        "conversation_history": []
    })
    res_json = response.json()
    print("Widget:", res_json.get("widget"))
    trains = res_json.get("data", {}).get("trains", [])
    print(f"Found {len(trains)} trains")

    print("\n=== Test 5: Synthesize itinerary ===")
    response = client.post("/api/itinerary/synthesize", json={
        "places": [
          {
            "id": "poi_1",
            "name": "Forbidden City",
            "category": "attraction",
            "coordinates": {"lat": 39.9163, "lng": 116.3972},
            "opening_hours": "8:30 AM - 5:00 PM"
          },
          {
            "id": "poi_2",
            "name": "Great Wall",
            "category": "attraction",
            "coordinates": {"lat": 40.4319, "lng": 116.5704},
            "opening_hours": "7:30 AM - 6:00 PM"
          }
        ]
    })
    res_json = response.json()
    print("Synthesis Success:", res_json.get("success"))
    print("Total Days:", res_json.get("itinerary", {}).get("total_days"))

if __name__ == "__main__":
    run_tests()
