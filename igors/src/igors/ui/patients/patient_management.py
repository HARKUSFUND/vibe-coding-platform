"""Écran de gestion des patients - IGORS v2.0"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QDateEdit, QComboBox, QGroupBox, QSplitter, QToolBar,
    QAction, QStatusBar, QDialog, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont

from datetime import datetime, date
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class PatientManagementScreen(QWidget):
    """Interface de gestion des patients avec historique des résultats"""
    
    patient_selected = pyqtSignal(dict)
    patient_created = pyqtSignal(dict)
    
    def __init__(self, patient_service, parent=None):
        super().__init__(parent)
        self.patient_service = patient_service
        self.current_patient = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        title = QLabel("Gestion des Patients")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panneau gauche - Liste des patients
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Barre d'outils
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        self.action_new = QAction("➕ Nouveau", self)
        self.action_new.triggered.connect(self.new_patient)
        toolbar.addAction(self.action_new)
        
        self.action_import = QAction("📥 Import prescriptions", self)
        self.action_import.triggered.connect(self.import_prescriptions)
        toolbar.addAction(self.action_import)
        
        self.action_export = QAction("📤 Exporter", self)
        self.action_export.triggered.connect(self.export_patients)
        toolbar.addAction(self.action_export)
        
        left_layout.addWidget(toolbar)
        
        # Recherche
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par nom, NIR, date naissance...")
        self.search_input.textChanged.connect(self.filter_patients)
        search_btn = QPushButton("🔍")
        search_btn.setFixedWidth(40)
        search_btn.clicked.connect(self.search_patient)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        left_layout.addLayout(search_layout)
        
        # Table des patients
        self.patient_table = QTableWidget()
        self.patient_table.setColumnCount(7)
        self.patient_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Prénom", "NIR", "Date nais.", "Sexe", "Téléphone"
        ])
        self.patient_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.patient_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.patient_table.itemSelectionChanged.connect(self.on_patient_selected)
        left_layout.addWidget(self.patient_table)
        
        splitter.addWidget(left_panel)
        
        # Panneau droit - Détails du patient
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Informations personnelles
        info_group = QGroupBox("Informations Personnelles")
        info_layout = QFormLayout(info_group)
        
        self.nom_input = QLineEdit()
        self.prenom_input = QLineEdit()
        self.date_naissance_input = QDateEdit()
        self.date_naissance_input.setCalendarPopup(True)
        self.sexe_combo = QComboBox()
        self.sexe_combo.addItems(["Masculin", "Féminin"])
        self.nir_input = QLineEdit()
        self.telephone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.adresse_input = QTextEdit()
        self.adresse_input.setMaximumHeight(60)
        self.mutuelle_input = QLineEdit()
        
        info_layout.addRow("Nom:", self.nom_input)
        info_layout.addRow("Prénom:", self.prenom_input)
        info_layout.addRow("Date naissance:", self.date_naissance_input)
        info_layout.addRow("Sexe:", self.sexe_combo)
        info_layout.addRow("NIR:", self.nir_input)
        info_layout.addRow("Téléphone:", self.telephone_input)
        info_layout.addRow("Email:", self.email_input)
        info_layout.addRow("Adresse:", self.adresse_input)
        info_layout.addRow("Mutuelle:", self.mutuelle_input)
        
        right_layout.addWidget(info_group)
        
        # Historique des résultats
        history_group = QGroupBox("Historique des Résultats")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Examen", "Résultat", "Unité", "Statut", "Validateur"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        history_layout.addWidget(self.history_table)
        
        stats_layout = QHBoxLayout()
        self.total_results_label = QLabel("Total résultats: 0")
        stats_layout.addWidget(self.total_results_label)
        stats_layout.addStretch()
        history_layout.addLayout(stats_layout)
        
        right_layout.addWidget(history_group)
        
        # Boutons d'action
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Enregistrer")
        self.save_btn.clicked.connect(self.save_patient)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                padding: 8px 16px; border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        btn_layout.addWidget(self.save_btn)
        
        self.delete_btn = QPushButton("🗑️ Supprimer")
        self.delete_btn.clicked.connect(self.delete_patient)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)
        
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Prêt")
        layout.addWidget(self.status_bar)
        
        # Charger la liste
        self.load_patients()
        
    def load_patients(self):
        """Charger la liste des patients"""
        try:
            patients = self.patient_service.get_all_patients()
            self.patient_table.setRowCount(0)
            
            for patient in patients:
                row = self.patient_table.rowCount()
                self.patient_table.insertRow(row)
                
                self.patient_table.setItem(row, 0, QTableWidgetItem(str(patient.get('id', ''))))
                self.patient_table.setItem(row, 1, QTableWidgetItem(patient.get('nom', '')))
                self.patient_table.setItem(row, 2, QTableWidgetItem(patient.get('prenom', '')))
                self.patient_table.setItem(row, 3, QTableWidgetItem(patient.get('nir', '')))
                
                ddn = patient.get('date_naissance', '')
                if isinstance(ddn, date):
                    ddn = ddn.strftime('%d/%m/%Y')
                self.patient_table.setItem(row, 4, QTableWidgetItem(str(ddn)))
                
                self.patient_table.setItem(row, 5, QTableWidgetItem(patient.get('sexe', '')))
                self.patient_table.setItem(row, 6, QTableWidgetItem(patient.get('telephone', '')))
            
            self.status_bar.showMessage(f"{len(patients)} patient(s) chargé(s)")
            
        except Exception as e:
            logger.error(f"Erreur chargement patients: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les patients: {e}")
            
    def filter_patients(self):
        """Filtrer les patients selon la recherche"""
        search_text = self.search_input.text().lower()
        
        for row in range(self.patient_table.rowCount()):
            match = False
            for col in range(1, 7):
                item = self.patient_table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.patient_table.setRowHidden(row, not match)
            
    def on_patient_selected(self):
        """Afficher les détails du patient sélectionné"""
        selected_rows = self.patient_table.selectedItems()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        patient_id = self.patient_table.item(row, 0).text()
        
        try:
            patient = self.patient_service.get_patient_by_id(int(patient_id))
            self.current_patient = patient
            
            # Remplir les champs
            self.nom_input.setText(patient.get('nom', ''))
            self.prenom_input.setText(patient.get('prenom', ''))
            
            if patient.get('date_naissance'):
                ddn = patient['date_naissance']
                if isinstance(ddn, str):
                    ddn = QDate.fromString(ddn, 'yyyy-MM-dd')
                self.date_naissance_input.setDate(ddn)
            
            self.sexe_combo.setCurrentText("Masculin" if patient.get('sexe') == 'M' else "Féminin")
            self.nir_input.setText(patient.get('nir', ''))
            self.telephone_input.setText(patient.get('telephone', ''))
            self.email_input.setText(patient.get('email', ''))
            self.adresse_input.setText(patient.get('adresse', ''))
            self.mutuelle_input.setText(patient.get('mutuelle', ''))
            
            # Historique des résultats
            self.load_patient_history(patient)
            
            self.status_bar.showMessage(f"Patient: {patient.get('nom')} {patient.get('prenom')}")
            
        except Exception as e:
            logger.error(f"Erreur chargement détails patient: {e}")
            
    def load_patient_history(self, patient):
        """Charger l'historique des résultats du patient"""
        try:
            history = self.patient_service.get_patient_results(patient.get('id'))
            self.history_table.setRowCount(0)
            
            total_results = 0
            
            for result in history:
                row = self.history_table.rowCount()
                self.history_table.insertRow(row)
                
                date_val = result.get('date_prelevement', '')
                if isinstance(date_val, datetime):
                    date_val = date_val.strftime('%d/%m/%Y')
                
                self.history_table.setItem(row, 0, QTableWidgetItem(str(date_val)))
                self.history_table.setItem(row, 1, QTableWidgetItem(result.get('examen_nom', '')))
                self.history_table.setItem(row, 2, QTableWidgetItem(str(result.get('valeur', ''))))
                self.history_table.setItem(row, 3, QTableWidgetItem(result.get('unite', '')))
                
                statut = result.get('statut', '')
                status_item = QTableWidgetItem(statut)
                if statut == 'Validé':
                    status_item.setForeground(Qt.GlobalColor.green)
                self.history_table.setItem(row, 4, status_item)
                
                self.history_table.setItem(row, 5, QTableWidgetItem(result.get('validateur', '')))
                
                total_results += 1
            
            self.total_results_label.setText(f"Total résultats: {total_results}")
            
        except Exception as e:
            logger.error(f"Erreur chargement historique: {e}")
            
    def new_patient(self):
        """Créer un nouveau patient"""
        self.clear_form()
        self.current_patient = None
        self.status_bar.showMessage("Nouveau patient - Veuillez remplir les informations")
        
    def clear_form(self):
        """Vider le formulaire"""
        self.nom_input.clear()
        self.prenom_input.clear()
        self.date_naissance_input.setDate(QDate.currentDate())
        self.sexe_combo.setCurrentIndex(0)
        self.nir_input.clear()
        self.telephone_input.clear()
        self.email_input.clear()
        self.adresse_input.clear()
        self.mutuelle_input.clear()
        self.history_table.setRowCount(0)
        self.total_results_label.setText("Total résultats: 0")
        
    def search_patient(self):
        """Recherche avancée"""
        self.search_input.setFocus()
        
    def import_prescriptions(self):
        """Importer des prescriptions depuis un SI hospitalier"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importer prescriptions", "", 
            "Fichiers HL7 (*.hl7);;XML (*.xml);;CSV (*.csv)"
        )
        
        if file_path:
            try:
                count = self.patient_service.import_prescriptions(file_path)
                QMessageBox.information(
                    self, "Import réussi", 
                    f"{count} prescription(s) importée(s)"
                )
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de l'import: {e}")
                
    def export_patients(self):
        """Exporter la liste des patients"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter les patients", "", 
            "Fichiers CSV (*.csv);;Excel (*.xlsx)"
        )
        
        if file_path:
            try:
                self.patient_service.export_patients(file_path)
                QMessageBox.information(self, "Export", f"Patients exportés vers {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de l'export: {e}")
                
    def save_patient(self):
        """Enregistrer les informations du patient"""
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, "Champ requis", "Le nom est obligatoire")
            return
            
        patient_data = {
            'nom': self.nom_input.text().strip(),
            'prenom': self.prenom_input.text().strip(),
            'date_naissance': self.date_naissance_input.date().toString('yyyy-MM-dd'),
            'sexe': 'M' if self.sexe_combo.currentText() == "Masculin" else 'F',
            'nir': self.nir_input.text().strip(),
            'telephone': self.telephone_input.text().strip(),
            'email': self.email_input.text().strip(),
            'adresse': self.adresse_input.toPlainText().strip(),
            'mutuelle': self.mutuelle_input.text().strip()
        }
        
        try:
            if self.current_patient:
                patient_data['id'] = self.current_patient.get('id')
                updated = self.patient_service.update_patient(patient_data)
                QMessageBox.information(self, "Succès", "Patient mis à jour avec succès")
            else:
                created = self.patient_service.create_patient(patient_data)
                self.current_patient = created
                QMessageBox.information(self, "Succès", "Nouveau patient créé avec succès")
                self.patient_created.emit(created)
            
            self.load_patients()
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde patient: {e}")
            QMessageBox.critical(self, "Erreur", f"Échec de la sauvegarde: {e}")
            
    def delete_patient(self):
        """Supprimer un patient"""
        if not self.current_patient:
            QMessageBox.warning(self, "Attention", "Aucun patient sélectionné")
            return
            
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer le patient {self.current_patient.get('nom')} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.patient_service.delete_patient(self.current_patient.get('id'))
                QMessageBox.information(self, "Succès", "Patient supprimé")
                self.clear_form()
                self.load_patients()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de la suppression: {e}")
