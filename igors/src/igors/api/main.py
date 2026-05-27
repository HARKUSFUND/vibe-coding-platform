"""
API REST FastAPI pour l'interopérabilité avec les systèmes externes.
CDC §5.2, §5.5: Portail prescripteurs et transmission de résultats.
"""
from fastapi import FastAPI, Depends, HTTPException, status, Security, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
import logging

from igors.infrastructure.database.session import get_db_session
from igors.infrastructure.models.user import UserModel
from igors.infrastructure.models.patient import PatientModel
from igors.infrastructure.models.resultat import ResultatModel
from igors.core.services.auth_service import AuthService
from igors.core.services.validation_service import ValidationBiologiqueService
from igors.infrastructure.reporting.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)

# Configuration JWT
JWT_SECRET = "votre_secret_jwt_tres_secured"  # À mettre dans .env
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

app = FastAPI(
    title="IGORS API",
    description="API REST du Laboratoire IGORS - CNTS Côte d'Ivoire",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - Autoriser les domaines des prescripteurs
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://portail.cntsci.ci",
        # Ajouter les domaines autorisés des prescripteurs
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


# ========== MODÈLES PYDANTIC ==========

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class PrescripteurLogin(BaseModel):
    identifiant: str
    mot_de_passe: str

class PatientSearch(BaseModel):
    nir: Optional[str] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date_naissance: Optional[str] = None

class ResultatSchema(BaseModel):
    id: int
    examen_nom: str
    valeur: Optional[str]
    unite: Optional[str]
    reference_basse: Optional[float]
    reference_haute: Optional[float]
    statut_validation: str
    date_analyse: datetime
    
    class Config:
        from_attributes = True

class CompteRenduSchema(BaseModel):
    patient_id: int
    patient_nom: str
    patient_prenom: str
    numero_dossier: str
    date_prelevement: datetime
    resultats: List[ResultatSchema]
    biologiste_validateur: str


# ========== AUTHENTIFICATION ==========

def verifier_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """Vérifier le token JWT et retourner les claims."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Vérifier l'expiration
        exp = payload.get('exp')
        if exp and datetime.fromtimestamp(exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expiré"
            )
        
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )


@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login_prescripteur(login_data: PrescripteurLogin):
    """
    Authentification d'un prescripteur.
    CDC §4.6: Portail prescripteur (API sécurisée).
    """
    db = next(get_db_session())
    
    auth_service = AuthService(db)
    
    # Vérifier les identifiants
    user = auth_service.authentifier_user(
        login_data.identifiant,
        login_data.mot_de_passe
    )
    
    if not user or user.role != 'prescripteur':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalids ou compte non autorisé"
        )
    
    # Générer le token JWT
    expiration = datetime.now() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        'sub': user.id,
        'identifiant': user.identifiant,
        'nom': user.nom,
        'role': user.role,
        'exp': expiration
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_HOURS * 3600
    )


# ========== RÉSULTATS D'ANALYSES ==========

@app.get("/api/v1/resultats/patient/{patient_id}", response_model=List[ResultatSchema])
async def get_resultats_patient(
    patient_id: int,
    current_user: Dict[str, Any] = Depends(verifier_token)
):
    """
    Récupérer les résultats validés d'un patient.
    CDC §4.6: Consultation résultats via API.
    """
    db = next(get_db_session())
    
    # Vérifier que le prescripteur a accès à ce patient
    # (logique métier à implémenter selon les règles d'accès)
    
    resultats = db.query(ResultatModel).filter(
        ResultatModel.patient_id == patient_id,
        ResultatModel.statut_validation == 'valide'
    ).all()
    
    return resultats


@app.get("/api/v1/resultats/derniers", response_model=List[CompteRenduSchema])
async def get_derniers_resultats(
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(verifier_token)
):
    """Récupérer les derniers résultats validés."""
    db = next(get_db_session())
    
    # Requête optimisée avec jointures
    resultats = db.query(ResultatModel).filter(
        ResultatModel.statut_validation == 'valide'
    ).order_by(ResultatModel.date_analyse.desc()).limit(limit).all()
    
    # Formater la réponse
    comptes_rendus = []
    for res in resultats:
        patient = db.query(PatientModel).get(res.patient_id)
        if patient:
            comptes_rendus.append(CompteRenduSchema(
                patient_id=patient.id,
                patient_nom=patient.nom,
                patient_prenom=patient.prenom,
                numero_dossier=f"CR{res.id:08d}",
                date_prelevement=res.date_prelevement,
                resultats=[res],
                biologiste_validateur=res.validateur.nom if res.validateur else "N/A"
            ))
    
    return comptes_rendus


@app.get("/api/v1/resultats/{resultat_id}/pdf")
async def telecharger_compte_rendu_pdf(
    resultat_id: int,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(verifier_token)
):
    """
    Générer et télécharger un compte rendu PDF.
    CDC §4.6: Génération PDF personnalisable.
    """
    db = next(get_db_session())
    
    resultat = db.query(ResultatModel).get(resultat_id)
    if not resultat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Résultat introuvable"
        )
    
    if resultat.statut_validation != 'valide':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Résultat non validé - ne peut être diffusé"
        )
    
    # Récupérer les données nécessaires
    patient = db.query(PatientModel).get(resultat.patient_id)
    biologiste = resultat.validateur
    
    if not patient or not biologiste:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Données incomplètes"
        )
    
    # Générer le PDF
    pdf_generator = PDFGenerator()
    
    donnees_resultat = {
        'nom_examen': resultat.examen.nom if resultat.examen else 'N/A',
        'valeur_numerique': resultat.valeur_numerique,
        'unite': resultat.unite,
        'reference_basse': resultat.reference_basse,
        'reference_haute': resultat.reference_haute,
        'commentaire': resultat.commentaire
    }
    
    pdf_path = pdf_generator.generer_compte_rendu(
        patient={
            'nom': patient.nom,
            'prenom': patient.prenom,
            'date_naissance': patient.date_naissance,
            'sexe': patient.sexe,
            'nir': patient.nir
        },
        prescripteur={
            'nom': current_user.get('nom'),
            'structure': 'Prescripteur externe',
            'telephone': ''
        },
        resultats=[donnees_resultat],
        biologiste={
            'nom': f"Dr. {biologiste.nom} {biologiste.prenom}"
        },
        date_prelevement=resultat.date_prelevement,
        date_validation=resultat.date_validation,
        numero_dossier=f"CR{resultat.id:08d}"
    )
    
    # Retourner le chemin du fichier (ou le streamer directement)
    return {
        "filename": pdf_path.name,
        "path": str(pdf_path),
        "message": "PDF généré avec succès"
    }


# ========== PATIENTS ==========

@app.post("/api/v1/patients/rechercher")
async def rechercher_patients(
    search_criteria: PatientSearch,
    current_user: Dict[str, Any] = Depends(verifier_token)
):
    """
    Rechercher des patients par critères.
    CDC §4.6: Portail prescripteur.
    """
    db = next(get_db_session())
    
    query = db.query(PatientModel)
    
    if search_criteria.nir:
        query = query.filter(PatientModel.nir == search_criteria.nir)
    if search_criteria.nom:
        query = query.filter(PatientModel.nom.ilike(f"%{search_criteria.nom}%"))
    if search_criteria.prenom:
        query = query.filter(PatientModel.prenom.ilike(f"%{search_criteria.prenom}%"))
    if search_criteria.date_naissance:
        query = query.filter(PatientModel.date_naissance == search_criteria.date_naissance)
    
    patients = query.limit(50).all()
    
    return [
        {
            'id': p.id,
            'nom': p.nom,
            'prenom': p.prenom,
            'date_naissance': p.date_naissance,
            'sexe': p.sexe,
            'nir': p.nir
        }
        for p in patients
    ]


# ========== INDICATEURS ET STATISTIQUES ==========

@app.get("/api/v1/stats/indicateurs")
async def get_indicateurs_activite(
    periode_jours: int = 30,
    current_user: Dict[str, Any] = Depends(verifier_token)
):
    """
    Récupérer les indicateurs d'activité du laboratoire.
    CDC §4.8: Tableaux de bord personnalisables.
    """
    db = next(get_db_session())
    from datetime import timedelta
    
    date_debut = datetime.now() - timedelta(days=periode_jours)
    
    # Nombre de résultats validés
    nb_resultats = db.query(ResultatModel).filter(
        ResultatModel.statut_validation == 'valide',
        ResultatModel.date_analyse >= date_debut
    ).count()
    
    # Délai moyen de rendu
    # (à calculer avec date_prelevement et date_validation)
    
    # Taux de validation automatique
    # (à calculer si un flag 'validation_auto' existe)
    
    return {
        "periode_jours": periode_jours,
        "nombre_resultats_valides": nb_resultats,
        "delai_moi_rendu_heures": None,  # À implémenter
        "taux_validation_auto": None,     # À implémenter
        "examens_plus_frequents": []      # À implémenter
    }


# ========== HEALTH CHECK ==========

@app.get("/health")
async def health_check():
    """Endpoint de vérification de santé de l'API."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# ========== GESTION DES ERREURS ==========

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.warning(f"HTTP Exception: {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return {
        "error": "Erreur interne du serveur",
        "status_code": 500
    }
