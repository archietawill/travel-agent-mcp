import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Sparkles } from 'lucide-react';
import { POICard } from './POICard';
import { TrainList } from './TrainList';
import { POICard as POICardType, TrainInfo } from '../types';
import styles from './ChatPanel.module.css';

export interface AppMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  widget?: 'poi_cards' | 'train_list' | null;
  widgetData?: any;
}

interface ChatPanelProps {
  messages: AppMessage[];
  agentStatus: string | null;
  onSendMessage: (msg: string) => void;
  onAddPlace: (place: POICardType) => void;
  onAddTrain: (train: TrainInfo) => void;
  isTrainAdded: (trainId: string) => boolean;
  placeholderIds: string[];
}

const SUGGESTIONS = [
  "Recommend me top attractions",
  "Recommend me local restaurants",
  "Recommend me 5-star hotels",
  "Recommend me bullet trains"
];

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  agentStatus,
  onSendMessage,
  onAddPlace,
  onAddTrain,
  isTrainAdded,
  placeholderIds
}) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, agentStatus]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !agentStatus) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.messages}>
        {messages.map((msg) => (
          <div key={msg.id} className={`${styles.messageRow} ${styles[msg.role]}`}>
            <div className={styles.bubble}>

              {/* Text Content */}
              {msg.content && (
                <div className={styles.textContent}>
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              )}

              {/* Dynamic Widgets */}
              {msg.widget === 'poi_cards' && msg.widgetData?.places && (
                <div className={`${styles.widgets} ${styles.poi_cards}`}>
                  {msg.widgetData.places.map((place: POICardType, idx: number) => (
                    <POICard
                      key={place.id || idx}
                      place={place}
                      onAdd={onAddPlace}
                      isAdded={placeholderIds.includes(place.id)}
                    />
                  ))}
                </div>
              )}

              {msg.widget === 'train_list' && msg.widgetData?.trains && (
                <div className={styles.widgets}>
                  <TrainList
                    trains={msg.widgetData.trains as TrainInfo[]}
                    onAdd={onAddTrain}
                    isAdded={isTrainAdded}
                  />
                </div>
              )}

            </div>
          </div>
        ))}

        {agentStatus && (
          <div className={`${styles.messageRow} ${styles.assistant}`}>
            <div className={styles.loadingIndicator}>
              <Sparkles size={16} color="var(--accent)" />
              <span>{agentStatus}</span>
              <div className={styles.dot}></div>
              <div className={styles.dot}></div>
              <div className={styles.dot}></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className={styles.inputArea}>
        <div className={styles.suggestions}>
          {SUGGESTIONS.map((s, i) => (
            <button
              key={i}
              className={styles.suggestionChip}
              onClick={() => onSendMessage(s)}
              disabled={!!agentStatus}
            >
              {s}
            </button>
          ))}
        </div>
        <form onSubmit={handleSubmit} className={styles.inputForm}>
          <input
            type="text"
            placeholder="E.g. Find me bullet trains from Beijing to Shanghai..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!!agentStatus}
          />
          <button type="submit" className={styles.sendButton} disabled={!input.trim() || !!agentStatus}>
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};
