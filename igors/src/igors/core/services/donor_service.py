"""Donor management service."""

from datetime import date, datetime
from typing import List, Optional
from loguru import logger

from ...config.settings import Settings, get_settings
from ...core.domain.donneur import Donneur, Sexe, GroupeSanguin
from ...infrastructure.repositories.donneur_repo import DonneurRepository


class DonorService:
    """Service for managing blood donors."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.donneur_repo = DonneurRepository()

    def create_donor(
        self,
        nom: str,
        prenom: str,
        sexe: str,
        date_naissance: date,
        telephone: str,
        adresse: str,
        ville: str,
        email: Optional[str] = None,
        profession: Optional[str] = None,
    ) -> Donneur:
        """Create a new donor."""
        donneur = Donneur(
            nom=nom.upper(),
            prenom=prenom.capitalize(),
            sexe=Sexe(sexe),
            date_naissance=date_naissance,
            telephone=telephone,
            adresse=adresse,
            ville=ville.upper(),
            email=email,
            profession=profession or "",
            date_creation=datetime.now(),
        )

        # Validate age
        if not donneur.est_majeur:
            raise ValueError("Le donneur doit être majeur (18 ans minimum)")

        saved = self.donneur_repo.save(donneur)
        logger.info(f"Donor created: {saved.nom} {saved.prenom} (ID: {saved.id})")
        return saved

    def get_donor_by_id(self, donor_id: int) -> Optional[Donneur]:
        """Get donor by ID."""
        return self.donneur_repo.get_by_id(donor_id)

    def get_donor_by_nir(self, nir: str) -> Optional[Donneur]:
        """Get donor by NIR (encrypted ID)."""
        return self.donneur_repo.get_by_nir(nir)

    def search_donors(
        self,
        query: str = "",
        groupe_sanguin: Optional[str] = None,
        eligible_only: bool = False,
    ) -> List[Donneur]:
        """Search donors with filters."""
        return self.donneur_repo.search(query, groupe_sanguin, eligible_only)

    def update_donor(self, donor_id: int, updates: dict) -> Optional[Donneur]:
        """Update donor information."""
        donneur = self.donneur_repo.get_by_id(donor_id)
        if not donneur:
            return None

        # Update fields
        for key, value in updates.items():
            if hasattr(donneur, key):
                setattr(donneur, key, value)

        donneur.date_modification = datetime.now()
        saved = self.donneur_repo.save(donneur)
        logger.info(f"Donor updated: ID {donor_id}")
        return saved

    def record_consent(
        self, donor_id: int, fichier_scan: str, signe_par: int
    ) -> Optional[Donneur]:
        """Record donor consent with scanned document."""
        donneur = self.donneur_repo.get_by_id(donor_id)
        if not donneur:
            return None

        donneur.consentement_signe = True
        donneur.date_consentement = datetime.now()
        donneur.fichier_consentement = fichier_scan
        donneur.date_modification = datetime.now()

        saved = self.donneur_repo.save(donneur)
        logger.info(f"Consent recorded for donor ID {donor_id}")
        return saved

    def check_eligibility(self, donor_id: int) -> dict:
        """Check if donor is eligible for donation."""
        donneur = self.donneur_repo.get_by_id(donor_id)
        if not donneur:
            return {"eligible": False, "reason": "Donneur non trouvé"}

        if not donneur.eligible_don:
            return {"eligible": False, "reason": "Donneur non éligible (contre-indication)"}

        if not donneur.est_majeur:
            return {"eligible": False, "reason": "Donneur mineur"}

        if donneur.date_dernier_don:
            jours_depuis = (date.today() - donneur.date_dernier_don).days
            if jours_depuis < 56:
                return {
                    "eligible": False,
                    "reason": f"Délai insuffisant ({jours_depuis} jours, minimum 56)",
                }

        return {"eligible": True, "reason": "Éligible"}

    def get_all_donors(self, actif_only: bool = True) -> List[Donneur]:
        """Get all donors."""
        return self.donneur_repo.get_all(actif_only)

    def delete_donor(self, donor_id: int) -> bool:
        """Soft delete a donor."""
        return self.donneur_repo.delete(donor_id)

    def get_statistics(self) -> dict:
        """Get donor statistics."""
        all_donors = self.donneur_repo.get_all(False)
        return {
            "total": len(all_donors),
            "actifs": sum(1 for d in all_donors if d.actif),
            "eligibles": sum(1 for d in all_donors if d.eligible_don),
            "par_groupe": self._count_by_blood_group(all_donors),
            "nombre_dons_total": sum(d.nombre_dons for d in all_donors),
        }

    def _count_by_blood_group(self, donors: List[Donneur]) -> dict:
        """Count donors by blood group."""
        counts = {}
        for donor in donors:
            if donor.groupe_sanguin:
                group = donor.groupe_sanguin.value
                counts[group] = counts.get(group, 0) + 1
        return counts
