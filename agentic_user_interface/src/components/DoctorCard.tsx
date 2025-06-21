import React from 'react';

export interface Identifier {
    system: string;
    value: string;
}

export interface Practitioner {
    id: string;
    name: string;
    active: boolean;
    identifiers: Identifier[];
    qualifications: any[];
    emails: string[];
    adresse?: string;
    specialite?: string;
    estimatedTravelTime?: string;
}

const DoctorCard: React.FC<{ doctor: Practitioner }> = ({ doctor }) => {
    return (
        <div style={{ border: "1px solid #ccc", borderRadius: 8, padding: 16, marginBottom: 16 }} data-testid="doctor-card">
            <h2>{doctor.name}</h2>
            {doctor.specialite && <p>Spécialité: {doctor.specialite}</p>}
            {doctor.adresse && <p>Adresse: {doctor.adresse}</p>}
            <p>RPPS: {doctor.identifiers.find((id: Identifier) => id.system === 'http://rpps.fr')?.value || 'N/A'}</p>
            <p>{doctor.active ? "Actif" : "Inactif"}</p>
            {doctor.emails.length > 0 && (
                <p>Email: {doctor.emails.join(", ")}</p>
            )}
            {doctor.estimatedTravelTime && (
                <p>Temps de trajet estimé: {doctor.estimatedTravelTime}</p>
            )}
        </div>
    );
};

export default DoctorCard;
