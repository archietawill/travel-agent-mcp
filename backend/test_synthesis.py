import json
from models import InitializeTripRequest, CityConfig, SynthesizeRequest
from services.trip_service import get_trip_service
from services.synthesis_service import get_synthesis_service

def test_synthesis():
    
    # 1. Initialize Trip first
    print("\n[========================================]")
    print("Initializing Trip...")
    trip_req = InitializeTripRequest(
        cities=[CityConfig(name="Beijing", days=3)],
        start_date="2025-04-01"
    )
    trip_service = get_trip_service()
    trip_result = trip_service.initialize_trip(trip_req)
    print("Trip Init Result:", trip_result)
    
    # 2. Synthesize with places
    print("\n[========================================]")
    print("Synthesizing Itinerary...")
    
    # Adding a couple places in Beijing
    places = [
      {
        "id": "poi_1",
        "name": "Forbidden City",
        "category": "attraction",
        "coordinates": {"lat": 39.9163, "lng": 116.3972},
        "opening_hours": "8:30 AM - 5:00 PM"
      },
      {
        "id": "poi_2",
        "name": "Temple of Heaven",
        "category": "attraction",
        "coordinates": {"lat": 39.8836, "lng": 116.4128},
        "opening_hours": "8:00 AM - 5:30 PM"
      },
      {
        "id": "poi_3",
        "name": "Quanjude Roast Duck",
        "category": "restaurant",
        "coordinates": {"lat": 39.897, "lng": 116.397},
        "opening_hours": "11:00 AM - 9:00 PM"
      }
    ]
    
    synth_req = SynthesizeRequest(places=places)
    synthesis_service = get_synthesis_service()
    
    itinerary = synthesis_service.synthesize(synth_req)
    print("\nFINAL RESULT:")
    print(json.dumps(itinerary.model_dump(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_synthesis()
