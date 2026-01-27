import React from 'react';
import ApartmentCard from './ApartmentCard';
import './ApartmentList.css';

function ApartmentList({ apartments }) {
  return (
    <div className="apartment-list">
      <div className="list-header">
        <h2>Found {apartments.length} Apartment{apartments.length !== 1 ? 's' : ''}</h2>
      </div>

      <div className="apartment-grid">
        {apartments.map((apartment, index) => (
          <ApartmentCard key={index} apartment={apartment} />
        ))}
      </div>
    </div>
  );
}

export default ApartmentList;
