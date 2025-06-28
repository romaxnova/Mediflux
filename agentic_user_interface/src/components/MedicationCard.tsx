import React from 'react';

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

interface MedicationCardProps {
  medication: Medication;
}

const MedicationCard: React.FC<MedicationCardProps> = ({ medication }) => {
  const getStatusColor = (status: string) => {
    if (status.includes('Commercialisée')) return 'medication-status-available';
    if (status.includes('Non commercialisée')) return 'medication-status-unavailable';
    if (status.includes('Abrogée')) return 'medication-status-discontinued';
    return 'medication-status-unknown';
  };

  const getReimbursementIcon = (status: string) => {
    if (status.includes('%')) return '💳';
    return '💰';
  };

  const getPrescriptionIcon = (conditions: string[]) => {
    if (conditions.length === 0) return '🟢'; // No prescription needed
    if (conditions.some(c => c.toLowerCase().includes('libre'))) return '🟢';
    if (conditions.some(c => c.toLowerCase().includes('liste'))) return '🔴'; // Prescription needed
    return '🟡'; // Unclear
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr.split('/').reverse().join('-')).toLocaleDateString('fr-FR');
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="medication-card">
      <div className="medication-header">
        <div className="medication-title">
          <h3 className="medication-name">{medication.name}</h3>
          <div className="medication-badges">
            <span className={`medication-status ${getStatusColor(medication.marketing_status)}`}>
              {medication.marketing_status}
            </span>
            {medication.enhanced_surveillance && (
              <span className="medication-surveillance">⚠️ Surveillance renforcée</span>
            )}
          </div>
        </div>
        <div className="medication-meta">
          <div className="medication-cis">CIS: {medication.cis_code}</div>
          <div className="medication-date">AMM: {formatDate(medication.amm_date)}</div>
        </div>
      </div>

      <div className="medication-content">
        <div className="medication-info-grid">
          <div className="medication-info-card">
            <div className="info-header">
              <span className="info-icon">💊</span>
              <h4>Forme & Administration</h4>
            </div>
            <div className="info-content">
              <p><strong>Forme:</strong> {medication.pharmaceutical_form}</p>
              <p><strong>Voie:</strong> {medication.administration_route}</p>
            </div>
          </div>

          {medication.primary_substance && (
            <div className="medication-info-card">
              <div className="info-header">
                <span className="info-icon">🧪</span>
                <h4>Principe Actif</h4>
              </div>
              <div className="info-content">
                <p><strong>Substance:</strong> {medication.primary_substance.names.join(', ')}</p>
                <p><strong>Dosage:</strong> {medication.primary_substance.dosage} {medication.primary_substance.reference}</p>
              </div>
            </div>
          )}

          <div className="medication-info-card">
            <div className="info-header">
              <span className="info-icon">{getPrescriptionIcon(medication.prescription_conditions)}</span>
              <h4>Prescription</h4>
            </div>
            <div className="info-content">
              {medication.prescription_conditions.length > 0 ? (
                <p>{medication.prescription_conditions.join(', ')}</p>
              ) : (
                <p>Vente libre</p>
              )}
            </div>
          </div>

          {medication.main_presentation && (
            <div className="medication-info-card">
              <div className="info-header">
                <span className="info-icon">{getReimbursementIcon(medication.reimbursement_status)}</span>
                <h4>Remboursement & Prix</h4>
              </div>
              <div className="info-content">
                <p><strong>Remboursement:</strong> {medication.reimbursement_status}</p>
                {medication.main_presentation.price_with_fees && (
                  <p><strong>Prix:</strong> {medication.main_presentation.price_with_fees.toFixed(2)}€</p>
                )}
                <p><strong>Conditionnement:</strong> {medication.main_presentation.label}</p>
              </div>
            </div>
          )}
        </div>

        {medication.holders.length > 0 && (
          <div className="medication-holders">
            <h4>🏥 Laboratoire(s)</h4>
            <div className="holders-list">
              {medication.holders.map((holder, index) => (
                <span key={index} className="holder-badge">{holder}</span>
              ))}
            </div>
          </div>
        )}

        {medication.all_substances.length > 1 && (
          <div className="medication-substances">
            <h4>🧬 Toutes les substances</h4>
            <div className="substances-grid">
              {medication.all_substances.map((substance, index) => (
                <div key={index} className="substance-item">
                  <strong>{substance.denominations.join(', ')}</strong>
                  <span>{substance.dosage_substance} {substance.reference_dosage}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="medication-footer">
        <div className="medication-stats">
          <span>📦 {medication.search_metadata.presentation_count} présentation(s)</span>
          <span>🧪 {medication.search_metadata.substance_count} substance(s)</span>
        </div>
      </div>
    </div>
  );
};

export default MedicationCard;
