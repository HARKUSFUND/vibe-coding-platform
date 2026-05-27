"""
Générateur de documents PDF pour les comptes rendus d'analyses.
Conforme CDC §4.6 avec archivage PDF/A-3.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import logging

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Générateur de comptes rendus d'analyses médicales."""
    
    def __init__(self, output_dir: str = "data/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Enregistrer les polices (si disponibles)
        try:
            pdfmetrics.registerFont(TTFont('Arial', '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Bold', '/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf'))
        except Exception:
            logger.warning("Polices personnalisées non disponibles, utilisation des polices par défaut")
        
        self.styles = getSampleStyleSheet()
        self._configurer_styles()
    
    def _configurer_styles(self):
        """Configurer les styles de paragraphe."""
        # Style titre principal
        self.styles.add(ParagraphStyle(
            name='TitrePrincipal',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a5276'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Style sous-titre
        self.styles.add(ParagraphStyle(
            name='SousTitre',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2e86c1'),
            spaceAfter=6
        ))
        
        # Style corps de texte
        self.styles.add(ParagraphStyle(
            name='CorpsTexte',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
            alignment=TA_JUSTIFY
        ))
        
        # Style pour les valeurs normales/anormales
        self.styles.add(ParagraphStyle(
            name='ValeurNormale',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black
        ))
        
        self.styles.add(ParagraphStyle(
            name='ValeurAnormale',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            fontName='Helvetica-Bold'
        ))
    
    def generer_compte_rendu(
        self,
        patient: Dict[str, Any],
        prescripteur: Dict[str, Any],
        resultats: List[Dict[str, Any]],
        biologiste: Dict[str, Any],
        date_prelevement: datetime,
        date_validation: datetime,
        numero_dossier: str,
        logo_path: Optional[str] = None
    ) -> Path:
        """
        Générer un compte rendu d'analyses complet.
        CDC §4.6: Génération PDF personnalisable.
        """
        
        # Nom du fichier
        filename = f"CR_{numero_dossier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = self.output_dir / filename
        
        # Créer le document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        # ========== EN-TÊTE ==========
        elements.extend(self._creer_en_tete(patient, prescripteur, numero_dossier, logo_path))
        
        # ========== INFORMATIONS PATIENT ==========
        elements.extend(self._creer_info_patient(patient, date_prelevement))
        
        # ========== TABLEAU DES RÉSULTATS ==========
        elements.extend(self._creer_tableau_resultats(resultats))
        
        # ========== PIED DE PAGE / VALIDATION ==========
        elements.extend(self._creer_pied_page(biologiste, date_validation))
        
        # Générer le PDF
        doc.build(elements)
        
        logger.info(f"Compte rendu généré: {output_path}")
        return output_path
    
    def _creer_en_tete(
        self,
        patient: Dict,
        prescripteur: Dict,
        numero_dossier: str,
        logo_path: Optional[str]
    ) -> List:
        """Créer l'en-tête du compte rendu."""
        elements = []
        
        # Logo et titre
        header_data = []
        
        if logo_path:
            try:
                logo = Image(logo_path, width=3*cm, height=2*cm)
                header_data.append([logo, ""])
            except Exception:
                header_data.append(["", ""])
        else:
            header_data.append(["", ""])
        
        header_data.append([
            Paragraph("<b>CNTS - Centre National de Transfusion Sanguine</b>", self.styles['TitrePrincipal']),
            Paragraph("<b>Laboratoire d'Hématologie</b>", self.styles['SousTitre'])
        ])
        
        header_data.append([
            Paragraph(f"N° Dossier: <b>{numero_dossier}</b>", self.styles['CorpsTexte']),
            Paragraph(f"Date: <b>{datetime.now().strftime('%d/%m/%Y %H:%M')}</b>", self.styles['CorpsTexte'])
        ])
        
        table_header = Table(header_data, colWidths=[5*cm, 10*cm])
        table_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f4f6f7')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ]))
        
        elements.append(table_header)
        elements.append(Spacer(1, 1*cm))
        
        # Prescripteur
        if prescripteur:
            presc_text = f"""
            <b>Prescripteur:</b> {prescripteur.get('nom', 'N/A')}<br/>
            <b>Structure:</b> {prescripteur.get('structure', 'N/A')}<br/>
            <b>Téléphone:</b> {prescripteur.get('telephone', 'N/A')}
            """
            elements.append(Paragraph(presc_text, self.styles['CorpsTexte']))
            elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _creer_info_patient(
        self,
        patient: Dict,
        date_prelevement: datetime
    ) -> List:
        """Créer la section informations patient."""
        elements = []
        
        patient_data = [
            ['Nom:', patient.get('nom', 'N/A')],
            ['Prénom:', patient.get('prenom', 'N/A')],
            ['Date de naissance:', patient.get('date_naissance', 'N/A')],
            ['Sexe:', patient.get('sexe', 'N/A')],
            ['NIR/Identifiant:', patient.get('nir', 'N/A')],
            ['Date de prélèvement:', date_prelevement.strftime('%d/%m/%Y %H:%M')]
        ]
        
        table_patient = Table(patient_data, colWidths=[4*cm, 8*cm])
        table_patient.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eaf2f8')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1a5276')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        elements.append(table_patient)
        elements.append(Spacer(1, 1*cm))
        
        return elements
    
    def _creer_tableau_resultats(
        self,
        resultats: List[Dict[str, Any]]
    ) -> List:
        """Créer le tableau des résultats d'analyses."""
        elements = []
        
        # Titre de section
        elements.append(Paragraph("<b>RÉSULTATS DES ANALYSES</b>", self.styles['SousTitre']))
        elements.append(Spacer(1, 0.5*cm))
        
        # En-têtes du tableau
        table_data = [[
            Paragraph("<b>Examen</b>", self.styles['CorpsTexte']),
            Paragraph("<b>Valeur</b>", self.styles['CorpsTexte']),
            Paragraph("<b>Unité</b>", self.styles['CorpsTexte']),
            Paragraph("<b>Valeurs de référence</b>", self.styles['CorpsTexte']),
            Paragraph("<b>Statut</b>", self.styles['CorpsTexte'])
        ]]
        
        # Lignes de résultats
        for res in resultats:
            # Déterminer si la valeur est anormale
            statut = "Normal"
            style_valeur = 'ValeurNormale'
            
            valeur = res.get('valeur_numerique')
            ref_bas = res.get('reference_basse')
            ref_haut = res.get('reference_haute')
            
            if valeur is not None:
                if ref_bas and valeur < ref_bas:
                    statut = "BAS"
                    style_valeur = 'ValeurAnormale'
                elif ref_haut and valeur > ref_haut:
                    statut = "HAUT"
                    style_valeur = 'ValeurAnormale'
            
            # Formater la valeur
            valeur_str = f"{valeur:.2f}" if valeur is not None else "N/A"
            
            table_data.append([
                Paragraph(res.get('nom_examen', 'N/A'), self.styles['CorpsTexte']),
                Paragraph(valeur_str, getattr(self.styles, style_valeur)),
                Paragraph(res.get('unite', ''), self.styles['CorpsTexte']),
                Paragraph(f"{ref_bas or 'N/A'} - {ref_haut or 'N/A'}", self.styles['CorpsTexte']),
                Paragraph(statut, self.styles['CorpsTexte'])
            ])
        
        # Créer le tableau
        table_resultats = Table(table_data, colWidths=[5*cm, 3*cm, 2*cm, 4*cm, 2*cm])
        table_resultats.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f6f7')]),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table_resultats)
        elements.append(Spacer(1, 1*cm))
        
        # Commentaires
        commentaires = [r.get('commentaire') for r in resultats if r.get('commentaire')]
        if commentaires:
            elements.append(Paragraph("<b>Commentaires:</b>", self.styles['SousTitre']))
            for comm in commentaires:
                elements.append(Paragraph(f"• {comm}", self.styles['CorpsTexte']))
            elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _creer_pied_page(
        self,
        biologiste: Dict,
        date_validation: datetime
    ) -> List:
        """Créer le pied de page avec validation."""
        elements = []
        
        elements.append(Spacer(1, 2*cm))
        
        # Signature
        signature_text = f"""
        <b>Validé par:</b> Dr. {biologiste.get('nom', 'N/A')}<br/>
        <b>Date de validation:</b> {date_validation.strftime('%d/%m/%Y %H:%M')}<br/>
        <i>Ce document électronique fait foi de signature.</i>
        """
        
        elements.append(Paragraph(signature_text, self.styles['CorpsTexte']))
        elements.append(Spacer(1, 1*cm))
        
        # Mentions légales
        mentions = """
        <i>
        CNTS - Centre National de Transfusion Sanguine<br/>
        Document généré électroniquement - Toute reproduction doit être intégrale<br/>
        En cas de doute, veuillez contacter le laboratoire.
        </i>
        """
        
        elements.append(Paragraph(mentions, self.styles['CorpsTexte']))
        
        return elements
