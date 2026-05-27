"""Écran de monitoring des automates - IGORS v2.0"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QTabWidget,
    QComboBox, QDateEdit, QLineEdit, QTextEdit,
    QProgressBar, QStatusBar, QSplitter, QFrame,
    QListWidget, QListWidgetItem, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from datetime import datetime, date
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class AutomateMonitoringScreen(QWidget):
    """Interface de monitoring et communication avec les automates"""
    
    automate_connected = pyqtSignal(dict)
    automate_error = pyqtSignal(dict)
    
    def __init__(self, automate_service, parent=None):
        super().__init__(parent)
        self.automate_service = automate_service
        self.current_automate = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        title = QLabel("Monitoring des Automates")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panneau gauche - Liste des automates
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stats connexion
        stats_group = QGroupBox("État des Connexions")
        stats_layout = QHBoxLayout(stats_group)
        
        self.connected_count_label = QLabel("Connectés: 0")
        self.connected_count_label.setStyleSheet("font-weight: bold; color: green;")
        stats_layout.addWidget(self.connected_count_label)
        
        self.disconnected_count_label = QLabel("Déconnectés: 0")
        stats_layout.addWidget(self.disconnected_count_label)
        
        self.error_count_label = QLabel("Erreurs: 0")
        self.error_count_label.setStyleSheet("font-weight: bold; color: red;")
        stats_layout.addWidget(self.error_count_label)
        
        stats_layout.addStretch()
        left_layout.addWidget(stats_group)
        
        # Liste des automates
        self.automate_list = QListWidget()
        self.automate_list.itemSelectionChanged.connect(self.on_automate_selected)
        left_layout.addWidget(self.automate_list)
        
        # Boutons d'action
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Actualiser")
        self.refresh_btn.clicked.connect(self.load_automates)
        btn_layout.addWidget(self.refresh_btn)
        
        self.connect_btn = QPushButton("🔌 Connecter")
        self.connect_btn.clicked.connect(self.connect_automate)
        btn_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("🔌 Déconnecter")
        self.disconnect_btn.clicked.connect(self.disconnect_automate)
        btn_layout.addWidget(self.disconnect_btn)
        
        left_layout.addLayout(btn_layout)
        
        splitter.addWidget(left_panel)
        
        # Panneau droit - Détails et monitoring
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabs
        tabs = QTabWidget()
        
        # Tab 1: Informations automate
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        
        # Informations générales
        general_group = QGroupBox("Informations Générales")
        general_layout = QFormLayout(general_group)
        
        self.info_nom_label = QLabel("-")
        self.info_nom_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        general_layout.addRow("Nom:", self.info_nom_label)
        
        self.info_modele_label = QLabel("-")
        general_layout.addRow("Modèle:", self.info_modele_label)
        
        self.info_constructeur_label = QLabel("-")
        general_layout.addRow("Constructeur:", self.info_constructeur_label)
        
        self.info_serial_label = QLabel("-")
        general_layout.addRow("N° Série:", self.info_serial_label)
        
        self.info_version_label = QLabel("-")
        general_layout.addRow("Version FW:", self.info_version_label)
        
        self.info_emplacement_label = QLabel("-")
        general_layout.addRow("Emplacement:", self.info_emplacement_label)
        
        info_layout.addWidget(general_group)
        
        # État connexion
        connection_group = QGroupBox("État de la Connexion")
        connection_layout = QFormLayout(connection_group)
        
        self.connection_status_label = QLabel("Statut: Non connecté")
        self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
        connection_layout.addRow(self.connection_status_label)
        
        self.connection_protocol_label = QLabel("Protocole: -")
        connection_layout.addRow("Protocole:", self.connection_protocol_label)
        
        self.connection_port_label = QLabel("Port: -")
        connection_layout.addRow("Port:", self.connection_port_label)
        
        self.connection_last_sync_label = QLabel("Dernière synchro: -")
        connection_layout.addRow("Dernière synchro:", self.connection_last_sync_label)
        
        info_layout.addWidget(connection_group)
        
        # Performances
        perf_group = QGroupBox("Performances")
        perf_layout = QVBoxLayout(perf_group)
        
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setFormat("CPU: %p%")
        self.cpu_progress.setValue(0)
        perf_layout.addWidget(self.cpu_progress)
        
        self.memory_progress = QProgressBar()
        self.memory_progress.setFormat("Mémoire: %p%")
        self.memory_progress.setValue(0)
        perf_layout.addWidget(self.memory_progress)
        
        self.samples_today_label = QLabel("Analyses aujourd'hui: 0")
        perf_layout.addWidget(self.samples_today_label)
        
        self.errors_today_label = QLabel("Erreurs aujourd'hui: 0")
        perf_layout.addWidget(self.errors_today_label)
        
        info_layout.addWidget(perf_group)
        
        tabs.addTab(info_tab, "📋 Informations")
        
        # Tab 2: Worklist
        worklist_tab = QWidget()
        worklist_layout = QVBoxLayout(worklist_tab)
        
        # Table worklist
        self.worklist_table = QTableWidget()
        self.worklist_table.setColumnCount(6)
        self.worklist_table.setHorizontalHeaderLabels([
            "ID", "Patient", "Examen", "Priorité", "Statut", "Date"
        ])
        self.worklist_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        worklist_layout.addWidget(self.worklist_table)
        
        # Boutons worklist
        wl_btn_layout = QHBoxLayout()
        
        self.send_worklist_btn = QPushButton("📤 Envoyer Worklist")
        self.send_worklist_btn.clicked.connect(self.send_worklist)
        wl_btn_layout.addWidget(self.send_worklist_btn)
        
        self.clear_worklist_btn = QPushButton("🗑️ Vider Worklist")
        self.clear_worklist_btn.clicked.connect(self.clear_worklist)
        wl_btn_layout.addWidget(self.clear_worklist_btn)
        
        wl_btn_layout.addStretch()
        worklist_layout.addLayout(wl_btn_layout)
        
        tabs.addTab(worklist_tab, "📝 Worklist")
        
        # Tab 3: Résultats bruts
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        
        # Table résultats
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "ID", "Tube", "Examen", "Résultat brut", "Unité", 
            "Drapeau", "Date/Heure"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        results_layout.addWidget(self.results_table)
        
        # Boutons résultats
        res_btn_layout = QHBoxLayout()
        
        self.fetch_results_btn = QPushButton("📥 Récupérer résultats")
        self.fetch_results_btn.clicked.connect(self.fetch_results)
        res_btn_layout.addWidget(self.fetch_results_btn)
        
        self.process_results_btn = QPushButton("⚙️ Traiter résultats")
        self.process_results_btn.clicked.connect(self.process_results)
        res_btn_layout.addWidget(self.process_results_btn)
        
        res_btn_layout.addStretch()
        results_layout.addLayout(res_btn_layout)
        
        tabs.addTab(results_tab, "📊 Résultats")
        
        # Tab 4: Journal
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 9))
        self.log_text.setStyleSheet("background-color: #1a1a1a; color: #00ff00;")
        log_layout.addWidget(self.log_text)
        
        # Boutons journal
        log_btn_layout = QHBoxLayout()
        
        self.clear_log_btn = QPushButton("🗑️ Effacer journal")
        self.clear_log_btn.clicked.connect(lambda: self.log_text.clear())
        log_btn_layout.addWidget(self.clear_log_btn)
        
        self.export_log_btn = QPushButton("💾 Exporter journal")
        self.export_log_btn.clicked.connect(self.export_log)
        log_btn_layout.addWidget(self.export_log_btn)
        
        log_btn_layout.addStretch()
        log_layout.addLayout(log_btn_layout)
        
        tabs.addTab(log_tab, "📜 Journal")
        
        right_layout.addWidget(tabs)
        
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Prêt - Monitoring automates")
        layout.addWidget(self.status_bar)
        
        # Timer pour rafraîchissement automatique
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(60000)  # 1 minute
        
        # Charger les automates
        self.load_automates()
        
    def load_automates(self):
        """Charger la liste des automates"""
        try:
            self.automate_list.clear()
            
            automates = self.automate_service.get_all_automates()
            
            connected_count = 0
            disconnected_count = 0
            error_count = 0
            
            for auto in automates:
                nom = auto.get('nom', 'Inconnu')
                statut = auto.get('statut_connexion', 'Déconnecté')
                
                # Icône selon statut
                if statut == 'Connecté':
                    icon = "🟢"
                    connected_count += 1
                elif statut == 'Erreur':
                    icon = "🔴"
                    error_count += 1
                else:
                    icon = "⚪"
                    disconnected_count += 1
                
                item_text = f"{icon} {nom} ({statut})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, auto.get('id'))
                self.automate_list.addItem(item)
            
            self.connected_count_label.setText(f"Connectés: {connected_count}")
            self.disconnected_count_label.setText(f"Déconnectés: {disconnected_count}")
            self.error_count_label.setText(f"Erreurs: {error_count}")
            
            self.status_bar.showMessage(f"{len(automates)} automate(s) trouvé(s)")
            self.log_message(f"Rafraîchissement: {len(automates)} automates")
            
        except Exception as e:
            logger.error(f"Erreur chargement automates: {e}")
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les automates: {e}")
            
    def on_automate_selected(self):
        """Afficher les détails de l'automate sélectionné"""
        selected_items = self.automate_list.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        automate_id = item.data(Qt.ItemDataRole.UserRole)
        
        try:
            self.current_automate = self.automate_service.get_automate_by_id(automate_id)
            self.display_automate_details()
            self.load_worklist()
            self.load_results()
            self.status_bar.showMessage(f"Automate: {self.current_automate.get('nom')}")
            
        except Exception as e:
            logger.error(f"Erreur chargement détails automate: {e}")
            
    def display_automate_details(self):
        """Afficher les détails de l'automate"""
        if not self.current_automate:
            return
            
        # Informations générales
        self.info_nom_label.setText(self.current_automate.get('nom', '-'))
        self.info_modele_label.setText(self.current_automate.get('modele', '-'))
        self.info_constructeur_label.setText(self.current_automate.get('constructeur', '-'))
        self.info_serial_label.setText(self.current_automate.get('numero_serie', '-'))
        self.info_version_label.setText(self.current_automate.get('version_fw', '-'))
        self.info_emplacement_label.setText(self.current_automate.get('emplacement', '-'))
        
        # État connexion
        statut = self.current_automate.get('statut_connexion', 'Déconnecté')
        if statut == 'Connecté':
            self.connection_status_label.setText("Statut: ✅ Connecté")
            self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")
        elif statut == 'Erreur':
            self.connection_status_label.setText("Statut: ❌ Erreur")
            self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.connection_status_label.setText("Statut: ⚪ Déconnecté")
            self.connection_status_label.setStyleSheet("color: orange; font-weight: bold;")
        
        self.connection_protocol_label.setText(self.current_automate.get('protocole', '-'))
        self.connection_port_label.setText(str(self.current_automate.get('port', '-')))
        
        last_sync = self.current_automate.get('derniere_sync', '-')
        if isinstance(last_sync, datetime):
            last_sync = last_sync.strftime('%d/%m/%Y %H:%M:%S')
        self.connection_last_sync_label.setText(str(last_sync))
        
        # Performances
        cpu = self.current_automate.get('cpu_usage', 0)
        memory = self.current_automate.get('memory_usage', 0)
        self.cpu_progress.setValue(int(cpu))
        self.memory_progress.setValue(int(memory))
        
        samples = self.current_automate.get('samples_today', 0)
        errors = self.current_automate.get('errors_today', 0)
        self.samples_today_label.setText(f"Analyses aujourd'hui: {samples}")
        self.errors_today_label.setText(f"Erreurs aujourd'hui: {errors}")
        
        # Mettre à jour couleurs barres
        if cpu > 80:
            self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        elif cpu > 60:
            self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
        else:
            self.cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: green; }")
            
    def load_worklist(self):
        """Charger la worklist de l'automate"""
        if not self.current_automate:
            return
            
        try:
            worklist = self.automate_service.get_worklist(self.current_automate.get('id'))
            self.worklist_table.setRowCount(0)
            
            for wl_item in worklist:
                row = self.worklist_table.rowCount()
                self.worklist_table.insertRow(row)
                
                self.worklist_table.setItem(row, 0, QTableWidgetItem(str(wl_item.get('id', ''))))
                self.worklist_table.setItem(row, 1, QTableWidgetItem(
                    f"{wl_item.get('patient_nom', '')} {wl_item.get('patient_prenom', '')}"
                ))
                self.worklist_table.setItem(row, 2, QTableWidgetItem(wl_item.get('examen_nom', '')))
                
                priorite = wl_item.get('priorite', 'Normale')
                prio_item = QTableWidgetItem(priorite)
                if priorite == 'Urgente':
                    prio_item.setForeground(QColor('red'))
                self.worklist_table.setItem(row, 3, prio_item)
                
                statut = wl_item.get('statut', 'En attente')
                self.worklist_table.setItem(row, 4, QTableWidgetItem(statut))
                
                date_val = wl_item.get('date', '')
                if isinstance(date_val, datetime):
                    date_val = date_val.strftime('%d/%m/%Y %H:%M')
                self.worklist_table.setItem(row, 5, QTableWidgetItem(str(date_val)))
                
        except Exception as e:
            logger.error(f"Erreur chargement worklist: {e}")
            
    def load_results(self):
        """Charger les résultats bruts de l'automate"""
        if not self.current_automate:
            return
            
        try:
            results = self.automate_service.get_raw_results(self.current_automate.get('id'))
            self.results_table.setRowCount(0)
            
            for res in results:
                row = self.results_table.rowCount()
                self.results_table.insertRow(row)
                
                self.results_table.setItem(row, 0, QTableWidgetItem(str(res.get('id', ''))))
                self.results_table.setItem(row, 1, QTableWidgetItem(res.get('tube_id', '')))
                self.results_table.setItem(row, 2, QTableWidgetItem(res.get('examen_nom', '')))
                self.results_table.setItem(row, 3, QTableWidgetItem(str(res.get('valeur_brute', ''))))
                self.results_table.setItem(row, 4, QTableWidgetItem(res.get('unite', '')))
                
                flag = res.get('drapeau', '')
                flag_item = QTableWidgetItem(flag)
                if flag:
                    flag_item.setForeground(QColor('red'))
                self.results_table.setItem(row, 5, flag_item)
                
                date_val = res.get('date_heure', '')
                if isinstance(date_val, datetime):
                    date_val = date_val.strftime('%d/%m/%Y %H:%M')
                self.results_table.setItem(row, 6, QTableWidgetItem(str(date_val)))
                
        except Exception as e:
            logger.error(f"Erreur chargement résultats: {e}")
            
    def connect_automate(self):
        """Connecter l'automate sélectionné"""
        if not self.current_automate:
            QMessageBox.warning(self, "Attention", "Aucun automate sélectionné")
            return
            
        try:
            result = self.automate_service.connect_automate(self.current_automate.get('id'))
            
            if result.get('success'):
                QMessageBox.information(self, "Succès", "Automate connecté avec succès")
                self.log_message(f"Connexion réussie: {self.current_automate.get('nom')}")
                self.automate_connected.emit(result)
                self.load_automates()
            else:
                QMessageBox.critical(self, "Erreur", f"Échec de connexion: {result.get('error', 'Inconnue')}")
                self.log_message(f"Échec connexion: {result.get('error', 'Inconnue')}")
                
        except Exception as e:
            logger.error(f"Erreur connexion automate: {e}")
            QMessageBox.critical(self, "Erreur", f"Échec de la connexion: {e}")
            
    def disconnect_automate(self):
        """Déconnecter l'automate sélectionné"""
        if not self.current_automate:
            QMessageBox.warning(self, "Attention", "Aucun automate sélectionné")
            return
            
        confirmation = QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous vraiment déconnecter {self.current_automate.get('nom')} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirmation == QMessageBox.StandardButton.Yes:
            try:
                self.automate_service.disconnect_automate(self.current_automate.get('id'))
                QMessageBox.information(self, "Succès", "Automate déconnecté")
                self.log_message(f"Déconnexion: {self.current_automate.get('nom')}")
                self.load_automates()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de la déconnexion: {e}")
                
    def send_worklist(self):
        """Envoyer une worklist à l'automate"""
        if not self.current_automate:
            QMessageBox.warning(self, "Attention", "Aucun automate sélectionné")
            return
            
        try:
            count = self.automate_service.send_worklist_to_automate(
                self.current_automate.get('id')
            )
            QMessageBox.information(self, "Succès", f"{count} envoi(s) envoyé(s) à l'automate")
            self.log_message(f"Worklist envoyée: {count} éléments")
            self.load_worklist()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de l'envoi: {e}")
            
    def clear_worklist(self):
        """Vider la worklist"""
        if not self.current_automate:
            return
            
        confirmation = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment vider la worklist ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirmation == QMessageBox.StandardButton.Yes:
            try:
                self.automate_service.clear_worklist(self.current_automate.get('id'))
                QMessageBox.information(self, "Succès", "Worklist vidée")
                self.load_worklist()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec du vidage: {e}")
                
    def fetch_results(self):
        """Récupérer les résultats de l'automate"""
        if not self.current_automate:
            QMessageBox.warning(self, "Attention", "Aucun automate sélectionné")
            return
            
        try:
            count = self.automate_service.fetch_results_from_automate(
                self.current_automate.get('id')
            )
            QMessageBox.information(self, "Succès", f"{count} résultat(s) récupéré(s)")
            self.log_message(f"Résultats récupérés: {count}")
            self.load_results()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de la récupération: {e}")
            
    def process_results(self):
        """Traiter les résultats bruts"""
        if not self.current_automate:
            return
            
        try:
            processed = self.automate_service.process_raw_results(
                self.current_automate.get('id')
            )
            QMessageBox.information(
                self, "Succès", 
                f"{processed.get('processed', 0)} résultat(s) traité(s), "
                f"{processed.get('errors', 0)} erreur(s)"
            )
            self.log_message(f"Résultats traités: {processed.get('processed', 0)}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec du traitement: {e}")
            
    def export_log(self):
        """Exporter le journal"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le journal", "", "Fichiers TXT (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "Succès", f"Journal exporté vers {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Échec de l'export: {e}")
                
    def log_message(self, message):
        """Ajouter un message au journal"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.append(f"[{timestamp}] {message}")
        
    def auto_refresh(self):
        """Rafraîchissement automatique"""
        self.load_automates()
        if self.current_automate:
            self.display_automate_details()
            self.load_worklist()
            self.load_results()
