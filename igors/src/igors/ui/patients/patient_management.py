# -*- coding: utf-8 -*-
"""
patient_management.py — Module de gestion des patients IGORS v2.0

Fonctionnalités :
- Recherche et filtrage des patients
- Pagination
- CRUD complet des patients
- Historique des résultats par patient
- Import prescriptions (CSV/Excel)

Architecture : UI PyQt6 → PatientService → PatientRepository → PostgreSQL
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from PyQt6.QtCore import Qt, QSettings, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QComboBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QGroupBox,
                             QSpinBox, QDialog, QMessageBox, QDialogButtonBox,
                             QFileDialog, QDateEdit)

from ...infrastructure.database.session import get_db_session
from ...infrastructure.repositories.patient_repo import PatientRepository
from ...core.services.patient_service import PatientService
from ...ui.theme import get_stylesheet, COLORS
from ...config.settings import settings

# Fichier de fallback pour données locales chiffrées
PATIENTS_STORE_FILE = os.path.join(settings.DATA_DIR, "patients_encrypted.json")


class PatientDialog(QDialog):
    """Dialog de création/modification d'un patient."""

    def __init__(self, patient_data: Optional[Dict] = None, parent=None, user_role: str = "", user_id: str = ""):
        super().__init__(parent)
        self.patient_data = patient_data or {}
        self.user_role = user_role
        self.user_id = user_id
        self.is_new = patient_data is None
        
        self.setWindowTitle("Nouveau Patient" if self.is_new else "Modifier Patient")
        self.setMinimumWidth(500)
        self.setStyleSheet(get_stylesheet())
        
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Informations personnelles
        perso_grp = QGroupBox("📋 Informations Personnelles")
        pl = QVBoxLayout(perso_grp)
        
        # Code patient (lecture seule si modification)
        hl1 = QHBoxLayout()
        hl1.addWidget(QLabel("Code Patient:"))
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Généré automatiquement")
        if not self.is_new:
            self.code_input.setEnabled(False)
        hl1.addWidget(self.code_input)
        pl.addLayout(hl1)
        
        # Nom
        hl2 = QHBoxLayout()
        hl2.addWidget(QLabel("Nom*:"))
        self.nom_input = QLineEdit()
        hl2.addWidget(self.nom_input)
        pl.addLayout(hl2)
        
        # Prénom
        hl3 = QHBoxLayout()
        hl3.addWidget(QLabel("Prénom*:"))
        self.prenom_input = QLineEdit()
        hl3.addWidget(self.prenom_input)
        pl.addLayout(hl3)
        
        # Sexe et Date de naissance
        hl4 = QHBoxLayout()
        hl4.addWidget(QLabel("Sexe*:"))
        self.sexe_combo = QComboBox()
        self.sexe_combo.addItems(["M", "F"])
        hl4.addWidget(self.sexe_combo)
        hl4.addSpacing(20)
        hl4.addWidget(QLabel("Date de naissance:"))
        self.dnaissance_input = QDateEdit()
        self.dnaissance_input.setCalendarPopup(True)
        self.dnaissance_input.setDate(datetime.now().date())
        hl4.addWidget(self.dnaissance_input)
        pl.addLayout(hl4)
        
        # Contact
        hl5 = QHBoxLayout()
        hl5.addWidget(QLabel("Téléphone:"))
        self.contact_input = QLineEdit()
        hl5.addWidget(self.contact_input)
        pl.addLayout(hl5)
        
        # Adresse
        hl6 = QHBoxLayout()
        hl6.addWidget(QLabel("Adresse:"))
        self.adresse_input = QLineEdit()
        hl6.addWidget(self.adresse_input)
        pl.addLayout(hl6)
        
        layout.addWidget(perso_grp)
        
        # Informations complémentaires
        comp_grp = QGroupBox("ℹ️ Informations Complémentaires")
        cl = QVBoxLayout(comp_grp)
        
        # Groupe sanguin
        hl7 = QHBoxLayout()
        hl7.addWidget(QLabel("Groupe Sanguin:"))
        self.groupe_combo = QComboBox()
        self.groupe_combo.addItem("", "")
        groupes = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        for g in groupes:
            self.groupe_combo.addItem(g, g)
        hl7.addWidget(self.groupe_combo)
        cl.addLayout(hl7)
        
        # Antécédents
        hl8 = QHBoxLayout()
        hl8.addWidget(QLabel("Antécédents:"))
        self.antecedents_input = QLineEdit()
        self.antecedents_input.setPlaceholderText("Diabète, HTA, Allergies...")
        hl8.addWidget(self.antecedents_input)
        cl.addLayout(hl8)
        
        layout.addWidget(comp_grp)
        
        # Boutons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        if self.patient_data:
            self.code_input.setText(self.patient_data.get('Pa_code', ''))
            self.nom_input.setText(self.patient_data.get('Pa_nom', ''))
            self.prenom_input.setText(self.patient_data.get('Pa_prenom', ''))
            self.sexe_combo.setCurrentText(self.patient_data.get('Pa_sexe', 'M'))
            self.contact_input.setText(self.patient_data.get('Pa_contact', ''))
            self.adresse_input.setText(self.patient_data.get('Pa_adresse', ''))
            self.groupe_combo.setCurrentText(self.patient_data.get('Pa_groupe_sanguin', ''))
            self.antecedents_input.setText(self.patient_data.get('Pa_antecedents', ''))
            
            dnaissance = self.patient_data.get('Pa_dnaissance')
            if dnaissance:
                try:
                    date_obj = datetime.strptime(dnaissance, "%Y-%m-%d").date()
                    self.dnaissance_input.setDate(date_obj)
                except:
                    pass

    def _on_accept(self):
        # Validation
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom est obligatoire.")
            return
        if not self.prenom_input.text().strip():
            QMessageBox.warning(self, "Erreur", "Le prénom est obligatoire.")
            return
        
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        return {
            'Pa_code': self.code_input.text().strip() or f"PA{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'Pa_nom': self.nom_input.text().strip(),
            'Pa_prenom': self.prenom_input.text().strip(),
            'Pa_sexe': self.sexe_combo.currentText(),
            'Pa_dnaissance': self.dnaissance_input.date().toString("yyyy-MM-dd"),
            'Pa_contact': self.contact_input.text().strip(),
            'Pa_adresse': self.adresse_input.text().strip(),
            'Pa_groupe_sanguin': self.groupe_combo.currentData(),
            'Pa_antecedents': self.antecedents_input.text().strip(),
        }


