import axios from 'axios';
import { CityConfig, ChatMessage, POICard, Itinerary, TrainInfo } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // 1. Initialize Trip
  initializeTrip: async (cities: CityConfig[], startDate: string) => {
    const response = await apiClient.post('/trip/initialize', {
      cities,
      start_date: startDate,
    });
    return response.data;
  },

  // 2. Chat with Agent Stream
  chatStream: async (message: string, history: ChatMessage[], onEvent: (event: any) => void): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_history: history })
    });
    
    if (!response.ok) throw new Error('Network response was not ok');
    
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    
    if (reader) {
      // Buffer for incomplete chunks
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Keep the last partial line in the buffer
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              onEvent(data);
            } catch (e) {
              console.error('Error parsing streaming data', e);
            }
          }
        }
      }
    }
  },

  // 3. Synthesize Itinerary
  synthesizeItinerary: async (places: POICard[], trains: TrainInfo[] = []): Promise<{ success: boolean; message: string; itinerary: Itinerary }> => {
    const response = await apiClient.post('/itinerary/synthesize', {
      places,
      trains,
    });
    return response.data;
  }
};
