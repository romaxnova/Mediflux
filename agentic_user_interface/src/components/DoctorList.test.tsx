import { render, screen, waitFor } from '@testing-library/react';
import DoctorList from './DoctorList';
import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('DoctorList', () => {
    it('renders doctors from API', async () => {
        mockedAxios.get.mockResolvedValueOnce({
            data: [
                {
                    id: '1',
                    name: 'Dr. John Doe',
                    active: true,
                    identifiers: [{ system: 'http://rpps.fr', value: '12345678901' }],
                    qualifications: [],
                    emails: ['john.doe@example.com'],
                    adresse: '123 Rue de Paris, 75001 Paris',
                    specialite: 'Généraliste',
                    estimatedTravelTime: '15 min',
                },
            ],
        });
        render(<DoctorList />);
        expect(screen.getByText('Chargement...')).toBeInTheDocument();
        await waitFor(() => expect(screen.getByText('Dr. John Doe')).toBeInTheDocument());
        expect(screen.getByText(/Généraliste/)).toBeInTheDocument();
        expect(screen.getByText(/123 Rue de Paris/)).toBeInTheDocument();
        expect(screen.getByText(/12345678901/)).toBeInTheDocument();
        expect(screen.getByText(/Actif/)).toBeInTheDocument();
        expect(screen.getByText(/john.doe@example.com/)).toBeInTheDocument();
        expect(screen.getByText(/15 min/)).toBeInTheDocument();
    });

    it('shows error on API failure', async () => {
        mockedAxios.get.mockRejectedValueOnce(new Error('API error'));
        render(<DoctorList />);
        await waitFor(() => expect(screen.getByText(/Erreur/)).toBeInTheDocument());
    });
});
