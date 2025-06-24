import { useEffect, useState } from "react";
import axios from "axios";
import DoctorCard from "./DoctorCard";

interface Identifier {
    system: string;
    value: string;
}
interface Practitioner {
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

export default function DoctorList() {
    const [doctors, setDoctors] = useState<Practitioner[]>([
    { id: '1', name: 'Dr. Mock One', active: true, identifiers: [], qualifications: [], emails: ['mock1@example.com'] }
]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        axios
            .get("http://localhost:8000/api/sante/medecins?specialite=generaliste&cp=75001", {
                headers: { "ESANTE-API-KEY": "b2c9aa48-53c0-4d1b-83f3-7b48a3e26740" },
            })
            .then((res) => {
                console.log("=== FRONTEND: Raw API Response ===");
                console.log("Status:", res.status);
                console.log("Data type:", typeof res.data);
                console.log("Data length:", Array.isArray(res.data) ? res.data.length : "Not an array");
                console.log("Full response data:", JSON.stringify(res.data, null, 2));
                
                if (Array.isArray(res.data) && res.data.length > 0) {
                    console.log("=== FRONTEND: First result analysis ===");
                    console.log("First result:", JSON.stringify(res.data[0], null, 2));
                    console.log("First result keys:", Object.keys(res.data[0]));
                }
                
                // Defensive: ensure array
                setDoctors(Array.isArray(res.data) ? res.data : []);
                setLoading(false);
            })
            .catch((error) => {
                console.error("=== FRONTEND: API Error ===");
                console.error("Error:", error);
                console.error("Error response:", error.response?.data);
                console.error("Error status:", error.response?.status);
                
                // Mock data for testing
                setDoctors([
                    { id: '1', name: 'Dr. Mock One', active: true, identifiers: [], qualifications: [], emails: ['mock1@example.com'] }
                ]);
                setLoading(false);
            });
    }, []);

    return (
        <div>
            <h2>Liste des médecins généralistes (75001)</h2>
            {loading && <p>Chargement...</p>}
            {error && <p style={{ color: "red" }}>{error}</p>}
            {doctors.map((doc) => (
                <DoctorCard key={doc.id} doctor={doc} />
            ))}
        </div>
    );
}
