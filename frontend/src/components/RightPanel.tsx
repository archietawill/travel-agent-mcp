import React, { useState } from 'react';
import { Trash2, Wand2, Compass, Clock } from 'lucide-react';
import { POICard as POICardType, Itinerary, TrainInfo } from '../types';
import styles from './RightPanel.module.css';

interface RightPanelProps {
  placeholderList: POICardType[];
  placeholderTrains: TrainInfo[];
  onRemovePlaceholder: (id: string) => void;
  onRemoveTrain: (id: string) => void;
  itinerary: Itinerary | null;
  onSynthesize: () => void;
}

export const RightPanel: React.FC<RightPanelProps> = ({
  placeholderList,
  placeholderTrains,
  onRemovePlaceholder,
  onRemoveTrain,
  itinerary,
  onSynthesize
}) => {
  const [isSynthesizing, setIsSynthesizing] = useState(false);

  const handleSynthesizeClick = async () => {
    setIsSynthesizing(true);
    await onSynthesize();
    setIsSynthesizing(false);
  };

  // If itinerary is complete, show the DailyItinerary view
  if (itinerary) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h2>{itinerary.title}</h2>
          <p>{itinerary.total_days} Days curated perfectly for you.</p>
        </div>
        
        <div className={styles.content}>
          <div className={styles.itineraryContainer}>
            {itinerary.days.map((day, idx) => (
              <div key={idx} className={styles.dayBlock}>
                
                <div className={styles.dayHeader}>
                  <div className={styles.daySubtitle}>Day {day.day_number} • {day.date}</div>
                  <div className={styles.dayTitle}>{day.city}</div>
                </div>

                <div className={styles.timeline}>
                  {day.items.map((item, iIdx) => (
                    <div key={item.id || iIdx} className={styles.timelineItem}>
                      <div className={styles.timelineDot}></div>
                      
                      <div className="data-mono" style={{ color: 'var(--accent)', fontSize: '0.85rem' }}>
                        {item.time}
                      </div>
                      
                      <div className={styles.itemTitle}>{item.title}</div>
                      
                      {item.notes && <div className={styles.itemNotes}>{item.notes}</div>}
                      
                      <div className={styles.itemMeta}>
                        <span className={styles.metaBadge}>{item.type}</span>
                        {item.estimated_duration && (
                          <span className={styles.metaBadge} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Clock size={10} /> {item.estimated_duration}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Pre-synthesis view
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>Trip Planner</h2>
        <p>Save places from chat, then synthesize them into a schedule.</p>
      </div>

      <div className={styles.content}>
        {placeholderList.length === 0 && placeholderTrains.length === 0 ? (
          <div className={styles.emptyState}>
            <Compass size={48} opacity={0.2} />
            <p>Your itinerary is empty.<br/>Ask the agent for places or trains and click "Add".</p>
          </div>
        ) : (
          <div className={styles.placeholderList}>
            {/* Pinned Places */}
            {placeholderList.length > 0 && (
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>Places</h3>
                {placeholderList.map((place) => (
                  <div key={place.id} className={styles.placeItem}>
                    <div className={styles.placeInfo}>
                      <span className={styles.placeName}>{place.name}</span>
                    </div>
                    <button 
                      className={styles.removeBtn}
                      onClick={() => onRemovePlaceholder(place.id)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Pinned Trains */}
            {placeholderTrains.length > 0 && (
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>Transits</h3>
                {placeholderTrains.map((train) => (
                  <div key={train.id} className={styles.placeItem}>
                    <div className={styles.placeInfo}>
                      <span className={styles.placeName}>{train.train_number} • {train.departure_date}</span>
                      <span className={styles.placeCategory}>{train.departure_station} ➔ {train.arrival_station}</span>
                    </div>
                    <button 
                      className={styles.removeBtn}
                      onClick={() => onRemoveTrain(train.id)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            <button 
              className={`btn-primary ${styles.synthesizeBtn}`}
              onClick={handleSynthesizeClick}
              disabled={isSynthesizing || (placeholderList.length === 0 && placeholderTrains.length === 0)}
            >
              {isSynthesizing ? 'Synthesizing...' : 'Synthesize Itinerary'}
              {!isSynthesizing && <Wand2 size={16} />}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
