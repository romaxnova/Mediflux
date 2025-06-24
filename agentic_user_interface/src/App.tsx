import React, { useState } from 'react';
import './App.css';

interface Practitioner {
  id: string;
  name: string;
  specialty: string;
  specialty_label?: string;
  profession_code: string;
  active: boolean;
  resource_type: string;
  address?: {
    organization_name?: string;
    organization_address?: {
      text?: string;
      city?: string;
      postalCode?: string;
      line?: string;
      full_address?: string;
    };
    full_location?: string;
  };
  organization_name?: string;
  organization_type?: string;
  practitioner_ref: string;
  organization_ref: string;
  rpps_id?: string;
  contact?: {
    phone?: string;
    email?: string;
    fax?: string;
  };
  search_metadata?: {
    query_city?: string;
    profession_mapped?: string;
  };
}

interface Organization {
  id: string;
  name: string;
  type: string | null;
  active: boolean;
  address: {
    text: string;
    city: string;
    postalCode: string;
    line: string;
  };
  lastUpdated: string;
}

interface ApiResponse {
  choices: Array<{
    message: {
      content: string;
    };
    data: {
      natural_response?: string;        structured_data?: {
          success: boolean;
          data: {
            results: (Practitioner | Organization)[];
            query_params?: any;
            query_type?: string;
          };
        };
      success: boolean;
    };
  }>;
  error?: string;
}

