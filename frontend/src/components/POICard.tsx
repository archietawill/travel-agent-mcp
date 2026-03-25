import React, { useState } from 'react';
import { MapPin, Clock, DollarSign, Star, Plus, Check, ImageIcon } from 'lucide-react';
import { POICard as POICardType } from '../types';
import styles from './POICard.module.css';

interface POICardProps {
  place: POICardType;
  onAdd?: (place: POICardType) => void;
  isAdded?: boolean;
}

export const POICard: React.FC<POICardProps> = ({ place, onAdd, isAdded = false }) => {
  const [added, setAdded] = useState(isAdded);

  const handleAdd = () => {
    if (onAdd && !added) {
      onAdd(place);
      setAdded(true);
    }
  };

  return (
    <div className={`${styles.card} glass-panel`}>
      <div className={styles.imageContainer}>
        {place.image_url ? (
          <img src={place.image_url} alt={place.name} className={styles.image} loading="lazy" />
        ) : (
          <div className={styles.fallbackImage}>
            <ImageIcon size={32} opacity={0.5} />
          </div>
        )}
      </div>

      <div className={styles.content}>
        <div className={styles.topContent}>
          <div className={styles.header}>
            <div>
              {place.category && <div className={styles.category}>{place.category}</div>}
              <h3 className={styles.title}>{place.name}</h3>
            </div>
            {place.rating && place.rating > 0 && (
              <div className={styles.rating}>
                <span>{place.rating}</span>
                <Star size={14} fill="currentColor" />
              </div>
            )}
          </div>

          {place.description && (
            <p className={styles.description}>{place.description}</p>
          )}
        </div>

        <div className={styles.details}>
          {place.address && (
            <div className={styles.detailItem}>
              <MapPin size={14} className={styles.detailIcon} />
              <span className="data-mono" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {place.address}
              </span>
            </div>
          )}
          {place.opening_hours && (
            <div className={styles.detailItem}>
              <Clock size={14} className={styles.detailIcon} />
              <span className="data-mono">{place.opening_hours}</span>
            </div>
          )}
          {place.price && (
            <div className={styles.detailItem}>
              <DollarSign size={14} className={styles.detailIcon} />
              <span className="data-mono">{place.price}</span>
            </div>
          )}
        </div>

        {onAdd && (
          <div className={styles.actions}>
            <button 
              className={`btn-primary ${styles.addButton}`} 
              onClick={handleAdd}
              disabled={added}
              style={{
                backgroundColor: added ? 'var(--bg-tertiary)' : 'var(--text-primary)',
                color: added ? 'var(--text-secondary)' : 'var(--bg-primary)'
              }}
            >
              {added ? (
                <>
                  <Check size={16} /> Added
                </>
              ) : (
                <>
                  <Plus size={16} /> Add 
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