class PatientsWidget(QWidget):
    """Widget principal pour la gestion des patients."""
    
    # Signaux
    patient_selected = pyqtSignal(dict)
    prescription_import_requested = pyqtSignal()

    def __init__(self, parent=None, user_role: str = "Administrateur", user_id: str = ""):
        super().__init__(parent)
        self.user_role = user_role
        self.user_id = user_id
        
        # Services
        try:
            self.db_session = get_db_session()
            self.patient_repo = PatientRepository(self.db_session)
            self.patient_service = PatientService(self.patient_repo)
            self.use_database = True
        except Exception as e:
            print(f"⚠️ Base de données non disponible: {e}")
            self.use_database = False
            self.local_patients: List[dict] = []
        
        # Pagination
        self.current_page = 1
        self.total_pages = 1
        self.total_patients = 0
        self.page_size = 25
        
        self._setup_ui()
        
        if self.use_database:
            self._load_patients()
        else:
            self._load_local_patients()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Titre
        title_label = QLabel("🏥 Gestion des Patients")
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)

        # Recherche et filtres
        search_grp = QGroupBox("🔍 Recherche et Filtres")
        sl = QHBoxLayout(search_grp)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par code, nom, prénom…")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self._on_search_patients)
        sl.addWidget(self.search_input)
        
        self.sexe_filter = QComboBox()
        self.sexe_filter.addItem("Tous les sexes", "")
        self.sexe_filter.addItem("Masculin", "M")
        self.sexe_filter.addItem("Féminin", "F")
        self.sexe_filter.currentIndexChanged.connect(self._on_search_patients)
        sl.addWidget(self.sexe_filter)
        
        self.groupe_filter = QComboBox()
        self.groupe_filter.addItem("Tous les groupes", "")
        for g in ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]:
            self.groupe_filter.addItem(f"Groupe {g}", g)
        self.groupe_filter.currentIndexChanged.connect(self._on_search_patients)
        sl.addWidget(self.groupe_filter)
        
        sl.addStretch()
        layout.addWidget(search_grp)

        # Tableau
        self.patients_table = QTableWidget()
        self.patients_table.setColumnCount(9)
        self.patients_table.setHorizontalHeaderLabels([
            "N° Patient", "Nom", "Prénom", "Sexe", "Âge",
            "Gr. Sanguin", "Nbre Prescriptions", "N° Tél", "Adresse"
        ])
        self.patients_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.patients_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.patients_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.patients_table.doubleClicked.connect(self._on_edit_patient)
        layout.addWidget(self.patients_table)

        # Pagination
        pag_grp = QGroupBox("Pagination")
        pl = QHBoxLayout(pag_grp)
        
        self.pagination_info = QLabel("Page 0 sur 0 (0 patients)")
        pl.addWidget(self.pagination_info)
        
        pl.addStretch()
        
        self.prev_page_btn = QPushButton("◀ Précédent")
        self.prev_page_btn.clicked.connect(self._on_prev_page)
        pl.addWidget(self.prev_page_btn)
        
        self.page_spinner = QSpinBox()
        self.page_spinner.setMinimum(1)
        self.page_spinner.valueChanged.connect(self._on_page_changed)
        pl.addWidget(self.page_spinner)
        
        self.next_page_btn = QPushButton("Suivant ▶")
        self.next_page_btn.clicked.connect(self._on_next_page)
        pl.addWidget(self.next_page_btn)
        
        layout.addWidget(pag_grp)

        # Actions
        act_grp = QGroupBox("Actions")
        al = QHBoxLayout(act_grp)
        
        new_btn = QPushButton("➕ Nouveau Patient")
        new_btn.setObjectName("primaryButton")
        new_btn.clicked.connect(self._on_new_patient)
        al.addWidget(new_btn)
        
        edit_btn = QPushButton("✏️ Modifier")
        edit_btn.clicked.connect(self._on_edit_current_patient)
        al.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Supprimer")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self._on_delete_patient)
        al.addWidget(delete_btn)
        
        history_btn = QPushButton("📊 Historique Résultats")
        history_btn.clicked.connect(self._on_view_history)
        al.addWidget(history_btn)
        
        import_btn = QPushButton("📥 Import Prescriptions")
        import_btn.clicked.connect(self._on_import_prescriptions)
        al.addWidget(import_btn)
        
        al.addStretch()
        layout.addWidget(act_grp)

    # ------------------------------------------------------------------
    # Persistance locale (fallback)
    # ------------------------------------------------------------------
    def _load_local_patients(self) -> None:
        """Charge les patients depuis le fichier local chiffré."""
        if os.path.exists(PATIENTS_STORE_FILE):
            try:
                from ...infrastructure.security.encryption import decrypt_text
                with open(PATIENTS_STORE_FILE, 'r', encoding='utf-8') as f:
                    raw = f.read()
                if raw.strip():
                    data = decrypt_text(raw)
                    if data:
                        patients = json.loads(data)
                        self.local_patients = [p for p in patients if isinstance(p, dict)]
                        return
            except Exception as exc:
                print(f"Lecture patients chiffrés impossible : {exc}")

        try:
            settings_qt = QSettings("CNTSCI", "IGORS")
            raw = settings_qt.value("local_patients", [])
            self.local_patients = [p for p in (raw or []) if isinstance(p, dict)]
            if self.local_patients:
                print(f"Migration de {len(self.local_patients)} patient(s) depuis QSettings.")
                self._save_local_patients()
        except Exception as exc:
            print(f"Lecture QSettings impossible : {exc}")
            self.local_patients = []

    def _save_local_patients(self) -> None:
        """Sauvegarde les patients dans le fichier local chiffré."""
        try:
            from ...infrastructure.security.encryption import encrypt_text
            payload = json.dumps(self.local_patients, ensure_ascii=False)
            with open(PATIENTS_STORE_FILE, 'w', encoding='utf-8') as f:
                f.write(encrypt_text(payload))
            try:
                os.chmod(PATIENTS_STORE_FILE, 0o600)
            except OSError:
                pass
        except Exception as exc:
            print(f"Sauvegarde patients impossible : {exc}")

    # ------------------------------------------------------------------
    # Recherche & pagination
    # ------------------------------------------------------------------
    def _filter_patients(self) -> List[dict]:
        """Filtre les patients selon les critères."""
        q = self.search_input.text().strip().lower()
        sexe = self.sexe_filter.currentData()
        groupe = self.groupe_filter.currentData()
        
        if self.use_database:
            # TODO: Implémenter filtre repository
            result = self.patient_repo.get_all()
        else:
            result = self.local_patients
            
        if q:
            result = [p for p in result
                      if q in str(p.get('Pa_code', '')).lower()
                      or q in str(p.get('Pa_nom', '')).lower()
                      or q in str(p.get('Pa_prenom', '')).lower()]
        if sexe:
            result = [p for p in result if p.get('Pa_sexe') == sexe]
        if groupe:
            result = [p for p in result if p.get('Pa_groupe_sanguin') == groupe]
        return result

    def _on_search_patients(self) -> None:
        self.current_page = 1
        self._load_patients()

    def _on_page_changed(self) -> None:
        self.current_page = self.page_spinner.value()
        self._load_patients()

    def _on_prev_page(self) -> None:
        if self.current_page > 1:
            self.current_page -= 1
            self.page_spinner.setValue(self.current_page)
            self._load_patients()

    def _on_next_page(self) -> None:
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.page_spinner.setValue(self.current_page)
            self._load_patients()

    def _load_patients(self) -> None:
        """Charge et affiche les patients avec pagination."""
        try:
            patients = self._filter_patients()
            self.total_patients = len(patients)
            self.total_pages = max(1, (self.total_patients + self.page_size - 1) // self.page_size)
            
            if self.current_page > self.total_pages:
                self.current_page = self.total_pages
            
            start = (self.current_page - 1) * self.page_size
            page = patients[start:start + self.page_size]
            
            self._update_patients_table(page)
            self._update_pagination_controls()
        except Exception as exc:
            print(f"Erreur chargement patients : {exc}")

    def _update_patients_table(self, patients: List[dict]) -> None:
        """Met à jour le tableau avec les patients."""
        self.patients_table.setRowCount(len(patients))
        
        for row, p in enumerate(patients):
            self.patients_table.setItem(row, 0, QTableWidgetItem(str(p.get('Pa_code', ''))))
            self.patients_table.setItem(row, 1, QTableWidgetItem(str(p.get('Pa_nom', ''))))
            self.patients_table.setItem(row, 2, QTableWidgetItem(str(p.get('Pa_prenom', ''))))
            self.patients_table.setItem(row, 3, QTableWidgetItem("M" if p.get('Pa_sexe') == 'M' else "F"))
            self.patients_table.setItem(row, 4, QTableWidgetItem(self._calculate_age(p.get('Pa_dnaissance', ''))))
            self.patients_table.setItem(row, 5, QTableWidgetItem(str(p.get('Pa_groupe_sanguin', ''))))
            self.patients_table.setItem(row, 6, QTableWidgetItem(str(p.get('Pa_nbr_prescriptions', 0))))
            self.patients_table.setItem(row, 7, QTableWidgetItem(str(p.get('Pa_contact', ''))))
            self.patients_table.setItem(row, 8, QTableWidgetItem(str(p.get('Pa_adresse', ''))))

    def _update_pagination_controls(self) -> None:
        """Met à jour les contrôles de pagination."""
        self.pagination_info.setText(f"Page {self.current_page} sur {self.total_pages} ({self.total_patients} patient(s))")
        self.page_spinner.blockSignals(True)
        self.page_spinner.setMaximum(max(1, self.total_pages))
        self.page_spinner.setValue(self.current_page)
        self.page_spinner.blockSignals(False)
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < self.total_pages)

    def _calculate_age(self, dnaissance: str) -> str:
        """Calcule l'âge à partir de la date de naissance."""
        if not dnaissance:
            return ""
        try:
            birth_date = datetime.strptime(dnaissance, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return f"{age} ans"
        except:
            return ""

    # ------------------------------------------------------------------
    # CRUD patients
    # ------------------------------------------------------------------
    def _existing_codes(self) -> set:
        """Retourne les codes patients existants."""
        if self.use_database:
            return {p.Pa_code for p in self.patient_repo.get_all()}
        return {p.get('Pa_code', '') for p in self.local_patients}

    def _on_new_patient(self) -> None:
        """Crée un nouveau patient."""
        dlg = PatientDialog(parent=self, user_role=self.user_role, user_id=self.user_id, existing_codes=self._existing_codes())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            patient = dlg.get_data()
            
            if patient.get('Pa_code') in self._existing_codes():
                QMessageBox.warning(self, "Doublon", f"Le code {patient['Pa_code']} existe déjà.")
                return
            
            if self.use_database:
                try:
                    self.patient_service.create_patient(patient)
                    QMessageBox.information(self, "Succès", "Patient enregistré avec succès.")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement: {e}")
            else:
                self.local_patients.append(patient)
                self._save_local_patients()
                QMessageBox.information(self, "Succès", "Patient enregistré (mode local).")
            
            self._load_patients()

    def _on_edit_current_patient(self) -> None:
        """Modifie le patient sélectionné."""
        row = self.patients_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un patient.")
            return
        self._open_edit_for_row(row)

    def _on_edit_patient(self, index) -> None:
        """Double-clic sur une ligne pour édition."""
        self._open_edit_for_row(index.row())

    def _open_edit_for_row(self, row: int) -> None:
        """Ouvre le dialog d'édition pour une ligne donnée."""
        item = self.patients_table.item(row, 0)
        if not item:
            return
        
        code = item.text()
        
        if self.use_database:
            patient = self.patient_repo.get_by_code(code)
            if not patient:
                QMessageBox.warning(self, "Erreur", "Patient introuvable.")
                return
            patient_dict = {
                'Pa_code': patient.Pa_code,
                'Pa_nom': patient.Pa_nom,
                'Pa_prenom': patient.Pa_prenom,
                'Pa_sexe': patient.Pa_sexe,
                'Pa_dnaissance': patient.Pa_dnaissance.isoformat() if patient.Pa_dnaissance else '',
                'Pa_contact': patient.Pa_contact,
                'Pa_adresse': patient.Pa_adresse,
                'Pa_groupe_sanguin': patient.Pa_groupe_sanguin,
                'Pa_antecedents': patient.Pa_antecedents,
            }
        else:
            patient = next((p for p in self.local_patients if p.get('Pa_code') == code), None)
            patient_dict = patient
        
        if not patient_dict:
            QMessageBox.warning(self, "Erreur", "Patient introuvable.")
            return
        
        dlg = PatientDialog(patient_data=patient_dict, parent=self, user_role=self.user_role, user_id=self.user_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            updated = dlg.get_data()
            
            if self.use_database:
                try:
                    self.patient_service.update_patient(code, updated)
                    QMessageBox.information(self, "Succès", "Patient modifié.")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de la modification: {e}")
            else:
                for i, p in enumerate(self.local_patients):
                    if p.get('Pa_code') == code:
                        self.local_patients[i] = updated
                        break
                self._save_local_patients()
                QMessageBox.information(self, "Succès", "Patient modifié (mode local).")
            
            self._load_patients()

    def _on_delete_patient(self) -> None:
        """Supprime le patient sélectionné."""
        row = self.patients_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un patient.")
            return
        
        code = self.patients_table.item(row, 0).text()
        reply = QMessageBox.question(
            self, "Confirmer", 
            f"Supprimer définitivement le patient {code} ?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.use_database:
                try:
                    self.patient_service.delete_patient(code)
                    QMessageBox.information(self, "Succès", "Patient supprimé.")
                except Exception as e:
                    QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {e}")
            else:
                self.local_patients = [p for p in self.local_patients if p.get('Pa_code') != code]
                self._save_local_patients()
                QMessageBox.information(self, "Succès", "Patient supprimé (mode local).")
            
            self._load_patients()

    def _on_view_history(self) -> None:
        """Affiche l'historique des résultats du patient sélectionné."""
        row = self.patients_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un patient.")
            return
        
        code = self.patients_table.item(row, 0).text()
        
        # Émettre un signal pour ouvrir l'écran d'historique
        if self.use_database:
            patient = self.patient_repo.get_by_code(code)
            if patient:
                self.patient_selected.emit({
                    'Pa_code': patient.Pa_code,
                    'Pa_nom': patient.Pa_nom,
                    'Pa_prenom': patient.Pa_prenom,
                })
        else:
            patient = next((p for p in self.local_patients if p.get('Pa_code') == code), None)
            if patient:
                self.patient_selected.emit(patient)

    def _on_import_prescriptions(self) -> None:
        """Importe des prescriptions depuis un fichier CSV/Excel."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importer Prescriptions", "", 
            "Fichiers CSV/Excel (*.csv *.xlsx *.xls);;Tous les fichiers (*)"
        )
        
        if file_path:
            # TODO: Implémenter l'import
            QMessageBox.information(self, "Info", "Fonctionnalité d'import en cours de développement.\nFichier sélectionné: " + file_path)
