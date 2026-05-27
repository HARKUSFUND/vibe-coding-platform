"""RBAC (Role-Based Access Control) - Matrice des permissions."""

from enum import Enum
from typing import Dict, List, Set
from dataclasses import dataclass, field


class Permission(str, Enum):
    """All system permissions."""

    # Donors
    DONOR_CREATE = "donor:create"
    DONOR_READ = "donor:read"
    DONOR_UPDATE = "donor:update"
    DONOR_DELETE = "donor:delete"
    DONOR_CONSENT = "donor:consent"

    # Dons / Collectes
    DON_CREATE = "don:create"
    DON_READ = "don:read"
    DON_UPDATE = "don:update"
    DON_VALIDATE = "don:validate"
    DON_DELETE = "don:delete"

    # Patients
    PATIENT_CREATE = "patient:create"
    PATIENT_READ = "patient:read"
    PATIENT_UPDATE = "patient:update"
    PATIENT_DELETE = "patient:delete"

    # Prescriptions
    PRESCRIPTION_CREATE = "prescription:create"
    PRESCRIPTION_READ = "prescription:read"
    PRESCRIPTION_UPDATE = "prescription:update"

    # Results
    RESULTAT_CREATE = "resultat:create"
    RESULTAT_READ = "resultat:read"
    RESULTAT_UPDATE = "resultat:update"
    RESULTAT_VALIDATE_INTERNE = "resultat:validate_interne"
    RESULTAT_VALIDATE_BIOLOGISTE = "resultat:validate_biologiste"
    RESULTAT_DELETE = "resultat:delete"

    # PSL / Stock
    PSL_CREATE = "psl:create"
    PSL_READ = "psl:read"
    PSL_UPDATE = "psl:update"
    PSL_QUALIFY = "psl:qualify"
    PSL_DISTRIBUTE = "psl:distribute"

    # Quality
    QUALITE_CQI = "qualite:cqi"
    QUALITE_EEQ = "qualite:eeq"
    QUALITE_CAPA = "qualite:capa"

    # Automates
    AUTOMATE_CONFIG = "automate:config"
    AUTOMATE_READ = "automate:read"

    # Administration
    ADMIN_USERS = "admin:users"
    ADMIN_ROLES = "admin:roles"
    ADMIN_CONFIG = "admin:config"
    ADMIN_AUDIT = "admin:audit"

    # Reports
    REPORT_GENERATE = "report:generate"
    REPORT_EXPORT = "report:export"


class Role(str, Enum):
    """System roles as per CDC requirements."""

    ADMINISTRATEUR = "administrateur"
    BIOLOGISTE = "biologiste"
    TECHNICIEN = "technicien"
    SAISISSEUR = "saisisseur"
    PRESCRIPTEUR = "prescripteur"
    DONNEUR = "donneur"


@dataclass
class RoleDefinition:
    """Role definition with permissions."""

    name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)


