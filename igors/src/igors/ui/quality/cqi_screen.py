"""Écran de contrôle qualité - IGORS v2.0"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QTabWidget,
    QComboBox, QDateEdit, QLineEdit, QTextEdit, QCheckBox,
    QFileDialog, QProgressBar, QStatusBar, QSplitter,
    QDialog, QDialogButtonBox, QFrame, QSpinBox, QDateTimeEdit
)
from PyQt6.QtCore import Qt, QDate, QDateTime, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class CQIScreen(QWidget):
    """Contrôle Qualité Interne - Règles de Westgard"""
    
    cqi_validated = pyqtSignal(dict)
    
    def __init__(self, qualite_service, parent=None):
        super().__init__(parent)
        self.qualite_service = qualite_service
        self.current_cqi = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        title = QLabel("Contrôle Qualité Interne (CQI)")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panneau gauche - Liste des CQI
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Filtres
        filter_group = QGroupBox("Filtres")
        filter_layout = QHBoxLayout(filter_group)
        
        self.filter_automate_combo = QComboBox()
        self.filter_automate_combo.addItem("Tous les automates")
        filter_layout.addWidget(QLabel("Automate:"))
        filter_layout.addWidget(self.filter_automate_combo)
        
        self.filter_date_input = QDateEdit()
        self.filter_date_input.setDate(QDate.currentDate())
        self.filter_date_input.setCalendarPopup(True)
        filter_layout.addWidget(QLabel("Date:"))
        filter_layout.addWidget(self.filter_date_input)
        
        self.filter_btn = QPushButton("🔍 Filtrer")
        self.filter_btn.clicked.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_btn)
        
        filter_layout.addStretch()
        left_layout.addWidget(filter_group)
        
        # Stats
        stats_layout = QHBoxLayout()
        self.conforme_label = QLabel("Conformes: 0")
        self.conforme_label.setStyleSheet("font-weight: bold; color: green;")
        stats_layout.addWidget(self.conforme_label)
        
        self.non_conforme_label = QLabel("Non conformes: 0")
        self.non_conforme_label.setStyleSheet("font-weight: bold; color: red;")
        stats_layout.addWidget(self.non_conforme_label)
        
        self.en_attente_label = QLabel("En attente: 0")
        stats_layout.addWidget(self.en_attente_label)
        
        stats_layout.addStretch()
        left_layout.addLayout(stats_layout)
        
        # Table CQI
        self.cqi_table = QTableWidget()
        self.cqi_table.setColumnCount(7)
        self.cqi_table.setHorizontalHeaderLabels([
            "ID", "Automate", "Examen", "Niveau", "Résultat", 
            "Statut Westgard", "Date"
        ])
        self.cqi_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.cqi_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.cqi_table.itemSelectionChanged.connect(self.on_cqi_selected)
        left_layout.addWidget(self.cqi_table)
        
        splitter.addWidget(left_panel)
        
        # Panneau droit - Détails
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabs
        tabs = QTabWidget()
        
        # Tab 1: Saisie CQI
        saisie_tab = QWidget()
        saisie_layout = QVBoxLayout(saisie_tab)
        
        # Sélection automate/examen
        select_group = QGroupBox("Paramètres du CQI")
        select_layout = QFormLayout(select_group)
        
        self.saisie_automate_combo = QComboBox()
        select_layout.addRow("Automate:", self.saisie_automate_combo)
        
        self.saisie_examen_combo = QComboBox()
        select_layout.addRow("Examen:", self.saisie_examen_combo)
        
        self.saisie_niveau_combo = QComboBox()
        self.saisie_niveau_combo.addItems(["Niveau 1 (Bas)", "Niveau 2 (Normal)", "Niveau 3 (Haut)"])
        select_layout.addRow("Niveau:", self.saisie_niveau_combo)
        
        self.saisie_lot_input = QLineEdit()
        self.saisie_lot_input.setPlaceholderText("Numéro de lot")
        select_layout.addRow("Lot réactif:", self.saisie_lot_input)
        
        saisie_layout.addWidget(select_group)
        
        # Résultats
        result_group = QGroupBox("Résultats du CQI")
        result_layout = QFormLayout(result_group)
        
        self.resultat_value_input = QLineEdit()
        self.resultat_value_input.setFont(QFont("Courier", 14, QFont.Weight.Bold))
        self.resultat_value_input.setPlaceholderText("Valeur mesurée")
        result_layout.addRow("Valeur:", self.resultat_value_input)
        
        self.resultat_unite_label = QLabel("-")
        result_layout.addRow("Unité:", self.resultat_unite_label)
        
        self.cible_label = QLabel("Cible: -")
        result_layout.addRow(self.cible_label)
        
        self.ecart_type_label = QLabel("ET: -")
        result_layout.addRow(self.ecart_type_label)
        
        saisie_layout.addWidget(result_group)
        
        # Boutons
        btn_layout = QHBoxLayout()
        self.enregistrer_cqi_btn = QPushButton("💾 Enregistrer CQI")
        self.enregistrer_cqi_btn.clicked.connect(self.enregistrer_cqi)
        btn_layout.addWidget(self.enregistrer_cqi_btn)
        
        self.calculer_btn = QPushButton("📊 Calculer règles")
        self.calculer_btn.clicked.connect(self.calculer_westgard)
        btn_layout.addWidget(self.calculer_btn)
        
        btn_layout.addStretch()
        saisie_layout.addLayout(btn_layout)
        
        tabs.addTab(saisie_tab, "📝 Saisie CQI")
        
        # Tab 2: Règles Westgard
        westgard_tab = QWidget()
        westgard_layout = QVBoxLayout(westgard_tab)
        
        self.westgard_status_label = QLabel("Statut global:")
        self.westgard_status_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        westgard_layout.addWidget(self.westgard_status_label)
        
        self.westgard_table = QTableWidget()
        self.westgard_table.setColumnCount(4)
        self.westgard_table.setHorizontalHeaderLabels([
            "Règle", "Description", "Statut", "Détails"
        ])
        self.westgard_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        westgard_layout.addWidget(self.westgard_table)
        
        self.westgard_commentaire_edit = QTextEdit()
        self.westgard_commentaire_edit.setPlaceholderText("Commentaire sur les règles Westgard...")
        self.westgard_commentaire_edit.setMaximumHeight(80)
        westgard_layout.addWidget(self.westgard_commentaire_edit)
        
        tabs.addTab(westgard_tab, "📏 Règles Westgard")
        
        # Tab 3: Graphiques Levey-Jennings
        lj_tab = QWidget()
        lj_layout = QVBoxLayout(lj_tab)
        
        self.lj_info_label = QLabel("Graphique de Levey-Jennings")
        self.lj_info_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lj_layout.addWidget(self.lj_info_label)
        
        # Placeholder graphique
        self.graph_frame = QFrame()
        self.graph_frame.setMinimumHeight(300)
        self.graph_frame.setStyleSheet("background-color: #ecf0f1; border-radius: 5px;")
        graph_label = QLabel("📈 Graphique Levey-Jennings (à implémenter avec matplotlib)")
        graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        graph_layout = QVBoxLayout(self.graph_frame)
        graph_layout.addWidget(graph_label)
        lj_layout.addWidget(self.graph_frame)
        
        tabs.addTab(lj_tab, "📊 Levey-Jennings")
        
        right_layout.addWidget(tabs)
        
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Prêt - Contrôle Qualité Interne")
        layout.addWidget(self.status_bar)
        
        # Charger les données
        self.load_cqi_list()
        self.load_automates()
        self.load_examens()
        
    def load_cqi_list(self):
        """Charger la liste des CQI"""
        try:
            cqi_list = self.qualite_service.get_cqi_list()
            self.cqi_table.setRowCount(0)
            
            conforme_count = 0
            non_conforme_count = 0
            en_attente_count = 0
            
            for cqi in cqi_list:
                row = self.cqi_table.rowCount()
                self.cqi_table.insertRow(row)
                
                self.cqi_table.setItem(row, 0, QTableWidgetItem(str(cqi.get('id', ''))))
                self.cqi_table.setItem(row, 1, QTableWidgetItem(cqi.get('automate_nom', '')))
                self.cqi_table.setItem(row, 2, QTableWidgetItem(cqi.get('examen_nom', '')))
                self.cqi_table.setItem(row, 3, QTableWidgetItem(cqi.get('niveau', '')))
                self.cqi_table.setItem(row, 4, QTableWidgetItem(str(cqi.get('resultat', ''))))
                
                statut_westgard = cqi.get('statut_westgard', 'En attente')
                status_item = QTableWidgetItem(statut_westgard)
                if statut_westgard == 'Conforme':
                    status_item.setForeground(QColor('green'))
                    conforme_count += 1
                elif statut_westgard == 'Non conforme':
                    status_item.setForeground(QColor('red'))
                    non_conforme_count += 1
                else:
                    en_attente_count += 1
                self.cqi_table.setItem(row, 5, status_item)
                
                date_val = cqi.get('date', '')
                if isinstance(date_val, datetime):
                    date_val = date_val.strftime('%d/%m/%Y %H:%M')
                self.cqi_table.setItem(row, 6, QTableWidgetItem(str(date_val)))
            
            self.conforme_label.setText(f"Conformes: {conforme_count}")
            self.non_conforme_label.setText(f"Non conformes: {non_conforme_count}")
            self.en_attente_label.setText(f"En attente: {en_attente_count}")
            
            self.status_bar.showMessage(f"{len(cqi_list)} CQI chargé(s)")
            
        except Exception as e:
            logger.error(f"Erreur chargement CQI: {e}")
            
    def load_automates(self):
        """Charger la liste des automates"""
        try:
            automates = self.qualite_service.get_automates_list()
            self.filter_automate_combo.clear()
            self.filter_automate_combo.addItem("Tous les automates")
            self.saisie_automate_combo.clear()
            
            for auto in automates:
                nom = auto.get('nom', '')
                self.filter_automate_combo.addItem(nom)
                self.saisie_automate_combo.addItem(nom)
                
        except Exception as e:
            logger.error(f"Erreur chargement automates: {e}")
            
    def load_examens(self):
        """Charger la liste des examens"""
        try:
            examens = self.qualite_service.get_examens_list()
            self.saisie_examen_combo.clear()
            
            for exam in examens:
                nom = exam.get('nom', '')
                code_loinc = exam.get('code_loinc', '')
                self.saisie_examen_combo.addItem(f"{nom} ({code_loinc})")
                
        except Exception as e:
            logger.error(f"Erreur chargement examens: {e}")
            
    def apply_filters(self):
        """Appliquer les filtres"""
        self.load_cqi_list()
        self.status_bar.showMessage("Filtres appliqués")
        
    def on_cqi_selected(self):
        """Afficher les détails du CQI sélectionné"""
        selected_rows = self.cqi_table.selectedItems()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        cqi_id = self.cqi_table.item(row, 0).text()
        
        try:
            self.current_cqi = self.qualite_service.get_cqi_by_id(int(cqi_id))
            self.display_cqi_details()
            
        except Exception as e:
            logger.error(f"Erreur chargement détails CQI: {e}")
            
    def display_cqi_details(self):
        """Afficher les détails du CQI"""
        if not self.current_cqi:
            return
            
        # Remplir les champs de saisie
        self.saisie_automate_combo.setCurrentText(self.current_cqi.get('automate_nom', ''))
        self.saisie_examen_combo.setCurrentText(self.current_cqi.get('examen_nom', ''))
        self.saisie_niveau_combo.setCurrentText(self.current_cqi.get('niveau', ''))
        self.saisie_lot_input.setText(self.current_cqi.get('lot_reactif', ''))
        self.resultat_value_input.setText(str(self.current_cqi.get('resultat', '')))
        
        # Calculer et afficher les règles Westgard
        self.calculer_westgard()
        
    def enregistrer_cqi(self):
        """Enregistrer un nouveau CQI"""
        try:
            cqi_data = {
                'automate_id': self.saisie_automate_combo.currentIndex(),
                'examen_id': self.saisie_examen_combo.currentIndex(),
                'niveau': self.saisie_niveau_combo.currentText(),
                'lot_reactif': self.saisie_lot_input.text(),
                'resultat': float(self.resultat_value_input.text()),
                'date': datetime.now()
            }
            
            created = self.qualite_service.create_cqi(cqi_data)
            QMessageBox.information(self, "Succès", "CQI enregistré avec succès")
            
            self.load_cqi_list()
            self.status_bar.showMessage("CQI enregistré")
            
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Veuillez saisir une valeur numérique valide")
        except Exception as e:
            logger.error(f"Erreur enregistrement CQI: {e}")
            QMessageBox.critical(self, "Erreur", f"Échec de l'enregistrement: {e}")
            
    def calculer_westgard(self):
        """Calculer les règles de Westgard"""
        if not self.current_cqi and not self.resultat_value_input.text():
            QMessageBox.warning(self, "Attention", "Aucun résultat à analyser")
            return
            
        try:
            resultat = float(self.resultat_value_input.text()) if self.resultat_value_input.text() else self.current_cqi.get('resultat')
            
            rules = self.qualite_service.calculate_westgard_rules(
                resultat=resultat,
                examen_id=self.saisie_examen_combo.currentIndex()
            )
            
            self.westgard_table.setRowCount(0)
            all_passed = True
            
            for rule in rules:
                row = self.westgard_table.rowCount()
                self.westgard_table.insertRow(row)
                
                self.westgard_table.setItem(row, 0, QTableWidgetItem(rule.get('nom', '')))
                self.westgard_table.setItem(row, 1, QTableWidgetItem(rule.get('description', '')))
                
                status = "✅ Pass" if rule.get('passed') else "❌ FAIL"
                status_item = QTableWidgetItem(status)
                if rule.get('passed'):
                    status_item.setForeground(QColor('green'))
                else:
                    status_item.setForeground(QColor('red'))
                    all_passed = False
                self.westgard_table.setItem(row, 2, status_item)
                
                self.westgard_table.setItem(row, 3, QTableWidgetItem(rule.get('details', '')))
            
            if all_passed:
                self.westgard_status_label.setText("Statut global: ✅ CONFORME")
                self.westgard_status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.westgard_status_label.setText("Statut global: ❌ NON CONFORME")
                self.westgard_status_label.setStyleSheet("color: red; font-weight: bold;")
                
            self.status_bar.showMessage("Règles Westgard calculées")
            
        except Exception as e:
            logger.error(f"Erreur calcul Westgard: {e}")
            QMessageBox.critical(self, "Erreur", f"Échec du calcul: {e}")


class EEQScreen(QWidget):
    """Évaluation Externe de la Qualité"""
    
    def __init__(self, qualite_service, parent=None):
        super().__init__(parent)
        self.qualite_service = qualite_service
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("Évaluation Externe de la Qualité (EEQ)")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        info_label = QLabel("Module de gestion des EEQ - Programmes d'accréditation")
        info_label.setFont(QFont("Arial", 12))
        layout.addWidget(info_label)
        
        # Placeholder pour futur développement
        placeholder = QFrame()
        placeholder.setMinimumHeight(300)
        placeholder.setStyleSheet("background-color: #ecf0f1; border-radius: 5px;")
        placeholder_label = QLabel("📋 Interface EEQ en cours de développement\n\n- Inscription aux programmes EEQ\n- Saisie des résultats EEQ\n- Analyse des performances\n- Certificats de participation")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_layout.addWidget(placeholder_label)
        layout.addWidget(placeholder)
        
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Module EEQ - Fonctionnalités à venir")
        layout.addWidget(self.status_bar)


class CAPAScreen(QWidget):
    """Gestion des Actions Correctives et Préventives (CAPA)"""
    
    capa_created = pyqtSignal(dict)
    
    def __init__(self, qualite_service, parent=None):
        super().__init__(parent)
        self.qualite_service = qualite_service
        self.current_capa = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("Gestion des Non-Conformités et CAPA")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panneau gauche - Liste CAPA
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Bouton nouvelle CAPA
        new_btn = QPushButton("➕ Nouvelle non-conformité")
        new_btn.clicked.connect(self.new_capa)
        new_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white;
                padding: 10px; border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        left_layout.addWidget(new_btn)
        
        # Table CAPA
        self.capa_table = QTableWidget()
        self.capa_table.setColumnCount(6)
        self.capa_table.setHorizontalHeaderLabels([
            "ID", "Type", "Description", "Priorité", "Statut", "Date"
        ])
        self.capa_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.capa_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.capa_table.itemSelectionChanged.connect(self.on_capa_selected)
        left_layout.addWidget(self.capa_table)
        
        splitter.addWidget(left_panel)
        
        # Panneau droit - Détails CAPA
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Formulaire
        form_group = QGroupBox("Détails de la Non-Conformité")
        form_layout = QFormLayout(form_group)
        
        self.capa_type_combo = QComboBox()
        self.capa_type_combo.addItems([
            "Non-conformité majeure",
            "Non-conformité mineure",
            "Action corrective",
            "Action préventive",
            "Amélioration continue"
        ])
        form_layout.addRow("Type:", self.capa_type_combo)
        
        self.capa_priorite_combo = QComboBox()
        self.capa_priorite_combo.addItems(["Faible", "Moyenne", "Élevée", "Critique"])
        form_layout.addRow("Priorité:", self.capa_priorite_combo)
        
        self.capa_statut_combo = QComboBox()
        self.capa_statut_combo.addItems([
            "Ouverte", "En cours", "En investigation", 
            "Planifiée", "Clôturée", "Annulée"
        ])
        form_layout.addRow("Statut:", self.capa_statut_combo)
        
        self.capa_description_edit = QTextEdit()
        self.capa_description_edit.setPlaceholderText("Description détaillée de la non-conformité...")
        self.capa_description_edit.setMaximumHeight(100)
        form_layout.addRow("Description:", self.capa_description_edit)
        
        self.capa_cause_edit = QTextEdit()
        self.capa_cause_edit.setPlaceholderText("Analyse des causes racines...")
        self.capa_cause_edit.setMaximumHeight(80)
        form_layout.addRow("Causes racines:", self.capa_cause_edit)
        
        self.capa_action_edit = QTextEdit()
        self.capa_action_edit.setPlaceholderText("Actions correctives/préventives proposées...")
        self.capa_action_edit.setMaximumHeight(80)
        form_layout.addRow("Actions proposées:", self.capa_action_edit)
        
        self.capa_echeance_input = QDateTimeEdit()
        self.capa_echeance_input.setDateTime(QDateTime.currentDateTime())
        self.capa_echeance_input.setCalendarPopup(True)
        form_layout.addRow("Échéance:", self.capa_echeance_input)
        
        self.capa_responsable_input = QLineEdit()
        self.capa_responsable_input.setPlaceholderText("Nom du responsable")
        form_layout.addRow("Responsable:", self.capa_responsable_input)
        
        right_layout.addWidget(form_group)
        
        # Boutons
        btn_layout = QHBoxLayout()
        self.save_capa_btn = QPushButton("💾 Enregistrer")
        self.save_capa_btn.clicked.connect(self.save_capa)
        btn_layout.addWidget(self.save_capa_btn)
        
        self.close_capa_btn = QPushButton("✅ Clôturer")
        self.close_capa_btn.clicked.connect(self.close_capa)
        btn_layout.addWidget(self.close_capa_btn)
        
        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)
        
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Gestion CAPA")
        layout.addWidget(self.status_bar)
        
        self.load_capa_list()
        
    def load_capa_list(self):
        """Charger la liste des CAPA"""
        try:
            capa_list = self.qualite_service.get_capa_list()
            self.capa_table.setRowCount(0)
            
            for capa in capa_list:
                row = self.capa_table.rowCount()
                self.capa_table.insertRow(row)
                
                self.capa_table.setItem(row, 0, QTableWidgetItem(str(capa.get('id', ''))))
                self.capa_table.setItem(row, 1, QTableWidgetItem(capa.get('type', '')))
                self.capa_table.setItem(row, 2, QTableWidgetItem(capa.get('description', '')[:50] + "..."))
                
                priorite = capa.get('priorite', 'Moyenne')
                prio_item = QTableWidgetItem(priorite)
                if priorite == 'Critique':
                    prio_item.setForeground(QColor('red'))
                elif priorite == 'Élevée':
                    prio_item.setForeground(QColor('orange'))
                self.capa_table.setItem(row, 3, prio_item)
                
                statut = capa.get('statut', 'Ouverte')
                status_item = QTableWidgetItem(statut)
                if statut == 'Clôturée':
                    status_item.setForeground(QColor('green'))
                elif statut == 'En cours':
                    status_item.setForeground(QColor('blue'))
                self.capa_table.setItem(row, 4, status_item)
                
                date_val = capa.get('date', '')
                if isinstance(date_val, datetime):
                    date_val = date_val.strftime('%d/%m/%Y')
                self.capa_table.setItem(row, 5, QTableWidgetItem(str(date_val)))
            
            self.status_bar.showMessage(f"{len(capa_list)} CAPA chargée(s)")
            
        except Exception as e:
            logger.error(f"Erreur chargement CAPA: {e}")
            
    def new_capa(self):
        """Créer une nouvelle CAPA"""
        self.capa_type_combo.setCurrentIndex(0)
        self.capa_priorite_combo.setCurrentIndex(1)
        self.capa_statut_combo.setCurrentIndex(0)
        self.capa_description_edit.clear()
        self.capa_cause_edit.clear()
        self.capa_action_edit.clear()
        self.capa_echeance_input.setDateTime(QDateTime.currentDateTime())
        self.capa_responsable_input.clear()
        self.current_capa = None
        self.status_bar.showMessage("Nouvelle non-conformité")
        
    def on_capa_selected(self):
        """Afficher les détails de la CAPA sélectionnée"""
        selected_rows = self.capa_table.selectedItems()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        capa_id = self.capa_table.item(row, 0).text()
        
        try:
            self.current_capa = self.qualite_service.get_capa_by_id(int(capa_id))
            
            self.capa_type_combo.setCurrentText(self.current_capa.get('type', ''))
            self.capa_priorite_combo.setCurrentText(self.current_capa.get('priorite', ''))
            self.capa_statut_combo.setCurrentText(self.current_capa.get('statut', ''))
            self.capa_description_edit.setText(self.current_capa.get('description', ''))
            self.capa_cause_edit.setText(self.current_capa.get('causes_racines', ''))
            self.capa_action_edit.setText(self.current_capa.get('actions_proposees', ''))
            self.capa_responsable_input.setText(self.current_capa.get('responsable', ''))
            
            if self.current_capa.get('echeance'):
                echeance = self.current_capa['echeance']
                if isinstance(echeance, datetime):
                    self.capa_echeance_input.setDateTime(QDateTime(echeance))
                    
            self.status_bar.showMessage(f"CAPA ID: {capa_id}")
            
        except Exception as e:
            logger.error(f"Erreur chargement CAPA: {e}")
            
    def save_capa(self):
        """Enregistrer une CAPA"""
        try:
            capa_data = {
                'type': self.capa_type_combo.currentText(),
                'priorite': self.capa_priorite_combo.currentText(),
                'statut': self.capa_statut_combo.currentText(),
                'description': self.capa_description_edit.toPlainText(),
                'causes_racines': self.capa_cause_edit.toPlainText(),
                'actions_proposees': self.capa_action_edit.toPlainText(),
                'responsable': self.capa_responsable_input.text(),
                'echeance': self.capa_echeance_input.dateTime().toPyDateTime()
            }
            
            if self.current_capa:
                capa_data['id'] = self.current_capa.get('id')
                updated = self.qualite_service.update_capa(capa_data)
                QMessageBox.information(self, "Succès", "CAPA mise à jour")
            else:
                created = self.qualite_service.create_capa(capa_data)
                self.current_capa = created
                QMessageBox.information(self, "Succès", "CAPA créée")
                self.capa_created.emit(created)
            
            self.load_capa_list()
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde CAPA: {e}")
            QMessageBox.critical(self, "Erreur", f"Échec de la sauvegarde: {e}")
            
    def close_capa(self):
        """Clôturer une CAPA"""
        if not self.current_capa:
            QMessageBox.warning(self, "Attention", "Aucune CAPA sélectionnée")
            return
            
        confirmation = QMessageBox.question(
            self, "Confirmation",
            "Confirmez-vous la clôture de cette CAPA ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirmation == QMessageBox.StandardButton.Yes:
            try:
                self.qualite_service.close_capa(self.current_capa.get('id'))
                QMessageBox.information(self, "Succès", "CAPA clôturée")
                self.load_capa_list()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de la clôture: {e}")


class QualiteManagementScreen(QWidget):
    """Écran principal de gestion de la qualité (onglets CQI/EEQ/CAPA)"""
    
    def __init__(self, qualite_service, parent=None):
        super().__init__(parent)
        self.qualite_service = qualite_service
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        
        self.cqi_screen = CQIScreen(qualite_service)
        self.eeq_screen = EEQScreen(qualite_service)
        self.capa_screen = CAPAScreen(qualite_service)
        
        self.tabs.addTab(self.cqi_screen, "📊 CQI")
        self.tabs.addTab(self.eeq_screen, "🏆 EEQ")
        self.tabs.addTab(self.capa_screen, "🔧 CAPA")
        
        layout.addWidget(self.tabs)
