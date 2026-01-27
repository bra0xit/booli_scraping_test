import React from 'react';
import './ApartmentCard.css';

function ApartmentCard({ apartment }) {
  return (
    <div className="apartment-card">
      <div className="card-header">
        <h3>{apartment.address || 'Address not available'}</h3>
      </div>

      <div className="card-body">
        {apartment.sold_price && (
          <div className="detail-row">
            <span className="label">Sold Price:</span>
            <span className="value">{apartment.sold_price}</span>
          </div>
        )}

        {apartment.sold_date && (
          <div className="detail-row">
            <span className="label">Sold Date:</span>
            <span className="value">{apartment.sold_date}</span>
          </div>
        )}

        {apartment.agent && (
          <div className="detail-row">
            <span className="label">Agent:</span>
            {apartment.agent_url ? (
              <a
                href={apartment.agent_url}
                target="_blank"
                rel="noopener noreferrer"
                className="value-link"
              >
                {apartment.agent}
              </a>
            ) : (
              <span className="value">{apartment.agent}</span>
            )}
          </div>
        )}

        {apartment.agency && (
          <div className="detail-row">
            <span className="label">Agency:</span>
            {apartment.agency_url ? (
              <a
                href={apartment.agency_url}
                target="_blank"
                rel="noopener noreferrer"
                className="value-link"
              >
                {apartment.agency}
              </a>
            ) : (
              <span className="value">{apartment.agency}</span>
            )}
          </div>
        )}
      </div>

      <div className="card-footer">
        <a
          href={apartment.url}
          target="_blank"
          rel="noopener noreferrer"
          className="link-button booli-link"
        >
          View on Booli
        </a>

        {apartment.realtor_link ? (
          <a
            href={apartment.realtor_link}
            target="_blank"
            rel="noopener noreferrer"
            className="link-button realtor-link"
          >
            View Realtor Listing
          </a>
        ) : (
          <span className="link-button disabled">
            Realtor Listing Not Found
          </span>
        )}
      </div>
    </div>
  );
}

export default ApartmentCard;
