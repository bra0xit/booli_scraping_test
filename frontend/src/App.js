import React, { useState } from 'react';
import './App.css';
import ApartmentList from './components/ApartmentList';
import SearchForm from './components/SearchForm';
import Admin from './components/Admin';
import ForSale from './components/ForSale';

function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [apartments, setApartments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [testMode, setTestMode] = useState(null);

  const handleSearch = async (searchParams) => {
    setLoading(true);
    setError(null);

    try {
      const queryParams = new URLSearchParams({
        areaId: searchParams.areaId || '115349',
        objectType: searchParams.objectType || 'Lägenhet',
        minPrice: searchParams.minPrice || '8000000',
        maxPrice: searchParams.maxPrice || '10000000',
      });

      // Add optional parameters
      if (searchParams.minRooms) queryParams.append('minRooms', searchParams.minRooms);
      if (searchParams.maxRooms) queryParams.append('maxRooms', searchParams.maxRooms);
      if (searchParams.minArea) queryParams.append('minArea', searchParams.minArea);
      if (searchParams.maxArea) queryParams.append('maxArea', searchParams.maxArea);
      if (searchParams.maxResults) queryParams.append('maxResults', searchParams.maxResults);

      const response = await fetch(`/api/apartments?${queryParams}`);
      const data = await response.json();

      if (data.success) {
        setApartments(data.apartments);
        setTestMode(data.test_mode);
      } else {
        setError(data.error || 'Failed to fetch apartments');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Booli Apartment Finder</h1>
        <p>Find sold apartments and their original realtor listings</p>
      </header>

      <nav className="App-nav">
        <button
          className={`nav-tab ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          Sold Apartments
        </button>
        <button
          className={`nav-tab ${activeTab === 'forsale' ? 'active' : ''}`}
          onClick={() => setActiveTab('forsale')}
        >
          For Sale
        </button>
        <button
          className={`nav-tab ${activeTab === 'admin' ? 'active' : ''}`}
          onClick={() => setActiveTab('admin')}
        >
          Agent/Agency Admin
        </button>
      </nav>

      <main className="App-main">
        {activeTab === 'search' ? (
          <>
            <SearchForm onSearch={handleSearch} loading={loading} />

            {testMode && (
              <div className="info-message">
                <strong>Test Mode:</strong> Showing mock data. To enable real scraping,
                see the <code>SETUP_GUIDE.md</code> file.
              </div>
            )}

            {error && (
              <div className="error-message">
                <strong>Error:</strong> {error}
              </div>
            )}

            {loading && (
              <div className="loading-message">
                <div className="spinner"></div>
                <p>Scraping Booli.se and searching for realtor listings...</p>
                <p className="loading-note">This may take a minute or two</p>
              </div>
            )}

            {!loading && apartments.length > 0 && (
              <ApartmentList apartments={apartments} />
            )}

            {!loading && apartments.length === 0 && !error && (
              <div className="empty-state">
                <p>Enter search parameters above and click "Search" to find apartments</p>
              </div>
            )}
          </>
        ) : activeTab === 'forsale' ? (
          <ForSale />
        ) : (
          <Admin />
        )}
      </main>
    </div>
  );
}

export default App;
