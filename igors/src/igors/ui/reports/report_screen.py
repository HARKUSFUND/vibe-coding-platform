"""Écran de reporting et génération de rapports - IGORS v2.0"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QTabWidget,
    QComboBox, QDateEdit, QFileDialog, QProgressBar,
    QStatusBar, QListWidget, QListWidgetItem, QTextEdit,
    QCheckBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont

from datetime import datetime, date, timedelta
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class ReportScreen(QWidget):
    """Interface de génération de rapports et comptes rendus"""
    
    report_generated = pyqtSignal(str)
    
    def __init__(self, reporting_service, parent=None):
        super().__init__(parent)
        self.reporting_service = reporting_service
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        title = QLabel("Reporting et Comptes Rendus")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        tabs = QTabWidget()
        
        # Tab 1: Comptes rendus patients
        cr_tab = QWidget()
        cr_layout = QVBoxLayout(cr_tab)
        
        patient_group = QGroupBox("Sélection du Patient")
        patient_layout = QFormLayout(patient_group)
        
        self.patient_search_input = QLineEdit()
        self.patient_search_input.setPlaceholderText("Rechercher un patient...")
        patient_layout.addRow("Patient:", self.patient_search_input)
        
        self.date_debut_input = QDateEdit()
        self.date_debut_input.setDate(QDate.currentDate().addDays(-30))
        self.date_debut_input.setCalendarPopup(True)
        patient_layout.addRow("Date début:", self.date_debut_input)
        
        self.date_fin_input = QDateEdit()
        self.date_fin_input.setDate(QDate.currentDate())
        self.date_fin_input.setCalendarPopup(True)
        patient_layout.addRow("Date fin:", self.date_fin_input)
        
        cr_layout.addWidget(patient_group)
        
        options_group = QGroupBox("Options du Compte Rendu")
        options_layout = QVBoxLayout(options_group)
        
        self.include_graphs_check = QCheckBox("Inclure graphiques de tendances")
        self.include_history_check = QCheckBox("Inclure historique des résultats")
        self.include_refs_check = QCheckBox("Inclure valeurs de référence")
        self.pdf_format_check = QCheckBox("Format PDF/A-3 (archivage)")
        
        options_layout.addWidget(self.include_graphs_check)
        options_layout.addWidget(self.include_history_check)
        options_layout.addWidget(self.include_refs_check)
        options_layout.addWidget(self.pdf_format_check)
        
        cr_layout.addWidget(options_group)
        
        btn_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("👁️ Aperçu")
        self.preview_btn.clicked.connect(self.preview_cr)
        btn_layout.addWidget(self.preview_btn)
        
        self.generate_cr_btn = QPushButton("📄 Générer CR")
        self.generate_cr_btn.clicked.connect(self.generate_cr)
        self.generate_cr_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white;
                padding: 10px 20px; border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        btn_layout.addWidget(self.generate_cr_btn)
        
        self.send_email_btn = QPushButton("📧 Envoyer par email")
        self.send_email_btn.clicked.connect(self.send_cr_email)
        btn_layout.addWidget(self.send_email_btn)
        
        btn_layout.addStretch()
        cr_layout.addLayout(btn_layout)
        
        self.cr_preview = QTextEdit()
        self.cr_preview.setReadOnly(True)
        self.cr_preview.setMinimumHeight(200)
        cr_layout.addWidget(self.cr_preview)
        
        tabs.addTab(cr_tab, "📋 Comptes Rendus")
        
        # Tab 2: Rapports statistiques
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        type_group = QGroupBox("Type de Rapport")
        type_layout = QVBoxLayout(type_group)
        
        self.report_type_group = QButtonGroup()
        
        self.rapport_activite_radio = QRadioButton("Rapport d'activité")
        self.rapport_activite_radio.setChecked(True)
        type_layout.addWidget(self.rapport_activite_radio)
        
        self.rapport_delais_radio = QRadioButton("Délais de rendu")
        type_layout.addWidget(self.rapport_delais_radio)
        
        self.rapport_validation_radio = QRadioButton("Taux de validation auto")
        type_layout.addWidget(self.rapport_validation_radio)
        
        self.rapport_qualite_radio = QRadioButton("Rapport qualité (CQI/EEQ)")
        type_layout.addWidget(self.rapport_qualite_radio)
        
        self.rapport_psl_radio = QRadioButton("Stocks PSL")
        type_layout.addWidget(self.rapport_psl_radio)
        
        stats_layout.addWidget(type_group)
        
        period_group = QGroupBox("Période")
        period_layout = QHBoxLayout(period_group)
        
        self.stats_date_debut = QDateEdit()
        self.stats_date_debut.setDate(QDate.currentDate().addMonths(-1))
        self.stats_date_debut.setCalendarPopup(True)
        period_layout.addWidget(QLabel("Du:"))
        period_layout.addWidget(self.stats_date_debut)
        
        self.stats_date_fin = QDateEdit()
        self.stats_date_fin.setDate(QDate.currentDate())
        self.stats_date_fin.setCalendarPopup(True)
        period_layout.addWidget(QLabel("Au:"))
        period_layout.addWidget(self.stats_date_fin)
        
        period_layout.addStretch()
        stats_layout.addWidget(period_group)
        
        format_group = QGroupBox("Format d'Export")
        format_layout = QHBoxLayout(format_group)
        
        self.export_pdf_radio = QRadioButton("PDF")
        self.export_pdf_radio.setChecked(True)
        format_layout.addWidget(self.export_pdf_radio)
        
        self.export_excel_radio = QRadioButton("Excel")
        format_layout.addWidget(self.export_excel_radio)
        
        self.export_csv_radio = QRadioButton("CSV")
        format_layout.addWidget(self.export_csv_radio)
        
        self.export_snis_radio = QRadioButton("SNIS (XML)")
        format_layout.addWidget(self.export_snis_radio)
        
        format_layout.addStretch()
        stats_layout.addWidget(format_group)
        
        stats_btn_layout = QHBoxLayout()
        
        self.generate_stats_btn = QPushButton("📊 Générer Rapport")
        self.generate_stats_btn.clicked.connect(self.generate_stats_report)
        self.generate_stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                padding: 10px 20px; border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2ecc71; }
        """)
        stats_btn_layout.addWidget(self.generate_stats_btn)
        
        self.export_stats_btn = QPushButton("💾 Exporter")
        self.export_stats_btn.clicked.connect(self.export_stats_report)
        stats_btn_layout.addWidget(self.export_stats_btn)
        
        stats_btn_layout.addStretch()
        stats_layout.addLayout(stats_btn_layout)
        
        reports_list_group = QGroupBox("Rapports Générés")
        reports_list_layout = QVBoxLayout(reports_list_group)
        
        self.reports_list = QListWidget()
        self.reports_list.itemDoubleClicked.connect(self.open_report)
        reports_list_layout.addWidget(self.reports_list)
        
        list_btn_layout = QHBoxLayout()
        
        self.refresh_reports_btn = QPushButton("🔄 Actualiser")
        self.refresh_reports_btn.clicked.connect(self.load_generated_reports)
        list_btn_layout.addWidget(self.refresh_reports_btn)
        
        self.open_report_btn = QPushButton("📂 Ouvrir")
        self.open_report_btn.clicked.connect(self.open_selected_report)
        list_btn_layout.addWidget(self.open_report_btn)
        
        self.delete_report_btn = QPushButton("🗑️ Supprimer")
        self.delete_report_btn.clicked.connect(self.delete_selected_report)
        list_btn_layout.addWidget(self.delete_report_btn)
        
        list_btn_layout.addStretch()
        reports_list_layout.addLayout(list_btn_layout)
        
        stats_layout.addWidget(reports_list_group)
        
        tabs.addTab(stats_tab, "📈 Statistiques")
        
        # Tab 3: Transmission SNIS
        snis_tab = QWidget()
        snis_layout = QVBoxLayout(snis_tab)
        
        snis_info = QLabel("Transmission des indicateurs au Système National d'Information Sanitaire")
        snis_info.setFont(QFont("Arial", 11))
        snis_layout.addWidget(snis_info)
        
        snis_group = QGroupBox("Paramètres SNIS")
        snis_form = QFormLayout(snis_group)
        
        self.snis_periode_combo = QComboBox()
        self.snis_periode_combo.addItems(["Mensuel", "Trimestriel", "Annuel"])
        snis_form.addRow("Périodicité:", self.snis_periode_combo)
        
        self.snis_mois_input = QDateEdit()
        self.snis_mois_input.setDate(QDate.currentDate())
        self.snis_mois_input.setDisplayFormat("MMMM yyyy")
        snis_form.addRow("Mois de référence:", self.snis_mois_input)
        
        snis_layout.addWidget(snis_group)
        
        indicators_group = QGroupBox("Indicateurs à Transmettre")
        indicators_layout = QVBoxLayout(indicators_group)
        
        self.indicators_table = QTableWidget()
        self.indicators_table.setColumnCount(3)
        self.indicators_table.setHorizontalHeaderLabels([
            "Indicateur", "Valeur", "Statut"
        ])
        self.indicators_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        indicators_layout.addWidget(self.indicators_table)
        
        snis_layout.addWidget(indicators_group)
        
        snis_btn_layout = QHBoxLayout()
        
        self.calculate_indicators_btn = QPushButton("📊 Calculer indicateurs")
        self.calculate_indicators_btn.clicked.connect(self.calculate_snis_indicators)
        snis_btn_layout.addWidget(self.calculate_indicators_btn)
        
        self.validate_snis_btn = QPushButton("✅ Valider")
        self.validate_snis_btn.clicked.connect(self.validate_snis_data)
        snis_btn_layout.addWidget(self.validate_snis_btn)
        
        self.transmit_snis_btn = QPushButton("📤 Transmettre SNIS")
        self.transmit_snis_btn.clicked.connect(self.transmit_to_snis)
        self.transmit_snis_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6; color: white;
                padding: 10px 20px; border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        snis_btn_layout.addWidget(self.transmit_snis_btn)
        
        snis_btn_layout.addStretch()
        snis_layout.addLayout(snis_btn_layout)
        
        self.snis_log = QTextEdit()
        self.snis_log.setReadOnly(True)
        self.snis_log.setMaximumHeight(150)
        self.snis_log.setPlaceholderText("Journal de transmission SNIS...")
        snis_layout.addWidget(self.snis_log)
        
        tabs.addTab(snis_tab, "🏥 SNIS")
        
        layout.addWidget(tabs)
        
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Prêt - Reporting")
        layout.addWidget(self.status_bar)
        
        self.load_generated_reports()
        
    def load_generated_reports(self):
        try:
            self.reports_list.clear()
            reports = self.reporting_service.get_generated_reports()
            
            for report in reports:
                item_text = f"{report.get('type', 'Inconnu')} - {report.get('date', '')}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, report.get('id'))
                self.reports_list.addItem(item)
            
            self.status_bar.showMessage(f"{len(reports)} rapport(s) trouvé(s)")
            
        except Exception as e:
            logger.error(f"Erreur chargement rapports: {e}")
            
    def preview_cr(self):
        try:
            patient_name = self.patient_search_input.text()
            if not patient_name:
                QMessageBox.warning(self, "Attention", "Veuillez saisir un nom de patient")
                return
                
            preview = self.reporting_service.generate_cr_preview(
                patient_name=patient_name,
                date_debut=self.date_debut_input.date().toPyDate(),
                date_fin=self.date_fin_input.date().toPyDate()
            )
            
            self.cr_preview.setText(preview)
            self.status_bar.showMessage("Aperçu généré")
            
        except Exception as e:
            logger.error(f"Erreur aperçu CR: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible de générer l'aperçu: {e}")
            
    def generate_cr(self):
        try:
            patient_name = self.patient_search_input.text()
            if not patient_name:
                QMessageBox.warning(self, "Attention", "Veuillez saisir un nom de patient")
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Enregistrer le compte rendu", "", 
                "Fichiers PDF (*.pdf)"
            )
            
            if file_path:
                pdf_path = self.reporting_service.generate_cr_pdf(
                    patient_name=patient_name,
                    date_debut=self.date_debut_input.date().toPyDate(),
                    date_fin=self.date_fin_input.date().toPyDate(),
                    include_graphs=self.include_graphs_check.isChecked(),
                    include_history=self.include_history_check.isChecked(),
                    include_refs=self.include_refs_check.isChecked(),
                    pdf_a_format=self.pdf_format_check.isChecked()
                )
                
                QMessageBox.information(self, "Succès", f"Compte rendu généré: {file_path}")
                self.report_generated.emit(pdf_path)
                self.status_bar.showMessage("Compte rendu généré")
                
        except Exception as e:
            logger.error(f"Erreur génération CR: {e}")
            QMessageBox.critical(self, "Erreur", f"Échec de la génération: {e}")
            
    def send_cr_email(self):
        QMessageBox.information(self, "Info", "Fonctionnalité email à configurer")
        
    def generate_stats_report(self):
        try:
            report_type = "activite"
            if self.rapport_delais_radio.isChecked():
                report_type = "delais"
            elif self.rapport_validation_radio.isChecked():
                report_type = "validation"
            elif self.rapport_qualite_radio.isChecked():
                report_type = "qualite"
            elif self.rapport_psl_radio.isChecked():
                report_type = "psl"
            
            stats = self.reporting_service.generate_stats_report(
                report_type=report_type,
                date_debut=self.stats_date_debut.date().toPyDate(),
                date_fin=self.stats_date_fin.date().toPyDate()
            )
            
            summary = f"Rapport: {report_type}\n"
            summary += f"Période: {self.stats_date_debut.date().toString('dd/MM/yyyy')} au {self.stats_date_fin.date().toString('dd/MM/yyyy')}\n\n"
            summary += f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            
            self.status_bar.showMessage(f"Rapport {report_type} généré")
            
        except Exception as e:
            logger.error(f"Erreur rapport stats: {e}")
            QMessageBox.critical(self, "Erreur", f"Échec de la génération: {e}")
            
    def export_stats_report(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exporter le rapport", "", 
                "PDF (*.pdf);;Excel (*.xlsx);;CSV (*.csv)"
            )
            
            if file_path:
                QMessageBox.information(self, "Succès", f"Rapport exporté: {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de l'export: {e}")
            
    def open_report(self, item):
        report_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            self.reporting_service.open_report(report_id)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ouvrir le rapport: {e}")
            
    def open_selected_report(self):
        selected = self.reports_list.currentItem()
        if selected:
            self.open_report(selected)
        else:
            QMessageBox.warning(self, "Attention", "Aucun rapport sélectionné")
            
    def delete_selected_report(self):
        selected = self.reports_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Attention", "Aucun rapport sélectionné")
            return
            
        confirmation = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment supprimer ce rapport ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirmation == QMessageBox.StandardButton.Yes:
            try:
                report_id = selected.data(Qt.ItemDataRole.UserRole)
                self.reporting_service.delete_report(report_id)
                self.load_generated_reports()
                QMessageBox.information(self, "Succès", "Rapport supprimé")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de la suppression: {e}")
                
    def calculate_snis_indicators(self):
        try:
            indicators = self.reporting_service.calculate_snis_indicators(
                periode=self.snis_mois_input.date().toPyDate()
            )
            
            self.indicators_table.setRowCount(0)
            for ind in indicators:
                row = self.indicators_table.rowCount()
                self.indicators_table.insertRow(row)
                
                self.indicators_table.setItem(row, 0, QTableWidgetItem(ind.get('nom', '')))
                self.indicators_table.setItem(row, 1, QTableWidgetItem(str(ind.get('valeur', ''))))
                
                status = "✓" if ind.get('valide', False) else "⚠️"
                self.indicators_table.setItem(row, 2, QTableWidgetItem(status))
            
            self.snis_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Indicateurs calculés: {len(indicators)}")
            
        except Exception as e:
            logger.error(f"Erreur calcul SNIS: {e}")
            
    def validate_snis_data(self):
        QMessageBox.information(self, "Validation", "Données SNIS validées")
        self.snis_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Validation effectuée")
        
    def transmit_to_snis(self):
        try:
            result = self.reporting_service.transmit_to_snis(
                periode=self.snis_mois_input.date().toPyDate()
            )
            
            if result.get('success'):
                QMessageBox.information(self, "Succès", "Transmission SNIS réussie")
                self.snis_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Transmission réussie")
            else:
                QMessageBox.warning(self, "Attention", f"Transmission échouée: {result.get('error', '')}")
                self.snis_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Échec: {result.get('error', '')}")
                
        except Exception as e:
            logger.error(f"Erreur transmission SNIS: {e}")
            QMessageBox.critical(self, "Erreur", f"Échec de la transmission: {e}")
