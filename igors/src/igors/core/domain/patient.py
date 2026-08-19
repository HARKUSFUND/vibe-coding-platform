# -*- coding: utf-8 -*-
"""
patient.py — Entité métier Patient

Représentation pure du domaine, indépendante de l'infrastructure
"""

from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Patient:
    """Entité métier représentant un patient."""
    
    Pa_code: str
    Pa_nom: str
    Pa_prenom: str
    Pa_sexe: str = "M"
    Pa_dnaissance: Optional[datetime] = None
    Pa_contact: str = ""
    Pa_adresse: str = ""
    Pa_groupe_sanguin: str = ""
    Pa_antecedents: str = ""
    
    def __post_init__(self):
        """Validation post-initialisation."""
        if not self.Pa_nom:
            raise ValueError("Le nom du patient est obligatoire")
        if not self.Pa_prenom:
            raise ValueError("Le prénom du patient est obligatoire")
        if self.Pa_sexe not in ["M", "F"]:
            raise ValueError("Le sexe doit être 'M' ou 'F'")
    
    @property
    def age(self) -> int:
        """Calcule l'âge du patient."""
        if not self.Pa_dnaissance:
            return 0
        
        today = datetime.now()
        age = today.year - self.Pa_dnaissance.year
        if (today.month, today.day) < (self.Pa_dnaissance.month, self.Pa_dnaissance.day):
            age -= 1
        return age
    
    @property
    def full_name(self) -> str:
        """Retourne le nom complet du patient."""
        return f"{self.Pa_nom} {self.Pa_prenom}"
    
    def is_major(self) -> bool:
        """Vérifie si le patient est majeur."""
        return self.age >= 18
    
    def to_dict(self) -> dict:
        """Convertit l'entité en dictionnaire."""
        return {
            'Pa_code': self.Pa_code,
            'Pa_nom': self.Pa_nom,
            'Pa_prenom': self.Pa_prenom,
            'Pa_sexe': self.Pa_sexe,
            'Pa_dnaissance': self.Pa_dnaissance.isoformat() if self.Pa_dnaissance else None,
            'Pa_contact': self.Pa_contact,
            'Pa_adresse': self.Pa_adresse,
            'Pa_groupe_sanguin': self.Pa_groupe_sanguin,
            'Pa_antecedents': self.Pa_antecedents,
            'age': self.age,
            'full_name': self.full_name,
            'is_major': self.is_major(),
        }
