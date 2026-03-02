// src/components/AddressSearch.jsx

import { useState, useEffect, useRef } from 'react';
import { searchAddress } from '../services/api';
import { Search, X } from 'lucide-react';

export default function AddressSearch({ value, onChange, placeholder }) {
  const [input, setInput] = useState(value || '');
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const suggestionsRef = useRef(null);

  // Search for addresses as user types
  useEffect(() => {
    if (input.length < 3) {
      setSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const results = await searchAddress(input);
        setSuggestions(results.slice(0, 5)); // Limit to 5 results
        setSelectedIndex(-1);
      } catch (error) {
        console.error('Search error:', error);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 300); // Debounce

    return () => clearTimeout(timer);
  }, [input]);

  const handleSelectSuggestion = (suggestion) => {
    const address = suggestion.display_name || suggestion.name;
    setInput(address);
    setSuggestions([]);
    setShowSuggestions(false);
    
    // Update parent with coordinates
    onChange({
      address,
      lat: parseFloat(suggestion.lat),
      lng: parseFloat(suggestion.lon),
    });
  };

  const handleClear = () => {
    setInput('');
    setSuggestions([]);
    setShowSuggestions(false);
  };

  const handleKeyDown = (e) => {
    if (!showSuggestions || suggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          handleSelectSuggestion(suggestions[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        break;
      default:
        break;
    }
  };

  return (
    <div className="relative">
      <div className="relative flex items-center">
        <Search className="absolute left-3 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            setShowSuggestions(true);
          }}
          onFocus={() => input.length >= 3 && setShowSuggestions(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || 'Search address...'}
          className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        {input && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-3 text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute top-full left-0 right-0 bg-white border border-gray-300 rounded-lg shadow-lg mt-1 z-50"
        >
          {loading ? (
            <div className="p-4 text-center text-gray-500">Searching...</div>
          ) : (
            <ul className="max-h-60 overflow-y-auto">
              {suggestions.map((suggestion, index) => (
                <li
                  key={index}
                  onClick={() => handleSelectSuggestion(suggestion)}
                  className={`px-4 py-3 cursor-pointer border-b last:border-b-0 transition ${
                    index === selectedIndex
                      ? 'bg-green-100'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  <div className="font-medium text-gray-800">
                    {suggestion.name || suggestion.display_name?.split(',')[0]}
                  </div>
                  <div className="text-xs text-gray-500">
                    {suggestion.display_name?.split(',').slice(1, 3).join(',')}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}