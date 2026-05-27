"""Donneur repository - Data access for donors table using SQLAlchemy."""

from typing import List, Optional
from loguru import logger

from ...infrastructure.database.base import SessionLocal
from ...infrastructure.models.donneur import DonneurModel


class DonneurRepository:
    """Repository for donor data access using SQLAlchemy with PostgreSQL."""

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def get_by_id(self, donor_id: int) -> Optional[DonneurModel]:
        """Get donor by ID."""
        return self.session.query(DonneurModel).filter(
            DonneurModel.id == donor_id,
            DonneurModel.actif == True
        ).first()

    def get_by_nir(self, nir: str) -> Optional[DonneurModel]:
        """Get donor by NIR (encrypted identifier)."""
        return self.session.query(DonneurModel).filter(
            DonneurModel.nir == nir,
            DonneurModel.actif == True
        ).first()

    def get_all(self, actif_only: bool = True) -> List[DonneurModel]:
        """Get all donors."""
        query = self.session.query(DonneurModel)
        if actif_only:
            query = query.filter(DonneurModel.actif == True)
        return query.order_by(DonneurModel.nom).all()

    def create(self, donor_data: dict) -> DonneurModel:
        """Create a new donor."""
        if donor_data.get("nir"):
            existing = self.get_by_nir(donor_data["nir"])
            if existing:
                raise ValueError(f"Donor with NIR {donor_data['nir']} already exists")

        donor = DonneurModel(**donor_data)
        self.session.add(donor)
        self.session.commit()
        self.session.refresh(donor)
        
        logger.info(f"Donor created: {donor.nom} {donor.prenom} (ID: {donor.id})")
        return donor

    def update(self, donor_id: int, updates: dict) -> Optional[DonneurModel]:
        """Update donor fields."""
        donor = self.get_by_id(donor_id)
        if not donor:
            return None

        allowed_fields = [
            "nom", "prenom", "sexe", "date_naissance", "lieu_naissance",
            "nationalite", "profession", "telephone", "email", "adresse",
            "ville", "quartier", "groupe_sanguin", "facteur_rhesus",
            "eligible_don", "contre_indications", "consentement_signe",
            "date_consentement", "fichier_consentement"
        ]
        
        for key, value in updates.items():
            if key in allowed_fields:
                setattr(donor, key, value)

        self.session.commit()
        self.session.refresh(donor)
        logger.info(f"Donor updated: ID {donor_id}")
        return donor

    def delete(self, donor_id: int) -> bool:
        """Soft delete a donor."""
        donor = self.get_by_id(donor_id)
        if not donor:
            return False
        donor.actif = False
        self.session.commit()
        logger.info(f"Donor soft deleted: ID {donor_id}")
        return True

    def search(self, query: str, groupe_sanguin: Optional[str] = None) -> List[DonneurModel]:
        """Search donors by name or NIR."""
        from sqlalchemy import or_
        query_lower = f"%{query.lower()}%"
        
        filters = [
            DonneurModel.actif == True,
            or_(
                DonneurModel.nom.ilike(query_lower),
                DonneurModel.prenom.ilike(query_lower),
            )
        ]
        if groupe_sanguin:
            filters.append(DonneurModel.groupe_sanguin == groupe_sanguin)

        return self.session.query(DonneurModel).filter(*filters).order_by(DonneurModel.nom).all()

    def get_eligible_donors(self) -> List[DonneurModel]:
        """Get all eligible donors who can donate."""
        return self.session.query(DonneurModel).filter(
            DonneurModel.actif == True,
            DonneurModel.eligible_don == True,
            DonneurModel.consentement_signe == True
        ).order_by(DonneurModel.nom).all()

    def count(self) -> int:
        """Get total number of active donors."""
        return self.session.query(DonneurModel).filter(DonneurModel.actif == True).count()

    def close(self):
        """Close the session."""
        self.session.close()
