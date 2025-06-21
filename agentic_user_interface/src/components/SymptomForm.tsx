import React, { useState } from 'react';

const SymptomForm = () => {
    const [symptoms, setSymptoms] = useState('');
    const [urgency, setUrgency] = useState('Low');

    const handleSubmit = async (e) => {
        e.preventDefault();
        const response = await fetch('/api/diagnose', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symptoms, urgency })
        });
        // Handle response
    };

    return (
        <form onSubmit={handleSubmit}>
            <textarea value={symptoms} onChange={(e) => setSymptoms(e.target.value)} placeholder="Enter symptoms" />
            <select value={urgency} onChange={(e) => setUrgency(e.target.value)}>
                <option value="Low">Low</option>
                <option value="Medium">Medium</option>
                <option value="High">High</option>
            </select>
            <button type="submit">Diagnose</button>
        </form>
    );
};

export default SymptomForm;
