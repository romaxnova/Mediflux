import React, { useState } from 'react';
import './App.css';

function App() {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setResponse('');
    try {
      const res = await fetch('http://localhost:9000/mcp/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: prompt }),
      });
      const data = await res.json();
      console.log('Backend response:', data); // Debug log
      
      // Prioritize natural language response
      if (data.choices && data.choices[0] && data.choices[0].message) {
        const content = data.choices[0].message.content;
        const responseData = data.choices[0].data;
        
        // Check if we have a natural language response
        if (responseData && responseData.natural_response) {
          setResponse(responseData.natural_response);
        } else if (content) {
          setResponse(content);
        } else {
          // Fallback to formatted JSON
          setResponse(JSON.stringify(responseData || data, null, 2));
        }
      } else if (data.natural_response) {
        // Direct natural response from orchestrator
        setResponse(data.natural_response);
      } else if (data.message && typeof data.message === 'string') {
        // Simple message response
        setResponse(data.message);
      } else if (data.error) {
        setResponse('Error: ' + data.error);
      } else {
        setResponse(typeof data === "object" ? JSON.stringify(data, null, 2) : data);
      }
    } catch (error) {
      setResponse('Error: Could not fetch response.');
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
          placeholder="Enter your query, e.g., 'find a hospital'"
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
      <div className="response-container">
        <h2>Response:</h2>
        <div className="response-text">{response}</div>
      </div>
    </div>
  );
}

export default App;