function App() {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [practitioners, setPractitioners] = useState<Practitioner[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [queryType, setQueryType] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setResponse('');
    setPractitioners([]);
    setOrganizations([]);
    setQueryType('');
    
    try {
      console.log('=== FRONTEND REQUEST ===');
      console.log('Sending query:', prompt);
      console.log('=======================');
      
      const res = await fetch('http://localhost:9000/mcp/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: prompt }),
      });
      const data: ApiResponse = await res.json();
      
      console.log('=== FRONTEND RESPONSE ===');
      console.log('Status:', res.status);
      console.log('Backend response:', data);
      console.log('Full data structure:', JSON.stringify(data, null, 2));
      console.log('========================');
      
      // Add detailed logging for debugging practitioner search issues
      if (data.choices && data.choices[0] && data.choices[0].data && data.choices[0].data.structured_data) {
        const results = data.choices[0].data.structured_data.data?.results || [];
        console.log('=== FRONTEND DEBUG ===');
        console.log('Number of results:', results.length);
        console.log('Query type:', data.choices[0].data.structured_data.data?.query_type);
        console.log('Success:', data.choices[0].data.structured_data.success);
        console.log('Message:', data.choices[0].data.structured_data.message);
        
        if (results.length > 0) {
          console.log('SAMPLE RESULT ANALYSIS:');
          const sample = results[0];
          console.log('Sample result keys:', Object.keys(sample));
          console.log('Sample name:', sample.name);
          console.log('Sample specialty:', sample.specialty);
          console.log('Sample active:', sample.active);
          console.log('Sample resource_type:', sample.resource_type);
          console.log('Sample address:', sample.address);
          
          console.log('ALL RESULTS OVERVIEW:');
          results.forEach((result, index) => {
            console.log(`Result ${index + 1}: ${result.name || 'NO_NAME'} - ${result.specialty || 'NO_SPECIALTY'} - Active: ${result.active} - Type: ${result.resource_type || 'NO_TYPE'}`);
          });
        } else {
          console.log('NO RESULTS RETURNED');
        }
        console.log('=== END DEBUG ===');
      }
      
      if (data.choices && data.choices[0]) {
        const choice = data.choices[0];
        const content = choice.message.content;
        const responseData = choice.data;
        
        console.log('Choice data:', choice);
        console.log('Response data:', responseData);
        
        // Set the natural language response
        if (responseData?.natural_response) {
          setResponse(responseData.natural_response);
        } else if (content) {
          setResponse(content);
        }
        
        // Extract structured data if available
        if (responseData?.structured_data?.success && responseData.structured_data.data?.results) {
          const results = responseData.structured_data.data.results;
          const detectedQueryType = responseData.structured_data.data.query_type || 
                           (responseData.structured_data.data as any).search_metadata?.query_type;
          
          setQueryType(detectedQueryType || '');
          console.log('Query type detected:', detectedQueryType, 'State:', queryType); // Debug log
          
          // Check if results are organizations or practitioners based on resource_type
          const practitionerResults = results.filter(result => result.resource_type === 'practitioner');
          const organizationResults = results.filter(result => result.resource_type === 'organization');
          
          if (practitionerResults.length > 0) {
            setPractitioners(practitionerResults as Practitioner[]);
          }
          if (organizationResults.length > 0) {
            setOrganizations(organizationResults as Organization[]);
          }
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
          placeholder="Enter your query, e.g., 'find a sage-femme in paris 17th arrondissement' or 'find hospitals in 75017'"
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
                  {practitioner.profession_code && (
                    <span className="practitioner-code">ID: {practitioner.profession_code}</span>
                  )}
                </div>
                
                <div className="practitioner-details">
                  <div className="detail-row">
                    <span className="detail-label">Spécialité:</span>
                    <span className="detail-value specialty">{practitioner.specialty}</span>
                  </div>
                  
                  {practitioner.address?.organization_name && (
                    <div className="detail-row">
                      <span className="detail-label">Organisation:</span>
                      <span className="detail-value">{practitioner.address.organization_name}</span>
                    </div>
                  )}
                  
                  {practitioner.address?.organization_address?.city && (
                    <div className="detail-row">
                      <span className="detail-label">Localisation:</span>
                      <span className="detail-value">
                        {practitioner.address.organization_address.city} {practitioner.address.organization_address.postalCode}
                      </span>
                    </div>
                  )}
                  
                  {practitioner.address?.full_location && practitioner.address.full_location !== 'Localisation non disponible' && (
                    <div className="detail-row">
                      <span className="detail-label">Adresse complète:</span>
                      <span className="detail-value">{practitioner.address.full_location}</span>
                    </div>
                  )}
                  
                  {practitioner.rpps_id && (
                    <div className="detail-row">
                      <span className="detail-label">RPPS:</span>
                      <span className="detail-value">{practitioner.rpps_id}</span>
                    </div>
                  )}
                  
                  <div className="detail-row">
                    <span className="detail-label">Statut:</span>
                    <span className={`detail-value status ${practitioner.active ? 'active' : 'inactive'}`}>
                      {practitioner.active ? 'Actif' : 'Inactif'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {organizations.length > 0 && (
        <div className="organizations-container">
          <h2>Healthcare Organizations Found:</h2>
          <div className="organizations-grid">
            {organizations.map((organization, index) => (
              <div key={organization.id || index} className="organization-card">
                <div className="organization-header">
                  <h3 className="organization-name">{organization.name}</h3>
                  {organization.type && (
                    <span className="organization-type">({organization.type})</span>
                  )}
                </div>
                
                <div className="organization-details">
                  <div className="detail-row">
                    <span className="detail-label">Address:</span>
                    <span className="detail-value">
                      {organization.address.line && `${organization.address.line}, `}
                      {organization.address.city && `${organization.address.city} `}
                      {organization.address.postalCode}
                    </span>
                  </div>
                  
                  {organization.address.text && (
                    <div className="detail-row">
                      <span className="detail-label">Full Address:</span>
                      <span className="detail-value">{organization.address.text}</span>
                    </div>
                  )}
                  
                  <div className="detail-row">
                    <span className="detail-label">Status:</span>
                    <span className={`detail-value status ${organization.active ? 'active' : 'inactive'}`}>
                      {organization.active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  
                  {organization.lastUpdated && (
                    <div className="detail-row">
                      <span className="detail-label">Last Updated:</span>
                      <span className="detail-value">
                        {new Date(organization.lastUpdated).toLocaleDateString()}
                      </span>
                    </div>
                  )}
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
