from typing import Optional, List, Dict
from models import CityConfig, InitializeTripRequest, ChatMessage
import uuid

class TripService:
    def __init__(self):
        self.active_trip: Optional[Dict] = None
        self.conversation_history: List[ChatMessage] = []

    def initialize_trip(self, request: InitializeTripRequest) -> dict:
        trip_id = f"trip_{uuid.uuid4().hex[:8]}"
        
        self.active_trip = {
            "trip_id": trip_id,
            "cities": [{"name": city.name, "days": city.days} for city in request.cities],
            "start_date": request.start_date,
            "total_days": sum(city.days for city in request.cities)
        }
        
        self.conversation_history = []
        
        return {
            "trip_id": trip_id,
            "message": f"Trip initialized: {len(request.cities)} cities, {self.active_trip['total_days']} days"
        }

    def get_trip_details(self) -> Optional[Dict]:
        return self.active_trip

    def add_message(self, message: ChatMessage):
        self.conversation_history.append(message)

    def get_conversation_history(self) -> List[ChatMessage]:
        return self.conversation_history

    def reset(self):
        self.active_trip = None
        self.conversation_history = []

_trip_service: Optional[TripService] = None

def get_trip_service() -> TripService:
    global _trip_service
    if _trip_service is None:
        _trip_service = TripService()
    return _trip_service
