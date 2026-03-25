import React from 'react';
import { Train } from 'lucide-react';
import { TrainInfo } from '../types';
import styles from './TrainList.module.css';

interface TrainListProps {
  trains: TrainInfo[];
  onAdd: (train: TrainInfo) => void;
  isAdded?: (trainId: string) => boolean;
}

export const TrainList: React.FC<TrainListProps> = ({ trains, onAdd, isAdded }) => {
  if (!trains || trains.length === 0) return null;

  return (
    <div className={styles.container}>
      {trains.map((train, idx) => (
        <div key={train.id || idx} className={`${styles.trainCard} glass-panel`}>
          
          <div className={styles.header}>
            <div className={styles.trainNumber}>
              <Train size={14} style={{ display: 'inline', marginRight: '6px' }} />
              <span className="data-mono">{train.train_number}</span>
            </div>
            <div className={styles.date}>{train.departure_date}</div>
          </div>

          <div className={styles.routeInfo}>
            <div className={styles.stationBlock}>
              <span className={`data-mono ${styles.time}`}>{train.departure_time}</span>
              <span className={styles.stationName}>{train.departure_station}</span>
            </div>
            
            <div className={styles.durationBlock}>
              <span className={`data-mono ${styles.duration}`}>{train.duration}</span>
              <div className={styles.line}></div>
            </div>

            <div className={`${styles.stationBlock} ${styles.right}`}>
              <span className={`data-mono ${styles.time}`}>{train.arrival_time}</span>
              <span className={styles.stationName}>{train.arrival_station}</span>
            </div>
          </div>

          {train.seat_options && train.seat_options.length > 0 && (
            <div className={styles.seatsInfo}>
              {train.seat_options.map((seat, sIdx) => (
                <div key={sIdx} className={styles.seatBadge}>
                  <span className={styles.seatType}>{seat.type}</span>
                  <span className={`data-mono ${styles.seatPrice}`}>{seat.price}</span>
                </div>
              ))}
            </div>
          )}

          <div className={styles.footer}>
            <button 
              className={isAdded?.(train.id) ? "btn-secondary" : "btn-primaryish"} 
              style={{ width: '100%', marginTop: 'var(--space-4)', fontSize: '0.8rem', padding: '8px' }}
              onClick={() => onAdd(train)}
              disabled={isAdded?.(train.id)}
            >
              {isAdded?.(train.id) ? 'Added to Itinerary' : 'Add to Itinerary'}
            </button>
          </div>

        </div>
      ))}
    </div>
  );
};
