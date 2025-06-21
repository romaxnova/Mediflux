import React, { useState } from 'react';
import './App.css';

interface Practitioner {
  name: string;
  title: string;
  specialty: string;
  specialty_label: string;
  practice_type: string;
  fonction_label: string;
  genre_activite_label: string;
  organization_ref: string | null;
  smart_card: any;
  active: boolean;
  id: string;
}

interface ApiResponse {
  choices: Array<{
    message: {
      content: string;
    };
    data: {
      natural_response?: string;
      structured_data?: {
        success: boolean;
        data: {
          results: Practitioner[];
          query_params: any;
        };
      };
      success: boolean;
    };
  }>;
}

function App() {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [practitioners, setPractitioners] = useState<Practitioner[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setResponse('');
    setPractitioners([]);
    
    try {
      const res = await fetch('http://localhost:9000/mcp/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: prompt }),
      });
      const data: ApiResponse = await res.json();
      console.log('Backend response:', data); // Debug log
      
      if (data.choices && data.choices[0]) {
        const choice = data.choices[0];
        const content = choice.message.content;
        const responseData = choice.data;
        
        // Set the natural language response
        if (responseData?.natural_response) {
          setResponse(responseData.natural_response);
        } else if (content) {
          setResponse(content);
        }
        
        // Extract structured practitioner data if available
        if (responseData?.structured_data?.success && responseData.structured_data.data?.results) {
          setPractitioners(responseData.structured_data.data.results);
        }
      } else if (data.error) {
        setResponse('Error: ' + data.error);
      } else {
        setResponse('No response received');
      }
    } catch (error) {
      setResponse('Error: Could not fetch response.');
      console.error('Fetch error:', error);
    }
    setIsLoading(false);
  };

  return (
    <div className="app-container">
      <h1>Mediflux Chat Interface</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter your query, e.g., 'find a sage-femme in paris 17th arrondissement'"
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
      
      {response && (
        <div className="response-container">
          <h2>Response:</h2>
          <div className="response-text">{response}</div>
        </div>
      )}
      
      {practitioners.length > 0 && (
        <div className="practitioners-container">
          <h2>Healthcare Professionals Found:</h2>
          <div className="practitioners-grid">
            {practitioners.map((practitioner, index) => (
              <div key={practitioner.id || index} className="practitioner-card">
                <div className="practitioner-header">
                  <h3 className="practitioner-name">{practitioner.name}</h3>
                  {practitioner.title && (
                    <span className="practitioner-title">({practitioner.title})</span>
                  )}
                </div>
                
                <div className="practitioner-details">
                  <div className="detail-row">
                    <span className="detail-label">Specialty:</span>
                    <span className="detail-value">{practitioner.specialty_label || practitioner.specialty}</span>
                  </div>
                  
                  <div className="detail-row">
                    <span className="detail-label">Practice Type:</span>
                    <span className="detail-value">{practitioner.practice_type || 'Not specified'}</span>
                  </div>
                  
                  <div className="detail-row">
                    <span className="detail-label">Professional Function:</span>
                    <span className="detail-value">{practitioner.fonction_label || 'Not specified'}</span>
                  </div>
                  
                  <div className="detail-row">
                    <span className="detail-label">Activity Type:</span>
                    <span className="detail-value">{practitioner.genre_activite_label || 'Not specified'}</span>
                  </div>
                  
                  {practitioner.organization_ref && (
                    <div className="detail-row">
                      <span className="detail-label">Organization:</span>
                      <span className="detail-value">Affiliated with healthcare organization</span>
                    </div>
                  )}
                  
                  <div className="detail-row">
                    <span className="detail-label">Status:</span>
                    <span className={`detail-value status ${practitioner.active ? 'active' : 'inactive'}`}>
                      {practitioner.active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
