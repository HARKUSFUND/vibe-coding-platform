"""
Tests unitaires pour le service de prescriptions.
Conforme CDC §4.1, §4.3
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, Mock

from igors.core.services.prescription_service import PrescriptionService
from igors.infrastructure.repositories.prescription_repo import PrescripteurRepository, PrescriptionRepository


class TestPrescriptionService:
    """Tests unitaires pour PrescriptionService."""
    
    @pytest.fixture
    def mock_session(self):
        """Session de base de données mockée."""
        return MagicMock()
    
    @pytest.fixture
    def prescription_service(self, mock_session):
        """Instance du service avec dependencies mockées."""
        return PrescriptionService(mock_session)
    
    def test_list_prescripteurs(self, prescription_service, mock_session):
        """Tester la liste des prescripteurs."""
        # Mock des données
        mock_prescripteurs = [
            MagicMock(id=1, code="PRES_001", nom="Dupont", prenom="Jean", 
                     structure="CHU Cocody", specialite="Médecine générale", actif=True),
            MagicMock(id=2, code="PRES_002", nom="Koné", prenom="Aminata",
                     structure="Clinique Pasteur", specialite="Pédiatrie", actif=True)
        ]
        
        prescription_service.prescripteur_repo.get_all = MagicMock(return_value=mock_prescripteurs)
        
        result = prescription_service.list_prescripteurs()
        
        assert len(result) == 2
        assert result[0]['nom'] == "Dupont"
        assert result[1]['nom'] == "Koné"
        assert all(p['actif'] for p in result)
    
    def test_search_prescripteurs(self, prescription_service, mock_session):
        """Tester la recherche de prescripteurs."""
        mock_results = [
            MagicMock(id=1, code="PRES_001", nom="Dupont", prenom="Jean",
                     structure="CHU Cocody", specialite="Médecine générale",
                     telephone="0707070707", email="dupont@chu.ci")
        ]
        
        prescription_service.prescripteur_repo.search = MagicMock(return_value=mock_results)
        
        result = prescription_service.search_prescripteurs("Dupont")
        
        assert len(result) == 1
        assert result[0]['nom'] == "Dupont"
        assert 'telephone' in result[0]
    
    def test_create_prescription(self, prescription_service, mock_session):
        """Tester la création d'une prescription."""
        # Mock prescription créée
        mock_prescription = MagicMock(
            id=1,
            numero="PRESC-20260527120000",
            examens=[]
        )
        
        prescription_service.prescription_repo.create = MagicMock(return_value=mock_prescription)
        
        data = {
            "patient_id": 1,
            "prescripteur_id": 1,
            "urgence": False,
            "contexte_clinique": "Bilan pré-opératoire"
        }
        
        examens = [
            {"examen_id": 1, "priorite": "NORMALE"},
            {"examen_id": 2, "priorite": "NORMALE"}
        ]
        
        result = prescription_service.create_prescription(data, examens, "test_user")
        
        assert result['id'] == 1
        assert result['numero'].startswith("PRESC-")
        assert "succès" in result['message'].lower()
    
    def test_get_prescriptions_en_attente(self, prescription_service, mock_session):
        """Tester la récupération des prescriptions en attente."""
        mock_prescriptions = [
            MagicMock(
                id=1,
                numero="PRESC-001",
                patient_id=1,
                patient=MagicMock(nom="Kouassi", prenom="Pierre"),
                prescripteur=MagicMock(nom="Dr. Martin"),
                date_prescription=datetime.now(),
                urgence=False,
                contexte_clinique="Test",
                traitement_en_cours=None,
                source="MANUEL",
                reference_externe=None,
                statut="ACTIVE",
                date_realisation=None,
                examens=[]
            )
        ]
        
        prescription_service.prescription_repo.get_en_attente = MagicMock(
            return_value=mock_prescriptions
        )
        
        result = prescription_service.get_prescriptions_en_attente()
        
        assert len(result) == 1
        assert result[0]['statut'] == "ACTIVE"
        assert result[0]['patient_nom'] == "Kouassi"
    
    def test_update_statut_prescription_valide(self, prescription_service, mock_session):
        """Tester la mise à jour du statut d'une prescription."""
        mock_prescription = MagicMock(id=1, statut="REALISEE")
        
        prescription_service.prescription_repo.update_statut = MagicMock(
            return_value=mock_prescription
        )
        
        result = prescription_service.update_statut_prescription(1, "REALISEE")
        
        assert result is not None
        assert result['statut'] == "REALISEE"
    
    def test_update_statut_prescription_invalide(self, prescription_service, mock_session):
        """Tester la mise à jour avec un statut invalide."""
        with pytest.raises(ValueError) as excinfo:
            prescription_service.update_statut_prescription(1, "STATUT_INVALIDE")
        
        assert "Statut invalide" in str(excinfo.value)
    
    def test_prescription_to_dict(self, prescription_service, mock_session):
        """Tester la conversion prescription -> dict."""
        mock_prescription = MagicMock(
            id=1,
            numero="PRESC-001",
            patient_id=1,
            patient=MagicMock(nom="Traore", prenom="Fatou"),
            prescripteur_id=1,
            prescripteur=MagicMock(nom="Dr. Kouamé"),
            date_prescription=datetime(2026, 5, 27, 10, 0, 0),
            urgence=True,
            contexte_clinique="Urgence vitale",
            traitement_en_cours="Antibiotiques",
            source="IMPORT_SI",
            reference_externe="EXT-12345",
            statut="ACTIVE",
            date_realisation=None,
            examens=[
                MagicMock(
                    id=1,
                    examen_id=1,
                    examen=MagicMock(nom="NFS"),
                    priorite="URGENTE",
                    instructions="Rapide",
                    statut="A_FAIRE",
                    date_prelevement=None,
                    date_resultat=None
                )
            ]
        )
        
        result = prescription_service._prescription_to_dict(mock_prescription)
        
        assert result['id'] == 1
        assert result['numero'] == "PRESC-001"
        assert result['patient_nom'] == "Traore"
        assert result['urgence'] == True
        assert len(result['examens']) == 1
        assert result['examens'][0]['examen_nom'] == "NFS"


class TestPrescripteurService:
    """Tests pour PrescripteurService."""
    
    @pytest.fixture
    def mock_session(self):
        return MagicMock()
    
    @pytest.fixture
    def prescripteur_service(self, mock_session):
        from igors.core.services.prescription_service import PrescripteurService
        return PrescripteurService(mock_session)
    
    def test_get_all_delegates(self, prescripteur_service):
        """Tester que get_all délègue au PrescriptionService."""
        mock_result = [{"id": 1, "nom": "Test"}]
        prescripteur_service.prescription_service.list_prescripteurs = MagicMock(
            return_value=mock_result
        )
        
        result = prescripteur_service.get_all()
        
        assert result == mock_result
        prescripteur_service.prescription_service.list_prescripteurs.assert_called_once()