# Role-Permission Matrix
ROLE_PERMISSIONS: Dict[Role, RoleDefinition] = {
    Role.ADMINISTRATEUR: RoleDefinition(
        name="Administrateur",
        description="Administration complète du système",
        permissions={
            Permission.ADMIN_USERS,
            Permission.ADMIN_ROLES,
            Permission.ADMIN_CONFIG,
            Permission.ADMIN_AUDIT,
            Permission.DONOR_CREATE,
            Permission.DONOR_READ,
            Permission.DONOR_UPDATE,
            Permission.DONOR_DELETE,
            Permission.DON_CREATE,
            Permission.DON_READ,
            Permission.DON_UPDATE,
            Permission.DON_VALIDATE,
            Permission.PATIENT_CREATE,
            Permission.PATIENT_READ,
            Permission.PATIENT_UPDATE,
            Permission.PRESCRIPTION_CREATE,
            Permission.PRESCRIPTION_READ,
            Permission.RESULTAT_CREATE,
            Permission.RESULTAT_READ,
            Permission.RESULTAT_UPDATE,
            Permission.RESULTAT_VALIDATE_INTERNE,
            Permission.RESULTAT_VALIDATE_BIOLOGISTE,
            Permission.PSL_CREATE,
            Permission.PSL_READ,
            Permission.PSL_UPDATE,
            Permission.PSL_QUALIFY,
            Permission.PSL_DISTRIBUTE,
            Permission.QUALITE_CQI,
            Permission.QUALITE_EEQ,
            Permission.QUALITE_CAPA,
            Permission.AUTOMATE_CONFIG,
            Permission.AUTOMATE_READ,
            Permission.REPORT_GENERATE,
            Permission.REPORT_EXPORT,
        },
    ),
    Role.BIOLOGISTE: RoleDefinition(
        name="Biologiste Transfusionnel",
        description="Validation biologique et supervision",
        permissions={
            Permission.DONOR_READ,
            Permission.DON_CREATE,
            Permission.DON_READ,
            Permission.DON_UPDATE,
            Permission.DON_VALIDATE,
            Permission.PATIENT_CREATE,
            Permission.PATIENT_READ,
            Permission.PATIENT_UPDATE,
            Permission.PRESCRIPTION_CREATE,
            Permission.PRESCRIPTION_READ,
            Permission.RESULTAT_CREATE,
            Permission.RESULTAT_READ,
            Permission.RESULTAT_UPDATE,
            Permission.RESULTAT_VALIDATE_INTERNE,
            Permission.RESULTAT_VALIDATE_BIOLOGISTE,
            Permission.PSL_CREATE,
            Permission.PSL_READ,
            Permission.PSL_UPDATE,
            Permission.PSL_QUALIFY,
            Permission.PSL_DISTRIBUTE,
            Permission.QUALITE_CQI,
            Permission.QUALITE_EEQ,
            Permission.QUALITE_CAPA,
            Permission.AUTOMATE_READ,
            Permission.REPORT_GENERATE,
            Permission.REPORT_EXPORT,
        },
    ),
    Role.TECHNICIEN: RoleDefinition(
        name="Technicien de Laboratoire",
        description="Analyses et saisie des résultats",
        permissions={
            Permission.DONOR_READ,
            Permission.DON_CREATE,
            Permission.DON_READ,
            Permission.DON_UPDATE,
            Permission.PATIENT_CREATE,
            Permission.PATIENT_READ,
            Permission.PRESCRIPTION_CREATE,
            Permission.PRESCRIPTION_READ,
            Permission.RESULTAT_CREATE,
            Permission.RESULTAT_READ,
            Permission.RESULTAT_UPDATE,
            Permission.RESULTAT_VALIDATE_INTERNE,
            Permission.PSL_CREATE,
            Permission.PSL_READ,
            Permission.PSL_QUALIFY,
            Permission.QUALITE_CQI,
            Permission.QUALITE_EEQ,
            Permission.AUTOMATE_READ,
        },
    ),
    Role.SAISSEUR: RoleDefinition(
        name="Personnel d'Accueil / Saisisseur",
        description="Accueil et saisie administrative",
        permissions={
            Permission.DONOR_CREATE,
            Permission.DONOR_READ,
            Permission.DONOR_UPDATE,
            Permission.DONOR_CONSENT,
            Permission.PATIENT_CREATE,
            Permission.PATIENT_READ,
            Permission.PATIENT_UPDATE,
            Permission.PRESCRIPTION_CREATE,
            Permission.PRESCRIPTION_READ,
            Permission.DON_READ,
            Permission.PSL_READ,
        },
    ),
    Role.PRESCRIPTEUR: RoleDefinition(
        name="Prescripteur",
        description="Médecin prescripteur externe",
        permissions={
            Permission.PRESCRIPTION_CREATE,
            Permission.PRESCRIPTION_READ,
            Permission.RESULTAT_READ,
        },
    ),
    Role.DONNEUR: RoleDefinition(
        name="Donneur",
        description="Donneur consultant son historique",
        permissions={
            Permission.DONOR_READ,
            Permission.DON_READ,
        },
    ),
}


class RBACManager:
    """Role-Based Access Control manager."""

    def __init__(self):
        self.role_permissions = ROLE_PERMISSIONS

    def get_role_permissions(self, role: Role) -> Set[Permission]:
        """Get all permissions for a role."""
        role_def = self.role_permissions.get(role)
        if not role_def:
            return set()
        return role_def.permissions

    def has_permission(self, role: Role, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        return permission in self.get_role_permissions(role)

    def get_user_permissions(self, user_roles: List[Role]) -> Set[Permission]:
        """Get aggregated permissions for a user with multiple roles."""
        permissions = set()
        for role in user_roles:
            permissions.update(self.get_role_permissions(role))
        return permissions

    def check_access(
        self, user_roles: List[Role], required_permission: Permission
    ) -> bool:
        """
        Check if user with given roles has required permission.
        
        Args:
            user_roles: List of roles assigned to user
            required_permission: Permission needed
        
        Returns:
            True if access granted, False otherwise
        """
        user_permissions = self.get_user_permissions(user_roles)
        return required_permission in user_permissions

    def list_roles(self) -> List[dict]:
        """List all roles with descriptions."""
        return [
            {"name": role.value, "description": role_def.description}
            for role, role_def in self.role_permissions.items()
        ]

    def get_available_permissions(self) -> List[str]:
        """List all available permissions."""
        return [p.value for p in Permission]
