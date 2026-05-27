"""Écran de validation biologique - IGORS v2.0"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox,
    QSplitter, QComboBox, QTextEdit, QDateEdit, QCheckBox,
    QTabWidget, QDialog, QDialogButtonBox, QFileDialog,
    QProgressBar, QStatusBar, QToolBar, QAction, QFrame
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QPen

from datetime import datetime, date
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class ValidationBiologiqueScreen(QWidget):
    """Interface de validation biologique avec règles de Westgard"""
    
    result_validated = pyqtSignal(dict)
    result_rejected = pyqtSignal(dict)
    
    def __init__(self, validation_service, parent=None):
        super().__init__(parent)
        self.validation_service = validation_service
        self.current_result = None
        self.pending_results = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        title = QLabel("Validation Biologique des Résultats")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panneau gauche - Résultats en attente
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Filtres
        filter_group = QGroupBox("Filtres")
        filter_layout = QHBoxLayout(filter_group)
        
        self.filter_exam_combo = QComboBox()
        self.filter_exam_combo.addItem("Tous les examens")
        filter_layout.addWidget(QLabel("Examen:"))
        filter_layout.addWidget(self.filter_exam_combo)
        
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
        
        # Stats rapides
        stats_layout = QHBoxLayout()
        self.pending_count_label = QLabel("En attente: 0")
        self.pending_count_label.setStyleSheet("font-weight: bold; color: orange;")
        stats_layout.addWidget(self.pending_count_label)
        
        self.validated_today_label = QLabel("Validés aujourd'hui: 0")
        self.validated_today_label.setStyleSheet("font-weight: bold; color: green;")
        stats_layout.addWidget(self.validated_today_label)
        
        self.rejected_today_label = QLabel("Rejetés aujourd'hui: 0")
        self.rejected_today_label.setStyleSheet("font-weight: bold; color: red;")
        stats_layout.addWidget(self.rejected_today_label)
        
        stats_layout.addStretch()
        left_layout.addLayout(stats_layout)
        
        # Table des résultats en attente
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "ID", "Patient", "Examen", "Résultat", "Unité", 
            "Drapeau", "Date", "Statut"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.results_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.results_table.itemSelectionChanged.connect(self.on_result_selected)
        left_layout.addWidget(self.results_table)
        
        splitter.addWidget(left_panel)
        
        # Panneau droit - Détails et validation
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabs pour différentes vues
        tabs = QTabWidget()
        
        # Tab 1: Détails du résultat
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        
        # Informations patient
        patient_group = QGroupBox("Informations Patient")
        patient_layout = QFormLayout(patient_group)
        
        self.patient_nom_label = QLabel("-")
        self.patient_prenom_label = QLabel("-")
        self.patient_ddn_label = QLabel("-")
        self.patient_sexe_label = QLabel("-")
        self.patient_nir_label = QLabel("-")
        
        patient_layout.addRow("Nom:", self.patient_nom_label)
        patient_layout.addRow("Prénom:", self.patient_prenom_label)
        patient_layout.addRow("Date naissance:", self.patient_ddn_label)
        patient_layout.addRow("Sexe:", self.patient_sexe_label)
        patient_layout.addRow("NIR:", self.patient_nir_label)
        
        details_layout.addWidget(patient_group)
        
        # Informations examen
        exam_group = QGroupBox("Informations Examen")
        exam_layout = QFormLayout(exam_group)
        
        self.exam_nom_label = QLabel("-")
        self.exam_code_loinc_label = QLabel("-")
        self.automate_label = QLabel("-")
        self.date_prelevement_label = QLabel("-")
        self.date_reception_label = QLabel("-")
        self.date_validation_label = QLabel("-")
        
        exam_layout.addRow("Examen:", self.exam_nom_label)
        exam_layout.addRow("Code LOINC:", self.exam_code_loinc_label)
        exam_layout.addRow("Automate:", self.automate_label)
        exam_layout.addRow("Date prélèvement:", self.date_prelevement_label)
        exam_layout.addRow("Date réception:", self.date_reception_label)
        exam_layout.addRow("Date validation:", self.date_validation_label)
        
        details_layout.addWidget(exam_group)
        
        # Résultat
        result_group = QGroupBox("Résultat de l'Analyse")
        result_layout = QFormLayout(result_group)
        
        self.result_value_input = QLineEdit()
        self.result_value_input.setFont(QFont("Courier", 14, QFont.Weight.Bold))
        self.result_unit_label = QLabel("-")
        self.result_flag_label = QLabel("-")
        self.result_flag_label.setStyleSheet("font-weight: bold;")
        
        result_layout.addRow("Valeur:", self.result_value_input)
        result_layout.addRow("Unité:", self.result_unit_label)
        result_layout.addRow("Drapeau:", self.result_flag_label)
        
        details_layout.addWidget(result_group)
        
        # Fourchettes de référence
        ref_group = QGroupBox("Fourchettes de Référence")
        ref_layout = QVBoxLayout(ref_group)
        
        self.ref_table = QTableWidget()
        self.ref_table.setColumnCount(4)
        self.ref_table.setHorizontalHeaderLabels([
            "Population", "Min", "Max", "Unité"
        ])
        self.ref_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        ref_layout.addWidget(self.ref_table)
        
        details_layout.addWidget(ref_group)
        
        tabs.addTab(details_tab, "📋 Détails")
        
        # Tab 2: Graphiques et tendances
        trends_tab = QWidget()
        trends_layout = QVBoxLayout(trends_tab)
        
        self.trend_info_label = QLabel("Historique des résultats pour ce patient:")
        self.trend_info_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        trends_layout.addWidget(self.trend_info_label)
        
        self.trend_table = QTableWidget()
        self.trend_table.setColumnCount(4)
        self.trend_table.setHorizontalHeaderLabels([
            "Date", "Résultat", "Unité", "Statut"
        ])
        self.trend_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        trends_layout.addWidget(self.trend_table)
        
        # Zone pour graphique (placeholder)
        self.graph_frame = QFrame()
        self.graph_frame.setMinimumHeight(200)
        self.graph_frame.setStyleSheet("background-color: #ecf0f1; border-radius: 5px;")
        graph_label = QLabel("📈 Graphique des tendances (à implémenter)")
        graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        graph_layout = QVBoxLayout(self.graph_frame)
        graph_layout.addWidget(graph_label)
        trends_layout.addWidget(self.graph_frame)
        
        tabs.addTab(trends_tab, "📊 Tendances")
        
        # Tab 3: Contrôle qualité
        qc_tab = QWidget()
        qc_layout = QVBoxLayout(qc_tab)
        
        self.qc_status_label = QLabel("Statut CQI:")
        self.qc_status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        qc_layout.addWidget(self.qc_status_label)
        
        self.westgard_rules_label = QLabel("Règles Westgard appliquées:")
        qc_layout.addWidget(self.westgard_rules_label)
        
        self.westgard_list = QTableWidget()
        self.westgard_list.setColumnCount(3)
        self.westgard_list.setHorizontalHeaderLabels([
            "Règle", "Statut", "Commentaire"
        ])
        self.westgard_list.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        qc_layout.addWidget(self.westgard_list)
        
        tabs.addTab(qc_tab, "✅ Contrôle Qualité")
        
        right_layout.addWidget(tabs)
        
        # Zone de commentaires
        comment_group = QGroupBox("Commentaires de Validation")
        comment_layout = QVBoxLayout(comment_group)
        
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText("Ajouter un commentaire optionnel...")
        self.comment_edit.setMaximumHeight(80)
        comment_layout.addWidget(self.comment_edit)
        
        self.critical_check = QCheckBox("⚠️ Résultat critique - Notification requise")
        self.critical_check.stateChanged.connect(self.on_critical_changed)
        comment_layout.addWidget(self.critical_check)
        
        right_layout.addWidget(comment_group)
        
        # Boutons d'action
        btn_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("✅ Valider")
        self.validate_btn.clicked.connect(self.validate_result)
        self.validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                padding: 10px 20px; border-radius: 5px;
                font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #2ecc71; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        btn_layout.addWidget(self.validate_btn)
        
        self.reject_btn = QPushButton("❌ Rejeter")
        self.reject_btn.clicked.connect(self.reject_result)
        self.reject_btn.setStyleSheet("""
            QPushButton {
                background-color: #c0392b; color: white;
                padding: 10px 20px; border-radius: 5px;
                font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #e74c3c; }
        """)
        btn_layout.addWidget(self.reject_btn)
        
        self.repeat_btn = QPushButton("🔄 Demander reprise")
        self.repeat_btn.clicked.connect(self.request_repeat)
        btn_layout.addWidget(self.repeat_btn)
        
        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)
        
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Prêt - En attente de résultats")
        layout.addWidget(self.status_bar)
        
        # Timer pour rafraîchissement automatique
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_pending_results)
        self.refresh_timer.start(30000)  # 30 secondes
        
        # Charger les résultats en attente
        self.load_pending_results()
        
    def load_pending_results(self):
        """Charger les résultats en attente de validation"""
        try:
            self.pending_results = self.validation_service.get_pending_results()
            self.results_table.setRowCount(0)
            
            pending_count = 0
            for result in self.pending_results:
                row = self.results_table.rowCount()
                self.results_table.insertRow(row)
                
                self.results_table.setItem(row, 0, QTableWidgetItem(str(result.get('id', ''))))
                self.results_table.setItem(row, 1, QTableWidgetItem(
                    f"{result.get('patient_nom', '')} {result.get('patient_prenom', '')}"
                ))
                self.results_table.setItem(row, 2, QTableWidgetItem(result.get('examen_nom', '')))
                
                value = result.get('valeur', '')
                value_item = QTableWidgetItem(str(value))
                value_item.setFont(QFont("Courier", 10, QFont.Weight.Bold))
                self.results_table.setItem(row, 3, value_item)
                
                self.results_table.setItem(row, 4, QTableWidgetItem(result.get('unite', '')))
                
                # Drapeau avec couleur
                flag = result.get('drapeau', '')
                flag_item = QTableWidgetItem(flag)
                if flag:
                    if 'H' in flag or 'HH' in flag:
                        flag_item.setForeground(QColor('red'))
                    elif 'L' in flag or 'LL' in flag:
                        flag_item.setForeground(QColor('orange'))
                self.results_table.setItem(row, 5, flag_item)
                
                date_val = result.get('date_reception', '')
                if isinstance(date_val, datetime):
                    date_val = date_val.strftime('%d/%m/%Y %H:%M')
                self.results_table.setItem(row, 6, QTableWidgetItem(str(date_val)))
                
                statut = result.get('statut', 'En attente')
                status_item = QTableWidgetItem(statut)
                if statut == 'En attente':
                    status_item.setForeground(QColor('orange'))
                    pending_count += 1
                self.results_table.setItem(row, 7, status_item)
            
            self.pending_count_label.setText(f"En attente: {pending_count}")
            self.status_bar.showMessage(f"{len(self.pending_results)} résultat(s) chargé(s)")
            
            # Mettre à jour les stats du jour
            self.update_daily_stats()
            
        except Exception as e:
            logger.error(f"Erreur chargement résultats: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les résultats: {e}")
            
    def update_daily_stats(self):
        """Mettre à jour les statistiques du jour"""
        try:
            today = date.today()
            stats = self.validation_service.get_daily_stats(today)
            
            self.validated_today_label.setText(f"Validés aujourd'hui: {stats.get('validated', 0)}")
            self.rejected_today_label.setText(f"Rejetés aujourd'hui: {stats.get('rejected', 0)}")
            
        except Exception as e:
            logger.error(f"Erreur stats: {e}")
            
    def apply_filters(self):
        """Appliquer les filtres de recherche"""
        exam_filter = self.filter_exam_combo.currentText()
        date_filter = self.filter_date_input.date().toPyDate()
        
        # Logique de filtrage à implémenter
        self.load_pending_results()
        self.status_bar.showMessage("Filtres appliqués")
        
    def on_result_selected(self):
        """Afficher les détails du résultat sélectionné"""
        selected_rows = self.results_table.selectedItems()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        result_id = self.results_table.item(row, 0).text()
        
        try:
            self.current_result = self.validation_service.get_result_by_id(int(result_id))
            self.display_result_details()
            self.status_bar.showMessage(f"Résultat ID: {result_id}")
            
        except Exception as e:
            logger.error(f"Erreur chargement détails: {e}")
            
    def display_result_details(self):
        """Afficher les détails complets du résultat"""
        if not self.current_result:
            return
            
        # Patient
        self.patient_nom_label.setText(self.current_result.get('patient_nom', '-'))
        self.patient_prenom_label.setText(self.current_result.get('patient_prenom', '-'))
        self.patient_ddn_label.setText(str(self.current_result.get('patient_ddn', '-')))
        self.patient_sexe_label.setText(self.current_result.get('patient_sexe', '-'))
        self.patient_nir_label.setText(self.current_result.get('patient_nir', '-'))
        
        # Examen
        self.exam_nom_label.setText(self.current_result.get('examen_nom', '-'))
        self.exam_code_loinc_label.setText(self.current_result.get('examen_code_loinc', '-'))
        self.automate_label.setText(self.current_result.get('automate_nom', '-'))
        
        date_prel = self.current_result.get('date_prelevement', '-')
        if isinstance(date_prel, datetime):
            date_prel = date_prel.strftime('%d/%m/%Y %H:%M')
        self.date_prelevement_label.setText(str(date_prel))
        
        date_rec = self.current_result.get('date_reception', '-')
        if isinstance(date_rec, datetime):
            date_rec = date_rec.strftime('%d/%m/%Y %H:%M')
        self.date_reception_label.setText(str(date_rec))
        
        # Résultat
        self.result_value_input.setText(str(self.current_result.get('valeur', '')))
        self.result_unit_label.setText(str(self.current_result.get('unite', '-')))
        
        flag = self.current_result.get('drapeau', '')
        self.result_flag_label.setText(flag if flag else 'Aucun')
        if flag:
            if 'H' in flag or 'HH' in flag:
                self.result_flag_label.setStyleSheet("font-weight: bold; color: red;")
            elif 'L' in flag or 'LL' in flag:
                self.result_flag_label.setStyleSheet("font-weight: bold; color: orange;")
            else:
                self.result_flag_label.setStyleSheet("font-weight: bold; color: black;")
        
        # Fourchettes de référence
        self.load_reference_ranges()
        
        # Tendances
        self.load_patient_trends()
        
        # Contrôle qualité
        self.load_qc_status()
        
        # Réinitialiser commentaire
        self.comment_edit.clear()
        self.critical_check.setChecked(False)
        
    def load_reference_ranges(self):
        """Charger les fourchettes de référence"""
        try:
            ranges = self.validation_service.get_reference_ranges(
                examen_id=self.current_result.get('examen_id'),
                sexe=self.current_result.get('patient_sexe'),
                age=self.current_result.get('patient_age')
            )
            
            self.ref_table.setRowCount(0)
            for r in ranges:
                row = self.ref_table.rowCount()
                self.ref_table.insertRow(row)
                self.ref_table.setItem(row, 0, QTableWidgetItem(r.get('population', 'Standard')))
                self.ref_table.setItem(row, 1, QTableWidgetItem(str(r.get('min', ''))))
                self.ref_table.setItem(row, 2, QTableWidgetItem(str(r.get('max', ''))))
                self.ref_table.setItem(row, 3, QTableWidgetItem(r.get('unite', '')))
                
        except Exception as e:
            logger.error(f"Erreur chargement références: {e}")
            
    def load_patient_trends(self):
        """Charger l'historique des résultats du patient"""
        try:
            history = self.validation_service.get_patient_history(
                patient_id=self.current_result.get('patient_id'),
                examen_id=self.current_result.get('examen_id')
            )
            
            self.trend_table.setRowCount(0)
            for h in history:
                row = self.trend_table.rowCount()
                self.trend_table.insertRow(row)
                
                date_val = h.get('date', '')
                if isinstance(date_val, datetime):
                    date_val = date_val.strftime('%d/%m/%Y')
                
                self.trend_table.setItem(row, 0, QTableWidgetItem(str(date_val)))
                self.trend_table.setItem(row, 1, QTableWidgetItem(str(h.get('valeur', ''))))
                self.trend_table.setItem(row, 2, QTableWidgetItem(h.get('unite', '')))
                
                statut = h.get('statut', '')
                status_item = QTableWidgetItem(statut)
                if statut == 'Validé':
                    status_item.setForeground(QColor('green'))
                self.trend_table.setItem(row, 3, status_item)
                
        except Exception as e:
            logger.error(f"Erreur chargement tendances: {e}")
            
    def load_qc_status(self):
        """Charger le statut du contrôle qualité"""
        try:
            qc_status = self.validation_service.get_qc_status(
                automate_id=self.current_result.get('automate_id'),
                date=self.current_result.get('date_reception')
            )
            
            if qc_status.get('valid'):
                self.qc_status_label.setText("Statut CQI: ✅ Conforme")
                self.qc_status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.qc_status_label.setText("Statut CQI: ⚠️ Non conforme")
                self.qc_status_label.setStyleSheet("color: red; font-weight: bold;")
            
            # Règles Westgard
            rules = qc_status.get('westgard_rules', [])
            self.westgard_rules_label.setText(f"Règles Westgard appliquées: {len(rules)}")
            
            self.westgard_list.setRowCount(0)
            for rule in rules:
                row = self.westgard_list.rowCount()
                self.westgard_list.insertRow(row)
                self.westgard_list.setItem(row, 0, QTableWidgetItem(rule.get('nom', '')))
                
                status = "Pass" if rule.get('passed') else "FAIL"
                status_item = QTableWidgetItem(status)
                if rule.get('passed'):
                    status_item.setForeground(QColor('green'))
                else:
                    status_item.setForeground(QColor('red'))
                self.westgard_list.setItem(row, 1, status_item)
                
                self.westgard_list.setItem(row, 2, QTableWidgetItem(rule.get('commentaire', '')))
                
        except Exception as e:
            logger.error(f"Erreur chargement QC: {e}")
            self.qc_status_label.setText("Statut CQI: ❓ Inconnu")
            
    def on_critical_changed(self, state):
        """Gestion du changement d'état critique"""
        if state == Qt.CheckState.Checked:
            self.status_bar.showMessage("⚠️ RÉSULTAT CRITIQUE - Notification requise")
        else:
            self.status_bar.showMessage("Résultat standard")
            
    def validate_result(self):
        """Valider le résultat"""
        if not self.current_result:
            QMessageBox.warning(self, "Attention", "Aucun résultat sélectionné")
            return
            
        # Vérifier le CQI
        if hasattr(self, 'qc_status_label'):
            if "Non conforme" in self.qc_status_label.text():
                reply = QMessageBox.question(
                    self, "Attention CQI",
                    "Le contrôle qualité est non conforme. Voulez-vous vraiment valider ?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
        
        confirmation = QMessageBox.question(
            self, "Confirmation",
            "Confirmez-vous la validation de ce résultat ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirmation == QMessageBox.StandardButton.Yes:
            try:
                validation_data = {
                    'result_id': self.current_result.get('id'),
                    'validateur_id': self.validation_service.current_user_id,
                    'commentaire': self.comment_edit.toPlainText(),
                    'critique': self.critical_check.isChecked(),
                    'date_validation': datetime.now()
                }
                
                validated = self.validation_service.validate_result(validation_data)
                
                QMessageBox.information(self, "Succès", "Résultat validé avec succès")
                self.result_validated.emit(validated)
                
                # Rafraîchir la liste
                self.load_pending_results()
                self.clear_details()
                
            except Exception as e:
                logger.error(f"Erreur validation: {e}")
                QMessageBox.critical(self, "Erreur", f"Échec de la validation: {e}")
                
    def reject_result(self):
        """Rejeter le résultat"""
        if not self.current_result:
            QMessageBox.warning(self, "Attention", "Aucun résultat sélectionné")
            return
            
        reason, ok = QInputDialog.getText(
            self, "Motif de rejet",
            "Veuillez saisir le motif de rejet:"
        )
        
        if ok and reason:
            try:
                rejection_data = {
                    'result_id': self.current_result.get('id'),
                    'motif': reason,
                    'rejecteur_id': self.validation_service.current_user_id,
                    'date_rejet': datetime.now()
                }
                
                rejected = self.validation_service.reject_result(rejection_data)
                
                QMessageBox.information(self, "Succès", "Résultat rejeté")
                self.result_rejected.emit(rejected)
                
                self.load_pending_results()
                self.clear_details()
                
            except Exception as e:
                logger.error(f"Erreur rejet: {e}")
                QMessageBox.critical(self, "Erreur", f"Échec du rejet: {e}")
                
    def request_repeat(self):
        """Demander une reprise du prélèvement"""
        if not self.current_result:
            QMessageBox.warning(self, "Attention", "Aucun résultat sélectionné")
            return
            
        QMessageBox.information(
            self, "Reprise demandée",
            "Une demande de reprise a été générée et transmise au service concerné."
        )
        
    def refresh_pending_results(self):
        """Rafraîchir automatiquement les résultats en attente"""
        self.load_pending_results()
        
    def clear_details(self):
        """Effacer les détails"""
        self.current_result = None
        self.patient_nom_label.setText("-")
        self.patient_prenom_label.setText("-")
        self.patient_ddn_label.setText("-")
        self.patient_sexe_label.setText("-")
        self.patient_nir_label.setText("-")
        self.exam_nom_label.setText("-")
        self.result_value_input.clear()
        self.comment_edit.clear()
        self.critical_check.setChecked(False)
        self.status_bar.showMessage("Prêt")


# Import nécessaire pour QInputDialog
from PyQt6.QtWidgets import QInputDialog
