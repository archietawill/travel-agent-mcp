export interface CityConfig {
  name: string;
  days: number;
}

export interface POICard {
  id: string;
  name: string;
  rating?: number;
  address?: string;
  description?: string;
  price?: string;
  opening_hours?: string;
  image_url?: string;
  coordinates?: {
    lat: number;
    lng: number;
  };
  category?: string;
  tags?: string[];
}

export interface SeatOption {
  type: string;
  price: string;
}

export interface TrainInfo {
  id: string;
  train_number: string;
  departure_date: string;
  departure_time: string;
  arrival_time: string;
  departure_station: string;
  arrival_station: string;
  duration: string;
  seat_options: SeatOption[];
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
}

export interface ChatResponse {
  text: string;
  widget: "poi_cards" | "train_list" | null;
  data: any;
}

export interface ItineraryItem {
  id: string;
  time: string;
  title: string;
  type: "poi" | "transit" | "hotel";
  related_id?: string;
  estimated_duration?: string;
  notes?: string;
}

export interface ItineraryDay {
  day_number: number;
  date: string;
  city: string;
  items: ItineraryItem[];
}

export interface Itinerary {
  title: string;
  total_days: number;
  days: ItineraryDay[];
}
