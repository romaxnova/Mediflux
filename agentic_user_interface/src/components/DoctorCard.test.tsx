import { render, screen } from '@testing-library/react';
import DoctorCard, { Practitioner } from './DoctorCard';

const mockDoctor: Practitioner = {
    id: '1',
    name: 'Dr. John Doe',
    active: true,
    identifiers: [
        { system: 'http://rpps.fr', value: '12345678901' },
        { system: 'other', value: '999' }
    ],
    qualifications: [],
    emails: ['john.doe@example.com'],
    adresse: '123 Rue de Paris, 75001 Paris',
    specialite: 'Généraliste',
    estimatedTravelTime: '15 min'
};

describe('DoctorCard', () => {
    it('renders doctor information correctly', () => {
        render(<DoctorCard doctor={mockDoctor} />);
        expect(screen.getByText('Dr. John Doe')).toBeInTheDocument();
        expect(screen.getByText(/Spécialité/)).toHaveTextContent('Généraliste');
        expect(screen.getByText(/Adresse/)).toHaveTextContent('123 Rue de Paris');
        expect(screen.getByText(/RPPS/)).toHaveTextContent('12345678901');
        expect(screen.getByText('Actif')).toBeInTheDocument();
        expect(screen.getByText(/Email/)).toHaveTextContent('john.doe@example.com');
        expect(screen.getByText(/Temps de trajet estimé/)).toHaveTextContent('15 min');
    });
});
