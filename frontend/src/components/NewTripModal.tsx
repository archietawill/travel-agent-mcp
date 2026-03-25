import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Search, MapPin, Calendar, Clock, ArrowRight, X } from 'lucide-react';
import { format } from 'date-fns';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import { CHINESE_CITIES } from '../constants/cities';
import { CityConfig } from '../types';
import styles from './NewTripModal.module.css';

interface NewTripModalProps {
  onInitialize: (cities: CityConfig[], startDate: string) => void;
  isLoading: boolean;
}

export const NewTripModal: React.FC<NewTripModalProps> = ({ onInitialize, isLoading }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [selectedCities, setSelectedCities] = useState<CityConfig[]>([]);
  const [startDate, setStartDate] = useState<Date | null>(null);
  
  const searchRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredCities = useMemo(() => {
    return CHINESE_CITIES.filter(city => 
      city.toLowerCase().includes(searchTerm.toLowerCase()) && 
      !selectedCities.some(sc => sc.name === city)
    ).slice(0, 20); // Show more matching cities (up to 20)
  }, [searchTerm, selectedCities]);

  const handleAddCity = (cityName: string) => {
    setSelectedCities([...selectedCities, { name: cityName, days: 3 }]);
    setSearchTerm('');
    setIsDropdownOpen(false);
  };

  const handleRemoveCity = (cityName: string) => {
    setSelectedCities(selectedCities.filter(c => c.name !== cityName));
  };

  const handleUpdateDays = (cityName: string, days: number) => {
    setSelectedCities(selectedCities.map(c => 
      c.name === cityName ? { ...c, days: Math.max(1, days) } : c
    ));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedCities.length > 0 && startDate) {
      const dateStr = format(startDate, 'yyyy-MM-dd');
      onInitialize(selectedCities, dateStr);
    }
  };

  const isValid = selectedCities.length > 0 && startDate !== null;

  return (
    <div className={styles.modalOverlay}>
      <div className={`${styles.modalContent} glass-panel`}>
        <div className={styles.header}>
          <h2>Where to, next?</h2>
          <p>Let's map out your journey through China.</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.header}>
          
          <div className={styles.formGroup}>
            <label>Trip Start Date</label>
            <div className={styles.searchContainer}>
              <Calendar className={styles.searchIcon} size={18} />
              <DatePicker
                selected={startDate}
                onChange={(date: Date | null) => setStartDate(date)}
                className={styles.searchInput}
                placeholderText="Select start date"
                dateFormat="yyyy-MM-dd"
                minDate={new Date()}
                required
              />
            </div>
          </div>

          <div className={styles.formGroup} ref={searchRef}>
            <label>Destinations</label>
            <div className={styles.searchContainer}>
              <Search className={styles.searchIcon} size={18} />
              <input 
                type="text" 
                className={styles.searchInput}
                placeholder="Search an amazing city..."
                value={searchTerm}
                onChange={e => {
                  setSearchTerm(e.target.value);
                  setIsDropdownOpen(true);
                }}
                onFocus={() => setIsDropdownOpen(true)}
              />
              
              {isDropdownOpen && filteredCities.length > 0 && (
                <div className={styles.dropdown}>
                  {filteredCities.map(city => (
                    <div 
                      key={city} 
                      className={styles.dropdownItem}
                      onClick={() => handleAddCity(city)}
                    >
                      <MapPin size={16} style={{ display: 'inline', marginRight: '8px', color: 'var(--accent)' }}/>
                      {city}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
            {selectedCities.map(city => (
              <div key={city.name} className={styles.selectedCity}>
                <div className={styles.cityInfo}>
                  <button 
                    type="button" 
                    className="btn-ghost" 
                    style={{ padding: '4px' }}
                    onClick={() => handleRemoveCity(city.name)}
                  >
                    <X size={16} />
                  </button>
                  <span>{city.name}</span>
                </div>
                <div className={styles.daysInput}>
                  <Clock size={16} color="var(--text-secondary)" />
                  <input 
                    type="number" 
                    min="1" 
                    max="14"
                    value={city.days}
                    onChange={(e) => handleUpdateDays(city.name, parseInt(e.target.value) || 1)}
                  />
                  <span>days</span>
                </div>
              </div>
            ))}
          </div>

          <div className={styles.actions}>
            <button 
              type="submit" 
              className="btn-primary"
              disabled={!isValid || isLoading}
              style={{ opacity: (!isValid || isLoading) ? 0.5 : 1, display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              {isLoading ? 'Initializing...' : 'Start Planning'}
              {!isLoading && <ArrowRight size={18} />}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
