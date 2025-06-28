import React, { useState } from 'react';
import MedicationCard from './MedicationCard';

interface Medication {
  id: string;
  name: string;
  cis_code: string;
  pharmaceutical_form: string;
  administration_route: string;
  marketing_status: string;
  amm_status: string;
  amm_date: string;
  enhanced_surveillance: boolean;
  prescription_conditions: string[];
  holders: string[];
  primary_substance?: {
    code: string;
    names: string[];
    dosage: string;
    reference: string;
  };
  all_substances: Array<{
    code_substance: string;
    denominations: string[];
    dosage_substance: string;
    reference_dosage: string;
    nature_composant: string;
  }>;
  main_presentation?: {
    cip7: string;
    cip13: string;
    label: string;
    reimbursement_rate: number | null;
    price_without_fees: number | null;
    price_with_fees: number | null;
    collective_agreement: boolean | null;
  };
  all_presentations: any[];
  reimbursement_status: string;
  resource_type: string;
  search_metadata: {
    matched_substance: any;
    presentation_count: number;
    substance_count: number;
  };
}

interface MedicationListProps {
  medications: Medication[];
}

const MedicationList: React.FC<MedicationListProps> = ({ medications }) => {
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'reimbursement'>('name');
  const [filterBy, setFilterBy] = useState<'all' | 'available' | 'prescription' | 'otc'>('all');

  const getFilteredAndSortedMedications = () => {
    let filtered = medications;

    // Apply filters
    switch (filterBy) {
      case 'available':
        filtered = medications.filter(med => med.marketing_status.includes('Commercialisée'));
        break;
      case 'prescription':
        filtered = medications.filter(med => med.prescription_conditions.length > 0);
        break;
      case 'otc':
        filtered = medications.filter(med => med.prescription_conditions.length === 0);
        break;
      default:
        filtered = medications;
    }

    // Apply sorting
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'price':
          const priceA = a.main_presentation?.price_with_fees || 0;
          const priceB = b.main_presentation?.price_with_fees || 0;
          return priceA - priceB;
        case 'reimbursement':
          const reimbA = a.main_presentation?.reimbursement_rate || 0;
          const reimbB = b.main_presentation?.reimbursement_rate || 0;
          return reimbB - reimbA; // Higher reimbursement first
        default:
          return 0;
      }
    });
  };

  const sortedMedications = getFilteredAndSortedMedications();

  const getQuickStats = () => {
    const available = medications.filter(med => med.marketing_status.includes('Commercialisée')).length;
    const prescription = medications.filter(med => med.prescription_conditions.length > 0).length;
    const otc = medications.filter(med => med.prescription_conditions.length === 0).length;
    const reimbursed = medications.filter(med => med.reimbursement_status.includes('%')).length;

    return { available, prescription, otc, reimbursed };
  };

  const stats = getQuickStats();

  if (medications.length === 0) {
    return null;
  }

  return (
    <div className="medication-list">
      <div className="medication-list-header">
        <div className="results-summary">
          <h2>🏥 Médicaments trouvés</h2>
          <div className="quick-stats">
            <div className="stat-item">
              <span className="stat-number">{medications.length}</span>
              <span className="stat-label">Total</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">{stats.available}</span>
              <span className="stat-label">Disponibles</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">{stats.otc}</span>
              <span className="stat-label">Sans ordonnance</span>
            </div>
            <div className="stat-item">
              <span className="stat-number">{stats.reimbursed}</span>
              <span className="stat-label">Remboursés</span>
            </div>
          </div>
        </div>

        <div className="medication-controls">
          <div className="control-group">
            <label>Trier par:</label>
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value as any)}
              className="control-select"
            >
              <option value="name">Nom</option>
              <option value="price">Prix</option>
              <option value="reimbursement">Remboursement</option>
            </select>
          </div>

          <div className="control-group">
            <label>Filtrer:</label>
            <select 
              value={filterBy} 
              onChange={(e) => setFilterBy(e.target.value as any)}
              className="control-select"
            >
              <option value="all">Tous</option>
              <option value="available">Disponibles</option>
              <option value="prescription">Sur ordonnance</option>
              <option value="otc">Vente libre</option>
            </select>
          </div>
        </div>
      </div>

      <div className="medication-grid">
        {sortedMedications.map((medication) => (
          <MedicationCard key={medication.id} medication={medication} />
        ))}
      </div>

      {sortedMedications.length !== medications.length && (
        <div className="filter-info">
          Affichage de {sortedMedications.length} sur {medications.length} médicaments
        </div>
      )}
    </div>
  );
};

export default MedicationList;
