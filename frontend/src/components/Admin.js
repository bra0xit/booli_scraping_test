import React, { useState, useEffect } from 'react';
import './Admin.css';

function Admin() {
  const [mappings, setMappings] = useState({ agents: {}, agencies: {} });
  const [discovered, setDiscovered] = useState({ agents: {}, agencies: {} });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [editingAgent, setEditingAgent] = useState({});
  const [editingAgency, setEditingAgency] = useState({});

  // Load mappings on component mount
  useEffect(() => {
    loadMappings();
  }, []);

  const loadMappings = async () => {
    try {
      const response = await fetch('/api/mappings');
      const data = await response.json();

      if (data.success) {
        setMappings(data.mappings);
        setDiscovered(data.discovered);
      }
    } catch (error) {
      console.error('Error loading mappings:', error);
    }
  };

  const discoverIds = async () => {
    setLoading(true);
    setMessage('Discovering agent and agency IDs...');

    try {
      const response = await fetch('/api/discover-ids', {
        method: 'POST'
      });
      const data = await response.json();

      if (data.success) {
        setDiscovered(data.discovered);
        setMessage(`✓ Found ${data.count.agents} agents and ${data.count.agencies} agencies`);
      } else {
        setMessage(`Error: ${data.error}`);
      }
    } catch (error) {
      setMessage(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const saveMapping = async (type, id, name) => {
    if (!name || !name.trim()) return;

    try {
      const updateData = {
        [type]: {
          [id]: name.trim()
        }
      };

      const response = await fetch('/api/mappings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      const data = await response.json();

      if (data.success) {
        // Update local state
        setMappings(prev => ({
          ...prev,
          [type]: {
            ...prev[type],
            [id]: name.trim()
          }
        }));

        // Clear editing state
        if (type === 'agents') {
          setEditingAgent(prev => ({ ...prev, [id]: undefined }));
        } else {
          setEditingAgency(prev => ({ ...prev, [id]: undefined }));
        }

        setMessage(`✓ Saved ${type === 'agents' ? 'agent' : 'agency'}: ${name}`);
      } else {
        setMessage(`Error: ${data.error}`);
      }
    } catch (error) {
      setMessage(`Error: ${error.message}`);
    }
  };

  const allAgentIds = new Set([
    ...Object.keys(mappings.agents),
    ...Object.keys(discovered.agents)
  ]);

  const allAgencyIds = new Set([
    ...Object.keys(mappings.agencies),
    ...Object.keys(discovered.agencies)
  ]);

  return (
    <div className="admin-container">
      <h1>Agent & Agency Mapping Admin</h1>

      <div className="admin-actions">
        <button
          onClick={discoverIds}
          disabled={loading}
          className="discover-button"
        >
          {loading ? 'Discovering...' : '🔍 Discover IDs from Booli'}
        </button>

        {message && (
          <div className={`message ${message.startsWith('✓') ? 'success' : 'info'}`}>
            {message}
          </div>
        )}
      </div>

      <div className="mappings-grid">
        <div className="mapping-section">
          <h2>Agents ({allAgentIds.size})</h2>

          <table className="mapping-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Profile</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {Array.from(allAgentIds).map(agentId => {
                const currentName = mappings.agents[agentId] || '';
                const isEditing = editingAgent[agentId] !== undefined;
                const editValue = isEditing ? editingAgent[agentId] : currentName;
                const discoveredInfo = discovered.agents[agentId];
                const profileUrl = discoveredInfo?.url || `https://www.hittamaklare.se/maklare/${agentId}`;

                return (
                  <tr key={agentId} className={currentName ? 'mapped' : 'unmapped'}>
                    <td className="id-cell">{agentId}</td>
                    <td className="name-cell">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditingAgent(prev => ({
                            ...prev,
                            [agentId]: e.target.value
                          }))}
                          placeholder="Enter agent name"
                          className="name-input"
                        />
                      ) : (
                        <span className={!currentName ? 'unmapped-text' : ''}>
                          {currentName || 'Not mapped'}
                        </span>
                      )}
                    </td>
                    <td className="profile-cell">
                      <a
                        href={profileUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="profile-link"
                      >
                        View
                      </a>
                    </td>
                    <td className="actions-cell">
                      {isEditing ? (
                        <>
                          <button
                            onClick={() => saveMapping('agents', agentId, editValue)}
                            className="save-button"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingAgent(prev => ({
                              ...prev,
                              [agentId]: undefined
                            }))}
                            className="cancel-button"
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => setEditingAgent(prev => ({
                            ...prev,
                            [agentId]: currentName
                          }))}
                          className="edit-button"
                        >
                          {currentName ? 'Edit' : 'Add'}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {allAgentIds.size === 0 && (
            <p className="empty-message">
              No agents discovered yet. Click "Discover IDs from Booli" to scan for agents.
            </p>
          )}
        </div>

        <div className="mapping-section">
          <h2>Agencies ({allAgencyIds.size})</h2>

          <table className="mapping-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Profile</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {Array.from(allAgencyIds).map(agencyId => {
                const currentName = mappings.agencies[agencyId] || '';
                const isEditing = editingAgency[agencyId] !== undefined;
                const editValue = isEditing ? editingAgency[agencyId] : currentName;
                const discoveredInfo = discovered.agencies[agencyId];
                const profileUrl = discoveredInfo?.url || `https://www.hittamaklare.se/maklarbyra/${agencyId}`;

                return (
                  <tr key={agencyId} className={currentName ? 'mapped' : 'unmapped'}>
                    <td className="id-cell">{agencyId}</td>
                    <td className="name-cell">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditingAgency(prev => ({
                            ...prev,
                            [agencyId]: e.target.value
                          }))}
                          placeholder="Enter agency name"
                          className="name-input"
                        />
                      ) : (
                        <span className={!currentName ? 'unmapped-text' : ''}>
                          {currentName || 'Not mapped'}
                        </span>
                      )}
                    </td>
                    <td className="profile-cell">
                      <a
                        href={profileUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="profile-link"
                      >
                        View
                      </a>
                    </td>
                    <td className="actions-cell">
                      {isEditing ? (
                        <>
                          <button
                            onClick={() => saveMapping('agencies', agencyId, editValue)}
                            className="save-button"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingAgency(prev => ({
                              ...prev,
                              [agencyId]: undefined
                            }))}
                            className="cancel-button"
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => setEditingAgency(prev => ({
                            ...prev,
                            [agencyId]: currentName
                          }))}
                          className="edit-button"
                        >
                          {currentName ? 'Edit' : 'Add'}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {allAgencyIds.size === 0 && (
            <p className="empty-message">
              No agencies discovered yet. Click "Discover IDs from Booli" to scan for agencies.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Admin;
