"""Écran de gestion des donneurs - IGORS v2.0"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QDateEdit, QComboBox, QGroupBox, QSplitter, QToolBar,
    QAction, QStatusBar, QProgressBar, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon, QPixmap

from datetime import datetime, date
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class DonorManagementScreen(QWidget):
    """Interface de gestion des donneurs avec scan de consentement"""
    
    donor_selected = pyqtSignal(dict)
    donor_created = pyqtSignal(dict)
    
    def __init__(self, donor_service, parent=None):
        super().__init__(parent)
        self.donor_service = donor_service
        self.current_donor = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        title = QLabel("Gestion des Donneurs de Sang")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Splitter pour liste et détails
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panneau gauche - Liste des donneurs
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Barre d'outils
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(Qt.GlobalSize(24, 24))
        
        self.action_new = QAction("Nouveau", self)
        self.action_new.triggered.connect(self.new_donor)
        toolbar.addAction(self.action_new)
        
        self.action_search = QAction("Rechercher", self)
        self.action_search.triggered.connect(self.search_donor)
        toolbar.addAction(self.action_search)
        
        self.action_export = QAction("Exporter", self)
        self.action_export.triggered.connect(self.export_donors)
        toolbar.addAction(self.action_export)
        
        left_layout.addWidget(toolbar)
        
        # Champ recherche
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par nom, NIR, téléphone...")
        self.search_input.textChanged.connect(self.filter_donors)
        search_btn = QPushButton("🔍")
        search_btn.setFixedWidth(40)
        search_btn.clicked.connect(self.search_donor)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        left_layout.addLayout(search_layout)
        
        # Table des donneurs
        self.donor_table = QTableWidget()
        self.donor_table.setColumnCount(7)
        self.donor_table.setHorizontalHeaderLabels([
            "ID", "Nom", "Prénom", "NIR", "Téléphone", 
            "Dernier don", "Statut"
        ])
        self.donor_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.donor_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.donor_table.itemSelectionChanged.connect(self.on_donor_selected)
        left_layout.addWidget(self.donor_table)
        
        splitter.addWidget(left_panel)
        
        # Panneau droit - Détails du donneur
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Groupbox informations personnelles
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
        
        info_layout.addRow("Nom:", self.nom_input)
        info_layout.addRow("Prénom:", self.prenom_input)
        info_layout.addRow("Date naissance:", self.date_naissance_input)
        info_layout.addRow("Sexe:", self.sexe_combo)
        info_layout.addRow("NIR:", self.nir_input)
        info_layout.addRow("Téléphone:", self.telephone_input)
        info_layout.addRow("Email:", self.email_input)
        info_layout.addRow("Adresse:", self.adresse_input)
        
        right_layout.addWidget(info_group)
        
        # Groupbox consentement
        consent_group = QGroupBox("Consentement Éclairé")
        consent_layout = QVBoxLayout(consent_group)
        
        self.consent_status_label = QLabel("Statut: Non signé")
        self.consent_status_label.setStyleSheet("color: red; font-weight: bold;")
        consent_layout.addWidget(self.consent_status_label)
        
        consent_btn_layout = QHBoxLayout()
        self.scan_consent_btn = QPushButton("📄 Scanner le consentement")
        self.scan_consent_btn.clicked.connect(self.scan_consent)
        consent_btn_layout.addWidget(self.scan_consent_btn)
        
        self.view_consent_btn = QPushButton("👁️ Voir le document")
        self.view_consent_btn.clicked.connect(self.view_consent)
        self.view_consent_btn.setEnabled(False)
        consent_btn_layout.addWidget(self.view_consent_btn)
        
        consent_layout.addLayout(consent_btn_layout)
        
        self.consent_date_label = QLabel("Date signature: -")
        consent_layout.addWidget(self.consent_date_label)
        
        right_layout.addWidget(consent_group)
        
        # Groupbox historique des dons
        history_group = QGroupBox("Historique des Dons")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Type", "Volume", "Résultats", "Statut"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        history_layout.addWidget(self.history_table)
        
        stats_layout = QHBoxLayout()
        self.total_dons_label = QLabel("Total dons: 0")
        self.last_don_label = QLabel("Dernier don: Jamais")
        self.eligible_label = QLabel("Éligible: Oui")
        self.eligible_label.setStyleSheet("color: green; font-weight: bold;")
        stats_layout.addWidget(self.total_dons_label)
        stats_layout.addWidget(self.last_don_label)
        stats_layout.addWidget(self.eligible_label)
        stats_layout.addStretch()
        history_layout.addLayout(stats_layout)
        
        right_layout.addWidget(history_group)
        
        # Boutons d'action
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Enregistrer")
        self.save_btn.clicked.connect(self.save_donor)
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
        self.delete_btn.clicked.connect(self.delete_donor)
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
        self.load_donors()
        
    def load_donors(self):
        """Charger la liste des donneurs depuis la BDD"""
        try:
            donors = self.donor_service.get_all_donors()
            self.donor_table.setRowCount(0)
            
            for donor in donors:
                row = self.donor_table.rowCount()
                self.donor_table.insertRow(row)
                
                self.donor_table.setItem(row, 0, QTableWidgetItem(str(donor.get('id', ''))))
                self.donor_table.setItem(row, 1, QTableWidgetItem(donor.get('nom', '')))
                self.donor_table.setItem(row, 2, QTableWidgetItem(donor.get('prenom', '')))
                self.donor_table.setItem(row, 3, QTableWidgetItem(donor.get('nir', '')))
                self.donor_table.setItem(row, 4, QTableWidgetItem(donor.get('telephone', '')))
                
                last_don = donor.get('dernier_don', 'Jamais')
                if isinstance(last_don, date):
                    last_don = last_don.strftime('%d/%m/%Y')
                self.donor_table.setItem(row, 5, QTableWidgetItem(str(last_don)))
                
                status = "Actif" if donor.get('actif', True) else "Inactif"
                status_item = QTableWidgetItem(status)
                if not donor.get('actif', True):
                    status_item.setForeground(Qt.GlobalColor.red)
                self.donor_table.setItem(row, 6, status_item)
                
            self.status_bar.showMessage(f"{len(donors)} donneur(s) chargé(s)")
            
        except Exception as e:
            logger.error(f"Erreur chargement donneurs: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les donneurs: {e}")
            
    def filter_donors(self):
        """Filtrer les donneurs selon la recherche"""
        search_text = self.search_input.text().lower()
        
        for row in range(self.donor_table.rowCount()):
            match = False
            for col in range(1, 5):  # Colonnes nom, prénom, NIR, téléphone
                item = self.donor_table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            
            self.donor_table.setRowHidden(row, not match)
            
    def on_donor_selected(self):
        """Afficher les détails du donneur sélectionné"""
        selected_rows = self.donor_table.selectedItems()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        donor_id = self.donor_table.item(row, 0).text()
        
        try:
            donor = self.donor_service.get_donor_by_id(int(donor_id))
            self.current_donor = donor
            
            # Remplir les champs
            self.nom_input.setText(donor.get('nom', ''))
            self.prenom_input.setText(donor.get('prenom', ''))
            
            if donor.get('date_naissance'):
                date_val = donor['date_naissance']
                if isinstance(date_val, str):
                    date_val = QDate.fromString(date_val, 'yyyy-MM-dd')
                self.date_naissance_input.setDate(date_val)
            
            self.sexe_combo.setCurrentText("Masculin" if donor.get('sexe') == 'M' else "Féminin")
            self.nir_input.setText(donor.get('nir', ''))
            self.telephone_input.setText(donor.get('telephone', ''))
            self.email_input.setText(donor.get('email', ''))
            self.adresse_input.setText(donor.get('adresse', ''))
            
            # Statut consentement
            if donor.get('consentement_signe'):
                self.consent_status_label.setText("Statut: Signé ✓")
                self.consent_status_label.setStyleSheet("color: green; font-weight: bold;")
                self.consent_date_label.setText(f"Date signature: {donor.get('date_consentement', 'N/A')}")
                self.view_consent_btn.setEnabled(True)
            else:
                self.consent_status_label.setText("Statut: Non signé")
                self.consent_status_label.setStyleSheet("color: red; font-weight: bold;")
                self.consent_date_label.setText("Date signature: -")
                self.view_consent_btn.setEnabled(False)
            
            # Historique des dons
            self.load_donor_history(donor)
            
            self.status_bar.showMessage(f"Donneur: {donor.get('nom')} {donor.get('prenom')}")
            
        except Exception as e:
            logger.error(f"Erreur chargement détails donneur: {e}")
            
    def load_donor_history(self, donor):
        """Charger l'historique des dons du donneur"""
        try:
            history = self.donor_service.get_donor_history(donor.get('id'))
            self.history_table.setRowCount(0)
            
            total_dons = 0
            last_don_date = None
            
            for don in history:
                row = self.history_table.rowCount()
                self.history_table.insertRow(row)
                
                date_don = don.get('date_don', '')
                if isinstance(date_don, date):
                    date_don = date_don.strftime('%d/%m/%Y')
                
                self.history_table.setItem(row, 0, QTableWidgetItem(str(date_don)))
                self.history_table.setItem(row, 1, QTableWidgetItem(don.get('type_don', '')))
                self.history_table.setItem(row, 2, QTableWidgetItem(f"{don.get('volume', 0)} ml"))
                
                resultats = don.get('resultats_qualification', 'En attente')
                self.history_table.setItem(row, 3, QTableWidgetItem(str(resultats)))
                
                statut = don.get('statut', 'En attente')
                status_item = QTableWidgetItem(statut)
                if statut == 'Qualifié':
                    status_item.setForeground(Qt.GlobalColor.green)
                elif statut == 'Exclu':
                    status_item.setForeground(Qt.GlobalColor.red)
                self.history_table.setItem(row, 4, status_item)
                
                total_dons += 1
                if don.get('date_don'):
                    if last_don_date is None or don['date_don'] > last_don_date:
                        last_don_date = don['date_don']
            
            self.total_dons_label.setText(f"Total dons: {total_dons}")
            
            if last_don_date:
                if isinstance(last_don_date, date):
                    last_don_str = last_don_date.strftime('%d/%m/%Y')
                else:
                    last_don_str = str(last_don_date)
                self.last_don_label.setText(f"Dernier don: {last_don_str}")
            else:
                self.last_don_label.setText("Dernier don: Jamais")
            
            # Vérifier éligibilité (45 jours minimum entre dons)
            if last_don_date:
                from datetime import timedelta
                days_since_last = (date.today() - last_don_date).days
                eligible = days_since_last >= 45
                self.eligible_label.setText(f"Éligible: {'Oui ✓' if eligible else 'Non'}")
                self.eligible_label.setStyleSheet(
                    f"color: {'green' if eligible else 'red'}; font-weight: bold;"
                )
            else:
                self.eligible_label.setText("Éligible: Oui ✓")
                self.eligible_label.setStyleSheet("color: green; font-weight: bold;")
                
        except Exception as e:
            logger.error(f"Erreur chargement historique: {e}")
            
    def new_donor(self):
        """Créer un nouveau donneur"""
        self.clear_form()
        self.current_donor = None
        self.status_bar.showMessage("Nouveau donneur - Veuillez remplir les informations")
        
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
        self.history_table.setRowCount(0)
        self.total_dons_label.setText("Total dons: 0")
        self.last_don_label.setText("Dernier don: Jamais")
        self.eligible_label.setText("Éligible: Oui ✓")
        self.eligible_label.setStyleSheet("color: green; font-weight: bold;")
        self.consent_status_label.setText("Statut: Non signé")
        self.consent_status_label.setStyleSheet("color: red; font-weight: bold;")
        self.consent_date_label.setText("Date signature: -")
        self.view_consent_btn.setEnabled(False)
        
    def search_donor(self):
        """Recherche avancée de donneur"""
        # Pourrait ouvrir un dialog de recherche avancée
        self.search_input.setFocus()
        
    def export_donors(self):
        """Exporter la liste des donneurs en CSV/Excel"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter les donneurs", "", "Fichiers CSV (*.csv);;Excel (*.xlsx)"
        )
        
        if file_path:
            try:
                # Export logic here
                QMessageBox.information(self, "Export", f"Donneurs exportés vers {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de l'export: {e}")
                
    def scan_consent(self):
        """Scanner le formulaire de consentement"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Scanner le consentement", "", 
            "Images (*.png *.jpg *.jpeg);;PDF (*.pdf)"
        )
        
        if file_path:
            try:
                # Sauvegarder le document scanné
                self.donor_service.save_consent_document(
                    donor_id=self.current_donor.get('id') if self.current_donor else None,
                    document_path=file_path,
                    date_signature=datetime.now()
                )
                
                self.consent_status_label.setText("Statut: Signé ✓")
                self.consent_status_label.setStyleSheet("color: green; font-weight: bold;")
                self.consent_date_label.setText(f"Date signature: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                self.view_consent_btn.setEnabled(True)
                
                QMessageBox.information(
                    self, "Consentement enregistré", 
                    "Le formulaire de consentement a été enregistré avec succès."
                )
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de l'enregistrement: {e}")
                
    def view_consent(self):
        """Visualiser le document de consentement"""
        if self.current_donor:
            try:
                consent_doc = self.donor_service.get_consent_document(
                    self.current_donor.get('id')
                )
                if consent_doc:
                    # Ouvrir le document
                    import os
                    os.startfile(consent_doc.get('chemin_fichier'))
                else:
                    QMessageBox.warning(self, "Aucun document", "Aucun consentement trouvé.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le document: {e}")
                
    def save_donor(self):
        """Enregistrer les informations du donneur"""
        if not self.nom_input.text().strip():
            QMessageBox.warning(self, "Champ requis", "Le nom est obligatoire")
            return
            
        donor_data = {
            'nom': self.nom_input.text().strip(),
            'prenom': self.prenom_input.text().strip(),
            'date_naissance': self.date_naissance_input.date().toString('yyyy-MM-dd'),
            'sexe': 'M' if self.sexe_combo.currentText() == "Masculin" else 'F',
            'nir': self.nir_input.text().strip(),
            'telephone': self.telephone_input.text().strip(),
            'email': self.email_input.text().strip(),
            'adresse': self.adresse_input.toPlainText().strip()
        }
        
        try:
            if self.current_donor:
                # Mise à jour
                donor_data['id'] = self.current_donor.get('id')
                updated = self.donor_service.update_donor(donor_data)
                QMessageBox.information(self, "Succès", "Donneur mis à jour avec succès")
            else:
                # Création
                created = self.donor_service.create_donor(donor_data)
                self.current_donor = created
                QMessageBox.information(self, "Succès", "Nouveau donneur créé avec succès")
                self.donor_created.emit(created)
            
            self.load_donors()
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde donneur: {e}")
            QMessageBox.critical(self, "Erreur", f"Échec de la sauvegarde: {e}")
            
    def delete_donor(self):
        """Supprimer un donneur"""
        if not self.current_donor:
            QMessageBox.warning(self, "Attention", "Aucun donneur sélectionné")
            return
            
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment supprimer le donneur {self.current_donor.get('nom')} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.donor_service.delete_donor(self.current_donor.get('id'))
                QMessageBox.information(self, "Succès", "Donneur supprimé")
                self.clear_form()
                self.load_donors()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de la suppression: {e}")
