import React, { useState } from 'react';
import './SearchForm.css';

function SearchForm({ onSearch, loading }) {
  const [areaId, setAreaId] = useState('115349');
  const [objectType, setObjectType] = useState('Lägenhet');
  const [minPrice, setMinPrice] = useState('8000000');
  const [maxPrice, setMaxPrice] = useState('10000000');
  const [minRooms, setMinRooms] = useState('');
  const [maxRooms, setMaxRooms] = useState('');
  const [minArea, setMinArea] = useState('');
  const [maxArea, setMaxArea] = useState('');
  const [maxResults, setMaxResults] = useState('10');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch({
      areaId,
      objectType,
      minPrice,
      maxPrice,
      minRooms,
      maxRooms,
      minArea,
      maxArea,
      maxResults
    });
  };

  return (
    <form className="search-form" onSubmit={handleSubmit}>
      <div className="form-grid">
        <div className="form-group">
          <label htmlFor="areaId">Area ID:</label>
          <input
            type="text"
            id="areaId"
            value={areaId}
            onChange={(e) => setAreaId(e.target.value)}
            placeholder="115349"
          />
          <small>Vasastan = 115349</small>
        </div>

        <div className="form-group">
          <label htmlFor="objectType">Property Type:</label>
          <select
            id="objectType"
            value={objectType}
            onChange={(e) => setObjectType(e.target.value)}
          >
            <option value="Lägenhet">Apartment (Lägenhet)</option>
            <option value="Villa">House (Villa)</option>
            <option value="Radhus">Townhouse (Radhus)</option>
            <option value="Fritidshus">Vacation Home (Fritidshus)</option>
            <option value="Tomt">Plot (Tomt)</option>
            <option value="Gård">Farm (Gård)</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="minPrice">Min Price (SEK):</label>
          <input
            type="text"
            id="minPrice"
            value={minPrice}
            onChange={(e) => setMinPrice(e.target.value)}
            placeholder="8000000"
          />
        </div>

        <div className="form-group">
          <label htmlFor="maxPrice">Max Price (SEK):</label>
          <input
            type="text"
            id="maxPrice"
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value)}
            placeholder="10000000"
          />
        </div>

        <div className="form-group">
          <label htmlFor="minRooms">Min Rooms:</label>
          <input
            type="number"
            id="minRooms"
            value={minRooms}
            onChange={(e) => setMinRooms(e.target.value)}
            placeholder="Any"
            min="1"
          />
        </div>

        <div className="form-group">
          <label htmlFor="maxRooms">Max Rooms:</label>
          <input
            type="number"
            id="maxRooms"
            value={maxRooms}
            onChange={(e) => setMaxRooms(e.target.value)}
            placeholder="Any"
            min="1"
          />
        </div>

        <div className="form-group">
          <label htmlFor="minArea">Min Area (m²):</label>
          <input
            type="number"
            id="minArea"
            value={minArea}
            onChange={(e) => setMinArea(e.target.value)}
            placeholder="Any"
            min="1"
          />
        </div>

        <div className="form-group">
          <label htmlFor="maxArea">Max Area (m²):</label>
          <input
            type="number"
            id="maxArea"
            value={maxArea}
            onChange={(e) => setMaxArea(e.target.value)}
            placeholder="Any"
            min="1"
          />
        </div>

        <div className="form-group">
          <label htmlFor="maxResults">Max Results:</label>
          <select
            id="maxResults"
            value={maxResults}
            onChange={(e) => setMaxResults(e.target.value)}
          >
            <option value="5">5 apartments</option>
            <option value="10">10 apartments</option>
            <option value="20">20 apartments</option>
            <option value="50">50 apartments</option>
            <option value="100">100 apartments</option>
            <option value="all">All available</option>
          </select>
        </div>
      </div>

      <button type="submit" className="search-button" disabled={loading}>
        {loading ? 'Searching...' : 'Search Apartments'}
      </button>
    </form>
  );
}

export default SearchForm;
