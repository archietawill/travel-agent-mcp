from typing import List, Dict, Any, Tuple, Optional
from services.llm_service import get_llm_service
from services.trip_service import get_trip_service
from mcp_manager import get_mcp_manager
from models import SynthesizeRequest, Itinerary, ItineraryDay, ItineraryItem
import json

class SynthesisService:
    def __init__(self):
        self.llm_service = get_llm_service()
        self.trip_service = get_trip_service()
        self.mcp_manager = get_mcp_manager()

    def _extract_json(self, text: str) -> str:
        if not text:
            return ""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def build_synthesis_prompt(self, places: List[Dict], pinned_trains: Optional[List[Dict]] = None) -> str:
        trip = self.trip_service.get_trip_details()
        if not trip:
            raise ValueError("No active trip. Please initialize a trip first.")
        
        cities = trip["cities"]
        total_days = trip["total_days"]
        start_date = trip["start_date"]
        
        cities_info = "\n".join([
            f"- {city['name']}: {city['days']} days"
            for city in cities
        ])
        
        places_info = "\n".join([
            f"- {p.get('name', 'Unknown')} ({p.get('category', 'unknown')}) at {p.get('coordinates', 'unknown')}"
            for p in places
        ])
        
        return f"""You are a travel itinerary planner. Create an optimized day-by-day itinerary.

Trip Details:
- Cities: {cities_info}
- Total Days: {total_days}
- Start Date: {start_date}

Places to Include:
{places_info}

Pinned Transits (User has specifically chosen these trains):
{json.dumps(pinned_trains) if pinned_trains else "None"}

Instructions:
1. Group places by city
2. Within each city, group nearby places together on the same day
3. Consider opening hours when scheduling
4. Calculate travel time between places using distance tools
5. Assign specific times (e.g., "09:00 AM", "02:30 PM")
6. Include estimated duration for each activity
7. Add transit (trains) between cities on appropriate days
8. Create a logical flow of activities

Response format:
{{
  "title": "Trip Title",
  "total_days": {total_days},
  "days": [
    {{
      "day_number": 1,
      "date": "2026-03-25",
      "city": "Beijing",
      "items": [
        {{
          "id": "item_1",
          "time": "09:00 AM",
          "title": "Place Name",
          "type": "poi" or "transit" or "hotel",
          "related_id": "poi_123",
          "estimated_duration": "2 hours",
          "notes": "Optional notes"
        }}
      ]
    }}
  ]
}}

Item types:
- poi: Places to visit (attractions, restaurants, shopping)
- transit: Train travel between cities
- hotel: Hotel stays

CRITICAL: 
1. Use "YYYY-MM-DD" for all date fields.
2. If Pinned Transits are provided, YOU MUST include them in the itinerary at the specified times and dates. Do not change their details.
3. Schedule times in "09:00 AM" format.
"""

    def calculate_distance(self, origin: Dict[str, float], destination: Dict[str, float]) -> Dict[str, Any]:
        """Calculate distance and travel time between two coordinates using Amap."""
        try:
            result = self.mcp_manager.call_tool(
                "amap_maps_distance",
                {
                    "origins": f"{origin['lng']},{origin['lat']}",
                    "destination": f"{destination['lng']},{destination['lat']}",
                    "type": "1"  # Driving distance
                }
            )
            return json.loads(result)
        except Exception as e:
            print(f"Error calculating distance: {e}")
            return {"distance": 0, "duration": 0}

    def cluster_places_by_proximity(self, places: List[Dict]) -> List[List[Dict]]:
        """Group places that are close to each other."""
        if len(places) <= 1:
            return [places]
        
        clusters = []
        unvisited = places.copy()
        
        while unvisited:
            current_cluster = [unvisited.pop(0)]
            
            i = 0
            while i < len(unvisited):
                place = unvisited[i]
                is_close = False
                
                for cluster_place in current_cluster:
                    coords1 = cluster_place.get("coordinates", {})
                    coords2 = place.get("coordinates", {})
                    
                    if coords1 and coords2:
                        distance_info = self.calculate_distance(coords1, coords2)
                        # Distance logic here based on amap_maps_distance response structure
                        # the result often has "results": [{"distance": "1234", ...}]
                        distance = 0
                        if distance_info and "results" in distance_info and distance_info["results"]:
                            try:
                                distance = int(distance_info["results"][0].get("distance", 0))
                            except ValueError:
                                pass
                        
                        # If within 5km, consider them close
                        if distance > 0 and distance < 5000:
                            is_close = True
                            break
                
                if is_close:
                    current_cluster.append(place)
                    unvisited.pop(i)
                else:
                    i += 1
            
            clusters.append(current_cluster)
        
        return clusters

    def synthesize(self, request: SynthesizeRequest) -> Itinerary:
        # Build prompt
        places_dicts = [p.model_dump() for p in request.places]
        trains_dicts = [t.model_dump() for t in request.trains] if request.trains else []
        prompt = self.build_synthesis_prompt(places_dicts, trains_dicts)
        
        # Call LLM with structured output
        response = self.llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # Parse response
        try:
            json_str = self._extract_json(response.content)
            result = json.loads(json_str)
            return self._parse_itinerary(result)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    def _parse_itinerary(self, result: Dict[str, Any]) -> Itinerary:
        days = []
        for day_data in result.get("days", []):
            items = []
            for item_data in day_data.get("items", []):
                item = ItineraryItem(**item_data)
                items.append(item)
            
            day = ItineraryDay(
                day_number=day_data["day_number"],
                date=day_data["date"],
                city=day_data["city"],
                items=items
            )
            days.append(day)
        
        return Itinerary(
            title=result.get("title", "Generated Trip"),
            total_days=result.get("total_days", 1),
            days=days
        )

# Global instance
_synthesis_service: Optional[SynthesisService] = None

def get_synthesis_service() -> SynthesisService:
    global _synthesis_service
    if _synthesis_service is None:
        _synthesis_service = SynthesisService()
    return _synthesis_service
