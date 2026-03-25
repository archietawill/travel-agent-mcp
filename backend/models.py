from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union

class CityConfig(BaseModel):
    name: str
    days: int

class InitializeTripRequest(BaseModel):
    cities: List[CityConfig]
    start_date: str

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []


class InitializeTripResponse(BaseModel):
    success: bool
    message: str
    trip_id: str

class Coordinates(BaseModel):
    lat: float
    lng: float

class POICard(BaseModel):
    id: str = Field(default_factory=lambda: "")
    image_url: Optional[str] = None
    name: str = ""
    rating: float = 0.0
    address: str = ""
    description: str = ""
    price: str = ""
    opening_hours: str = ""
    coordinates: Optional[Coordinates] = None
    category: str = "attraction"  # Removed Literal to be safe
    tags: List[str] = []

class POICardsResponse(BaseModel):
    places: List[POICard]

class SeatOption(BaseModel):
    type: str
    price: str

class TrainInfo(BaseModel):
    id: str = Field(default_factory=lambda: "")
    train_number: str = ""
    departure_date: str = ""
    departure_time: str = ""
    arrival_time: str = ""
    departure_station: str = ""
    arrival_station: str = ""
    duration: str = ""
    seat_options: List[SeatOption] = []

class TrainListResponse(BaseModel):
    trains: List[TrainInfo]

class SynthesizeRequest(BaseModel):
    places: List[POICard]
    trains: Optional[List[TrainInfo]] = []

class ChatResponseSchema(BaseModel):
    text: str
    widget: Optional[Literal["poi_cards", "train_list"]] = None
    data: Optional[Union[POICardsResponse, TrainListResponse]] = None

class ChatResponse(BaseModel):
    text: str
    widget: Optional[Literal["poi_cards", "train_list"]] = None
    data: Optional[Union[POICardsResponse, TrainListResponse]] = None

class ItineraryItem(BaseModel):
    id: str
    time: str
    title: str
    type: Literal["poi", "transit", "hotel"]
    related_id: Optional[str] = None
    estimated_duration: Optional[str] = None
    notes: Optional[str] = None

class ItineraryDay(BaseModel):
    day_number: int
    date: str
    city: str
    items: List[ItineraryItem]

class Itinerary(BaseModel):
    title: str
    total_days: int
    days: List[ItineraryDay]

class SynthesizeResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    itinerary: Optional[Itinerary] = None
