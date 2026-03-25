import { useState } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { NewTripModal } from './components/NewTripModal';
import { ChatPanel, AppMessage } from './components/ChatPanel';
import { RightPanel } from './components/RightPanel';
import { api } from './services/api';
import { CityConfig, POICard, Itinerary, TrainInfo } from './types';
import './App.css';

function App() {
  const [tripInitialized, setTripInitialized] = useState(false);
  const [agentStatus, setAgentStatus] = useState<string | null>(null);
  
  // Global App State
  const [messages, setMessages] = useState<AppMessage[]>([
    { id: 'msg_0', role: 'assistant', content: 'Hello! I am your AI travel agent. Where are you dreaming of going in China?' }
  ]);
  const [placeholderList, setPlaceholderList] = useState<POICard[]>([]);
  const [placeholderTrains, setPlaceholderTrains] = useState<TrainInfo[]>([]);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);

  const handleInitializeTrip = async (selectedCities: CityConfig[], date: string) => {
    setAgentStatus('Initializing trip...');
    try {
      await api.initializeTrip(selectedCities, date);
      setTripInitialized(true);
      
      const cityNames = selectedCities.map(c => c.name).join(' and ');
      setMessages(prev => [
        ...prev,
        { id: uuidv4(), role: 'user', content: `I want to visit ${cityNames} starting ${date}.` },
        { id: uuidv4(), role: 'assistant', content: `Fantastic choice! I've set up your trip to ${cityNames}. What kind of places or activities are you interested in exploring first?` }
      ]);
    } catch (error) {
      console.error('Failed to initialize trip:', error);
      alert('Failed to initialize trip. Please ensure the backend is running.');
    } finally {
      setAgentStatus(null);
    }
  };

  const handleSendMessage = async (msgContent: string) => {
    // Optimistic user message update
    const userMsg: AppMessage = { id: uuidv4(), role: 'user', content: msgContent };
    const chatHistory = messages.map(m => ({ role: m.role, content: m.content }));
    
    setMessages(prev => [...prev, userMsg]);
    setAgentStatus('Analyzing request...');

    let tempAssistantId = uuidv4();
    try {
      await api.chatStream(msgContent, chatHistory, (event) => {
        if (event.type === 'status') {
          setAgentStatus(event.message);
        } else if (event.type === 'result') {
          const assistantMsg: AppMessage = {
            id: tempAssistantId,
            role: 'assistant',
            content: event.data.text,
            widget: event.data.widget,
            widgetData: event.data.data
          };
          setMessages(prev => [...prev, assistantMsg]);
          setAgentStatus(null);
        }
      });
    } catch (error) {
      console.error("Chat error", error);
      setMessages(prev => [...prev, { id: uuidv4(), role: 'assistant', content: 'I encountered an error trying to process your request. Please try again.' }]);
      setAgentStatus(null);
    }
  };

  const handleAddPlaceholder = (place: POICard) => {
    if (!placeholderList.find(p => p.id === place.id && p.name === place.name)) {
      setPlaceholderList(prev => [...prev, place]);
    }
  };

  const handleRemovePlaceholder = (placeId: string) => {
    setPlaceholderList(prev => prev.filter(p => p.id !== placeId));
  };

  const handleAddTrain = (train: TrainInfo) => {
    // 1. Add to pinned transits list (for synthesis)
    if (!placeholderTrains.find(t => t.id === train.id && t.train_number === train.train_number)) {
      setPlaceholderTrains(prev => [...prev, train]);
    }

    // 2. Direct injection if itinerary already exists
    if (!itinerary) {
      return;
    }

    // Find the day matching the train date
    const dayIndex = itinerary.days.findIndex(d => d.date === train.departure_date);
    
    if (dayIndex === -1) {
      alert(`This train (Date: ${train.departure_date}) doesn't fall within your current trip dates.`);
      return;
    }

    const newTransitItem: any = {
      id: uuidv4(),
      time: train.departure_time,
      title: `Train ${train.train_number}: ${train.departure_station} ➔ ${train.arrival_station}`,
      type: "transit",
      notes: `Duration: ${train.duration}. Seats: ${train.seat_options.map((s: {type: string; price: string}) => `${s.type} (${s.price})`).join(', ')}`
    };

    const newItinerary = { ...itinerary };
    newItinerary.days[dayIndex].items = [...newItinerary.days[dayIndex].items, newTransitItem];
    
    // Sort items by time if possible
    newItinerary.days[dayIndex].items.sort((a, b) => a.time.localeCompare(b.time));

    setItinerary(newItinerary);
  };

  const isTrainAdded = (trainId: string) => {
    // Check both placeholder list and active itinerary
    const inPlaceholder = placeholderTrains.some(t => t.id === trainId);
    if (inPlaceholder) return true;
    
    if (!itinerary) return false;
    return itinerary.days.some(d => d.items.some(item => item.title.includes(trainId)));
  };

  const handleSynthesize = async () => {
    setAgentStatus('Synthesizing optimized itinerary...');
    try {
      const result = await api.synthesizeItinerary(placeholderList, placeholderTrains);
      if (result.success && result.itinerary) {
        setItinerary(result.itinerary);
      }
    } catch (error) {
      console.error('Synthesis failed:', error);
      alert('Failed to synthesize itinerary.');
    } finally {
      setAgentStatus(null);
    }
  };

  const placeholderIds = placeholderList.map(p => p.id);

  return (
    <>
      {!tripInitialized && (
        <NewTripModal onInitialize={handleInitializeTrip} isLoading={!!agentStatus} />
      )}

      <main className="appContainer">
        <section className="chatSection">
          <ChatPanel 
            messages={messages}
            agentStatus={agentStatus}
            onSendMessage={handleSendMessage}
            onAddPlace={handleAddPlaceholder}
            onAddTrain={handleAddTrain}
            isTrainAdded={isTrainAdded}
            placeholderIds={placeholderIds}
          />
        </section>

        <section className="planSection">
          <RightPanel 
            placeholderList={placeholderList}
            placeholderTrains={placeholderTrains}
            onRemovePlaceholder={handleRemovePlaceholder}
            onRemoveTrain={(trainId) => setPlaceholderTrains(prev => prev.filter(t => t.id !== trainId))}
            itinerary={itinerary}
            onSynthesize={handleSynthesize}
          />
        </section>
      </main>
    </>
  );
}

export default App;
