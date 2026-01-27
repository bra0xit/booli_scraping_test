import React, { useState, useEffect } from 'react';
import './ForSale.css';

function ForSale() {
  const [locationIds, setLocationIds] = useState('925970');
  const [propertyType, setPropertyType] = useState('lägenhet');
  const [minPrice, setMinPrice] = useState('7000000');
  const [maxPrice, setMaxPrice] = useState('10000000');
  const [minRooms, setMinRooms] = useState('');
  const [maxRooms, setMaxRooms] = useState('');
  const [minSize, setMinSize] = useState('');
  const [maxSize, setMaxSize] = useState('');
  const [maxResults, setMaxResults] = useState('10');
  const [downloadImages, setDownloadImages] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  const [listings, setListings] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedListing, setSelectedListing] = useState(null);
  const [modalListing, setModalListing] = useState(null);
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'
  const [sortField, setSortField] = useState('first_seen');
  const [sortDirection, setSortDirection] = useState('desc');

  // Load existing listings on mount
  useEffect(() => {
    loadListings();
    loadStats();
  }, []);

  const loadListings = async () => {
    try {
      const response = await fetch('/api/hemnet/listings');
      const data = await response.json();

      if (data.success) {
        setListings(data.listings);
      }
    } catch (err) {
      console.error('Error loading listings:', err);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch('/api/hemnet/stats');
      const data = await response.json();

      if (data.success) {
        setStats(data.stats);
      }
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  const handleScrape = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const response = await fetch('/api/hemnet/scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          locationIds: locationIds.split(',').map(id => id.trim()),
          propertyType,
          minPrice: minPrice ? parseInt(minPrice) : null,
          maxPrice: maxPrice ? parseInt(maxPrice) : null,
          minRooms: minRooms ? parseInt(minRooms) : null,
          maxRooms: maxRooms ? parseInt(maxRooms) : null,
          minSize: minSize ? parseInt(minSize) : null,
          maxSize: maxSize ? parseInt(maxSize) : null,
          maxResults: maxResults === 'all' ? 'all' : parseInt(maxResults),
          downloadImages
        })
      });

      const data = await response.json();

      if (data.success) {
        setMessage(`Successfully scraped ${data.count} listings!`);
        // Reload listings and stats
        await loadListings();
        await loadStats();
      } else {
        setError(data.error || 'Failed to scrape Hemnet');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price) => {
    if (!price) return 'N/A';
    return new Intl.NumberFormat('sv-SE').format(price) + ' kr';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('sv-SE');
  };

  const calculatePricePerSqm = (price, size) => {
    if (!price || !size) return null;
    return Math.round(price / size);
  };

  const openModal = (listing) => {
    setModalListing(listing);
    setCarouselIndex(0);
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
  };

  const closeModal = () => {
    setModalListing(null);
    setCarouselIndex(0);
    document.body.style.overflow = 'auto';
  };

  const nextImage = () => {
    if (modalListing && modalListing.images) {
      setCarouselIndex((prev) => (prev + 1) % modalListing.images.length);
    }
  };

  const prevImage = () => {
    if (modalListing && modalListing.images) {
      setCarouselIndex((prev) =>
        prev === 0 ? modalListing.images.length - 1 : prev - 1
      );
    }
  };

  // Sorting function
  const handleSort = (field) => {
    if (sortField === field) {
      // Toggle direction if same field
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // New field, default to ascending
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Get sorted listings
  const getSortedListings = () => {
    const sorted = [...listings].sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      // Handle null/undefined values
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      // Special handling for price per sqm
      if (sortField === 'price_per_sqm') {
        aVal = calculatePricePerSqm(a.asking_price, a.size_sqm) || 0;
        bVal = calculatePricePerSqm(b.asking_price, b.size_sqm) || 0;
      }

      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }

      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    return sorted;
  };

  const sortedListings = getSortedListings();

  return (
    <div className="for-sale">
      <div className="for-sale-header">
        <h2>Hemnet - For Sale Listings</h2>
        <p>Scrape and save active listings from Hemnet.se</p>
      </div>

      {stats && (
        <div className="stats-bar">
          <div className="stat-item">
            <strong>{stats.total_listings || 0}</strong>
            <span>Total Listings</span>
          </div>
          <div className="stat-item">
            <strong>{stats.by_status?.active || 0}</strong>
            <span>Active</span>
          </div>
          <div className="stat-item">
            <strong>{stats.total_images || 0}</strong>
            <span>Images Saved</span>
          </div>
          <div className="stat-item">
            <strong>{stats.total_size_mb || 0} MB</strong>
            <span>Storage Used</span>
          </div>
        </div>
      )}

      <form className="scrape-form" onSubmit={handleScrape}>
        <h3>Scrape New Listings</h3>

        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="locationIds">Location IDs:</label>
            <input
              type="text"
              id="locationIds"
              value={locationIds}
              onChange={(e) => setLocationIds(e.target.value)}
              placeholder="925970"
            />
            <small>Vasastan, Stockholm = 925970 (comma-separated for multiple)</small>
          </div>

          <div className="form-group">
            <label htmlFor="propertyType">Property Type:</label>
            <select
              id="propertyType"
              value={propertyType}
              onChange={(e) => setPropertyType(e.target.value)}
            >
              <option value="lägenhet">Apartment (Lägenhet)</option>
              <option value="villa">House (Villa)</option>
              <option value="radhus">Townhouse (Radhus)</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="minPrice">Min Price (SEK):</label>
            <input
              type="number"
              id="minPrice"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
              placeholder="Any"
            />
          </div>

          <div className="form-group">
            <label htmlFor="maxPrice">Max Price (SEK):</label>
            <input
              type="number"
              id="maxPrice"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              placeholder="Any"
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
            />
          </div>

          <div className="form-group">
            <label htmlFor="minSize">Min Size (m²):</label>
            <input
              type="number"
              id="minSize"
              value={minSize}
              onChange={(e) => setMinSize(e.target.value)}
              placeholder="Any"
            />
          </div>

          <div className="form-group">
            <label htmlFor="maxSize">Max Size (m²):</label>
            <input
              type="number"
              id="maxSize"
              value={maxSize}
              onChange={(e) => setMaxSize(e.target.value)}
              placeholder="Any"
            />
          </div>

          <div className="form-group">
            <label htmlFor="maxResults">Max Results:</label>
            <select
              id="maxResults"
              value={maxResults}
              onChange={(e) => setMaxResults(e.target.value)}
            >
              <option value="5">5 listings</option>
              <option value="10">10 listings</option>
              <option value="20">20 listings</option>
              <option value="50">50 listings</option>
              <option value="all">All available</option>
            </select>
          </div>
        </div>

        <div className="form-group checkbox-group">
          <label>
            <input
              type="checkbox"
              checked={downloadImages}
              onChange={(e) => setDownloadImages(e.target.checked)}
            />
            Download and save images locally
          </label>
        </div>

        <button type="submit" className="scrape-button" disabled={loading}>
          {loading ? 'Scraping Hemnet...' : 'Scrape Hemnet'}
        </button>
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {message && (
        <div className="success-message">
          <strong>Success:</strong> {message}
        </div>
      )}

      {loading && (
        <div className="loading-message">
          <div className="spinner"></div>
          <p>Scraping Hemnet and downloading images...</p>
          <p className="loading-note">This may take a few minutes</p>
        </div>
      )}

      <div className="listings-section">
        <div className="listings-header">
          <h3>Saved Listings ({listings.length})</h3>
          <div className="view-toggle">
            <button
              className={`view-btn ${viewMode === 'cards' ? 'active' : ''}`}
              onClick={() => setViewMode('cards')}
            >
              Card View
            </button>
            <button
              className={`view-btn ${viewMode === 'table' ? 'active' : ''}`}
              onClick={() => setViewMode('table')}
            >
              Table View
            </button>
          </div>
        </div>

        {listings.length === 0 && !loading && (
          <div className="empty-state">
            <p>No listings saved yet. Scrape Hemnet to get started!</p>
          </div>
        )}

        {viewMode === 'table' && listings.length > 0 && (
          <div className="table-container">
            <table className="listings-table">
              <thead>
                <tr>
                  <th onClick={() => handleSort('address')}>
                    Address {sortField === 'address' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th onClick={() => handleSort('asking_price')}>
                    Asking Price {sortField === 'asking_price' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th onClick={() => handleSort('price_per_sqm')}>
                    Price/m² {sortField === 'price_per_sqm' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th onClick={() => handleSort('rooms')}>
                    Rooms {sortField === 'rooms' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th onClick={() => handleSort('size_sqm')}>
                    Size (m²) {sortField === 'size_sqm' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th onClick={() => handleSort('monthly_fee')}>
                    Monthly Fee {sortField === 'monthly_fee' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th onClick={() => handleSort('floor')}>
                    Floor {sortField === 'floor' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th onClick={() => handleSort('agent_name')}>
                    Agent {sortField === 'agent_name' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th onClick={() => handleSort('agency_name')}>
                    Agency {sortField === 'agency_name' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                  <th onClick={() => handleSort('first_seen')}>
                    First Scraped {sortField === 'first_seen' && (sortDirection === 'asc' ? '▲' : '▼')}
                  </th>
                </tr>
              </thead>
              <tbody>
                {sortedListings.map((listing) => {
                  const pricePerSqm = calculatePricePerSqm(listing.asking_price, listing.size_sqm);
                  return (
                    <tr key={listing.id} onClick={() => openModal(listing)} className="table-row">
                      <td>{listing.address || 'N/A'}</td>
                      <td className="price-cell">{formatPrice(listing.asking_price)}</td>
                      <td className="price-cell">{formatPrice(pricePerSqm)}</td>
                      <td>{listing.rooms || 'N/A'}</td>
                      <td>{listing.size_sqm ? `${listing.size_sqm} m²` : 'N/A'}</td>
                      <td className="price-cell">{formatPrice(listing.monthly_fee)}</td>
                      <td>{listing.floor || 'N/A'}</td>
                      <td>{listing.agent_name || 'N/A'}</td>
                      <td>{listing.agency_name || 'N/A'}</td>
                      <td>{formatDate(listing.first_seen)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {viewMode === 'cards' && (
          <div className="listings-grid">
            {listings.map((listing) => {
            const pricePerSqm = calculatePricePerSqm(listing.asking_price, listing.size_sqm);

            return (
              <div key={listing.id} className="listing-card" onClick={() => openModal(listing)}>
                <div className="listing-images">
                {listing.images && listing.images.length > 0 ? (
                  <img
                    src={listing.images[0].downloaded && listing.images[0].local_path
                      ? `/api/hemnet/images/${listing.hemnet_id}/image_000.jpg`
                      : listing.images[0].url}
                    alt={listing.address}
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23ddd" width="400" height="300"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle"%3ENo Image%3C/text%3E%3C/svg%3E';
                    }}
                  />
                ) : (
                  <div className="no-image">No images</div>
                )}
                {listing.images && listing.images.length > 1 && (
                  <span className="image-count">{listing.images.length} photos</span>
                )}
              </div>

              <div className="listing-content">
                <h4>{listing.address || 'No address'}</h4>

                <div className="listing-price-highlight">
                  <span className="price-label">Asking Price:</span>
                  <span className="price-amount">{formatPrice(listing.asking_price)}</span>
                </div>

                <div className="listing-details">
                  {pricePerSqm && (
                    <div className="detail-item highlight-item">
                      <strong>Price/m² (Kvadratmeterpris):</strong> {formatPrice(pricePerSqm)}
                    </div>
                  )}
                  {listing.monthly_fee && (
                    <div className="detail-item">
                      <strong>Monthly fee:</strong> {formatPrice(listing.monthly_fee)}
                    </div>
                  )}
                  {listing.rooms && (
                    <div className="detail-item">
                      <strong>Rooms:</strong> {listing.rooms}
                    </div>
                  )}
                  {listing.size_sqm && (
                    <div className="detail-item">
                      <strong>Size:</strong> {listing.size_sqm} m²
                    </div>
                  )}
                  {listing.floor && (
                    <div className="detail-item">
                      <strong>Floor:</strong> {listing.floor}
                    </div>
                  )}
                  {listing.agent_name && (
                    <div className="detail-item">
                      <strong>Agent:</strong> {listing.agent_name}
                    </div>
                  )}
                  {listing.agency_name && (
                    <div className="detail-item">
                      <strong>Agency:</strong> {listing.agency_name}
                    </div>
                  )}
                  <div className="detail-item">
                    <strong>First seen:</strong> {formatDate(listing.first_seen)}
                  </div>
                  <div className="detail-item">
                    <strong>Last updated:</strong> {formatDate(listing.last_scraped)}
                  </div>
                </div>

                <div className="click-hint">
                  Click to view full details
                </div>
              </div>
            </div>
            );
          })}
          </div>
        )}
      </div>

      {/* Modal Popup */}
      {modalListing && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={closeModal}>×</button>

            <div className="modal-body">
              {/* Image Carousel */}
              <div className="modal-carousel">
                {modalListing.images && modalListing.images.length > 0 ? (
                  <>
                    <button className="carousel-button prev" onClick={prevImage}>‹</button>
                    <div className="carousel-image-container">
                      <img
                        src={modalListing.images[carouselIndex].downloaded && modalListing.images[carouselIndex].local_path
                          ? `/api/hemnet/images/${modalListing.hemnet_id}/image_${String(carouselIndex).padStart(3, '0')}.jpg`
                          : modalListing.images[carouselIndex].url}
                        alt={`${modalListing.address} - ${carouselIndex + 1}`}
                        className="carousel-image"
                        onError={(e) => {
                          e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="800" height="600"%3E%3Crect fill="%23ddd" width="800" height="600"/%3E%3Ctext fill="%23999" x="50%25" y="50%25" text-anchor="middle"%3ENo Image%3C/text%3E%3C/svg%3E';
                        }}
                      />
                      <div className="carousel-counter">
                        {carouselIndex + 1} / {modalListing.images.length}
                      </div>
                    </div>
                    <button className="carousel-button next" onClick={nextImage}>›</button>
                  </>
                ) : (
                  <div className="no-images-placeholder">No images available</div>
                )}
              </div>

              {/* Listing Details */}
              <div className="modal-details">
                <h2>{modalListing.address || 'No address'}</h2>

                <div className="modal-price-banner">
                  {formatPrice(modalListing.asking_price)}
                </div>

                <div className="modal-key-info">
                  <div className="key-info-item">
                    <span className="key-info-label">Rooms</span>
                    <span className="key-info-value">{modalListing.rooms || 'N/A'} rum</span>
                  </div>
                  <div className="key-info-item">
                    <span className="key-info-label">Living Area</span>
                    <span className="key-info-value">{modalListing.size_sqm || 'N/A'} m²</span>
                  </div>
                  <div className="key-info-item">
                    <span className="key-info-label">Monthly Fee</span>
                    <span className="key-info-value">{formatPrice(modalListing.monthly_fee)}</span>
                  </div>
                  <div className="key-info-item">
                    <span className="key-info-label">Price/m²</span>
                    <span className="key-info-value">
                      {calculatePricePerSqm(modalListing.asking_price, modalListing.size_sqm)
                        ? formatPrice(calculatePricePerSqm(modalListing.asking_price, modalListing.size_sqm))
                        : 'N/A'}
                    </span>
                  </div>
                </div>

                <div className="modal-details-grid">
                  <div className="modal-detail-section full-width">
                    <h3>Property Information</h3>
                    <div className="detail-row">
                      <span className="detail-label">Property Type</span>
                      <span className="detail-value">Lägenhet</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Tenure Type</span>
                      <span className="detail-value">Bostadsrätt</span>
                    </div>
                    {modalListing.rooms && (
                      <div className="detail-row">
                        <span className="detail-label">Rooms</span>
                        <span className="detail-value">{modalListing.rooms} rum</span>
                      </div>
                    )}
                    {modalListing.size_sqm && (
                      <div className="detail-row">
                        <span className="detail-label">Living Area (Boarea)</span>
                        <span className="detail-value">{modalListing.size_sqm} m²</span>
                      </div>
                    )}
                    {modalListing.floor && (
                      <div className="detail-row">
                        <span className="detail-label">Floor</span>
                        <span className="detail-value">{modalListing.floor}</span>
                      </div>
                    )}
                  </div>

                  <div className="modal-detail-section full-width">
                    <h3>Economics</h3>
                    <div className="detail-row">
                      <span className="detail-label">Asking Price</span>
                      <span className="detail-value">{formatPrice(modalListing.asking_price)}</span>
                    </div>
                    {calculatePricePerSqm(modalListing.asking_price, modalListing.size_sqm) && (
                      <div className="detail-row">
                        <span className="detail-label">Price per m²</span>
                        <span className="detail-value">{formatPrice(calculatePricePerSqm(modalListing.asking_price, modalListing.size_sqm))}</span>
                      </div>
                    )}
                    {modalListing.monthly_fee && (
                      <div className="detail-row">
                        <span className="detail-label">Monthly Fee (Avgift)</span>
                        <span className="detail-value">{formatPrice(modalListing.monthly_fee)}/mån</span>
                      </div>
                    )}
                  </div>

                  <div className="modal-detail-section full-width">
                    <h3>Contact</h3>
                    {modalListing.agent_name && (
                      <div className="detail-row">
                        <span className="detail-label">Listing Agent</span>
                        <span className="detail-value">{modalListing.agent_name}</span>
                      </div>
                    )}
                    {modalListing.agency_name && (
                      <div className="detail-row">
                        <span className="detail-label">Real Estate Agency</span>
                        <span className="detail-value">{modalListing.agency_name}</span>
                      </div>
                    )}
                  </div>

                  <div className="modal-detail-section full-width">
                    <h3>Listing Details</h3>
                    <div className="detail-row">
                      <span className="detail-label">Hemnet ID</span>
                      <span className="detail-value">{modalListing.hemnet_id}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">First Scraped</span>
                      <span className="detail-value">{formatDate(modalListing.first_seen)}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Last Updated</span>
                      <span className="detail-value">{formatDate(modalListing.last_scraped)}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Status</span>
                      <span className="detail-value status-badge">{modalListing.status}</span>
                    </div>
                    {modalListing.images && modalListing.images.length > 0 && (
                      <div className="detail-row">
                        <span className="detail-label">Total Images</span>
                        <span className="detail-value">{modalListing.images.length} photos</span>
                      </div>
                    )}
                  </div>

                  {modalListing.description && (
                    <div className="modal-detail-section full-width">
                      <h3>Description</h3>
                      <p className="description-text">{modalListing.description}</p>
                    </div>
                  )}
                </div>

                <div className="modal-actions">
                  <a
                    href={modalListing.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="modal-button primary"
                    onClick={(e) => e.stopPropagation()}
                  >
                    View on Hemnet
                  </a>
                  <button className="modal-button secondary" onClick={closeModal}>
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ForSale;
