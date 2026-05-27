"""
Handlers pour la communication avec les automates de laboratoire.
Protocoles ASTM E1381/E1394 et HL7 v2.x.
"""
import asyncio
import serial
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class AutomateHandler(ABC):
    """Classe de base pour les handlers d'automates."""
    
    def __init__(self, port: str, baud_rate: int = 9600, timeout: int = 30):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.connection: Optional[serial.Serial] = None
    
    @abstractmethod
    def connecter(self) -> bool:
        """Établir la connexion avec l'automate."""
        pass
    
    @abstractmethod
    def deconnecter(self):
        """Fermer la connexion."""
        pass
    
    @abstractmethod
    def envoyer_commande(self, commande: str) -> str:
        """Envoyer une commande à l'automate."""
        pass
    
    @abstractmethod
    def recevoir_reponse(self) -> str:
        """Recevoir une réponse de l'automate."""
        pass


class ASTMHandler(AutomateHandler):
    """
    Handler pour le protocole ASTM E1381/E1394.
    Utilisé par la majorité des automates de biologie médicale.
    """
    
    # Caractères de contrôle ASTM
    STX = '\x02'  # Start of Text
    ETX = '\x03'  # End of Text
    EOT = '\x04'  # End of Transmission
    ENQ = '\x05'  # Enquiry
    ACK = '\x06'  # Acknowledge
    NAK = '\x15'  # Negative Acknowledge
    LF = '\x0A'   # Line Feed
    CR = '\x0D'   # Carriage Return
    
    def __init__(self, port: str, baud_rate: int = 9600, automate_id: Optional[int] = None):
        super().__init__(port, baud_rate)
        self.automate_id = automate_id
        self.sequence_number = 0
        self.message_queue: List[str] = []
    
    def connecter(self) -> bool:
        """Établir la connexion série avec l'automate."""
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            logger.info(f"Connecté à l'automate ASTM sur {self.port}")
            return True
        except serial.SerialException as e:
            logger.error(f"Échec connexion ASTM: {e}")
            return False
    
    def deconnecter(self):
        """Fermer la connexion série."""
        if self.connection and self.connection.is_open:
            self.envoyer_caractere(self.EOT)
            self.connection.close()
            logger.info("Déconnecté de l'automate ASTM")
    
    def envoyer_commande(self, commande: str) -> str:
        """
        Envoyer une commande et attendre la réponse.
        Format ASTM: <STX>message<ETX><checksum><CR><LF>
        """
        if not self.connection or not self.connection.is_open:
            raise ConnectionError("Non connecté à l'automate")
        
        # Incrémenter le numéro de séquence
        self.sequence_number = (self.sequence_number % 8) + 1
        
        # Construire le message ASTM
        message = f"{self.sequence_number}{commande}"
        checksum = self._calculer_checksum(message)
        trame = f"{self.STX}{message}{self.ETX}{checksum:02X}{self.CR}{self.LF}"
        
        # Envoyer et attendre ACK
        self.connection.write(trame.encode())
        reponse = self.connection.read(1).decode()
        
        if reponse == self.ACK:
            # Attendre la réponse de l'automate
            return self.recevoir_reponse()
        elif reponse == self.NAK:
            logger.warning("NAK reçu - réessai")
            return self.envoyer_commande(commande)  # Réessai
        else:
            raise TimeoutError(f"Réponse invalide: {reponse}")
    
    def recevoir_reponse(self) -> str:
        """Recevoir un message ASTM complet."""
        if not self.connection:
            raise ConnectionError("Non connecté")
        
        buffer = ""
        while True:
            char = self.connection.read(1).decode()
            if not char:
                raise TimeoutError("Timeout réception ASTM")
            
            if char == self.STX:
                buffer = ""
            elif char == self.ETX:
                # Vérifier le checksum
                checksum_recu = self.connection.read(2).decode()
                cr_lf = self.connection.read(2)  # CR+LF
                
                if self._verifier_checksum(buffer, checksum_recu):
                    self.connection.write(self.ACK.encode())
                    return buffer
                else:
                    self.connection.write(self.NAK.encode())
                    buffer = ""
            else:
                buffer += char
    
    def demander_worklist(self, criteria: Dict[str, Any]) -> List[Dict]:
        """
        Demander une worklist (Host Query) à l'automate.
        CDC §4.4: Récupérer les échantillons à analyser.
        """
        # Construire la requête Q (Query) ASTM
        # Format: Q|^|\\^&||PATIENT|||||||
        patient_id = criteria.get('patient_id', '')
        commande = f"Q|^|\\^&||{patient_id}|||||||"
        
        reponse = self.envoyer_commande(commande)
        
        # Parser la réponse (lignes L pour les commandes)
        resultats = []
        for ligne in reponse.split(self.LF):
            if ligne.startswith('L'):
                parts = ligne.split('|')
                if len(parts) >= 7:
                    resultats.append({
                        'sample_id': parts[2],
                        'test_code': parts[3],
                        'priority': parts[4],
                        'date_commande': parts[5]
                    })
        
        return resultats
    
    def envoyer_resultats(self, resultats: List[Dict]) -> bool:
        """
        Envoyer des résultats à l'automate (si bidirectionnel).
        Format: O (Order) + R (Result)
        """
        messages = []
        
        for res in resultats:
            # Message O (Order)
            ordre = f"O|1|{res.get('sample_id', '')}|{res.get('test_code', '')}|||||||P"
            messages.append(ordre)
            
            # Message R (Result)
            resultat = f"R|1|{res.get('test_code', '')}|{res.get('valeur', '')}|{res.get('unite', '')}||||F"
            messages.append(resultat)
        
        # Envoyer tous les messages
        for msg in messages:
            self.envoyer_commande(msg)
        
        # Envoyer EOT pour terminer
        self.envoyer_caractere(self.EOT)
        return True
    
    def _calculer_checksum(self, message: str) -> int:
        """Calculer le checksum ASTM (somme des codes ASCII mod 256)."""
        return sum(ord(c) for c in message) % 256
    
    def _verifier_checksum(self, message: str, checksum_str: str) -> bool:
        """Vérifier le checksum d'un message reçu."""
        try:
            checksum_recu = int(checksum_str, 16)
            checksum_calcule = self._calculer_checksum(message)
            return checksum_recu == checksum_calcule
        except ValueError:
            return False
    
    def envoyer_caractere(self, char: str):
        """Envoyer un caractère de contrôle."""
        if self.connection and self.connection.is_open:
            self.connection.write(char.encode())


class HL7Handler(AutomateHandler):
    """
    Handler pour le protocole HL7 v2.x.
    Utilisé pour l'interopérabilité entre systèmes d'information.
    """
    
    # Séparateurs HL7
    FIELD_SEP = '|'
    COMPONENT_SEP = '^'
    REPETITION_SEP = '~'
    ESCAPE_CHAR = '\\'
    SUBCOMPONENT_SEP = '&'
    
    def __init__(self, host: str, port: int, automate_id: Optional[int] = None):
        self.host = host
        self.port = port
        self.automate_id = automate_id
        self.socket = None
    
    def connecter(self) -> bool:
        """Établir la connexion TCP/IP avec le serveur HL7."""
        try:
            import socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(30)
            logger.info(f"Connecté au serveur HL7 sur {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Échec connexion HL7: {e}")
            return False
    
    def deconnecter(self):
        """Fermer la connexion TCP."""
        if self.socket:
            self.socket.close()
            self.socket = None
            logger.info("Déconnecté du serveur HL7")
    
    def envoyer_commande(self, commande: str) -> str:
        """
        Envoyer un message HL7 et recevoir l'accusé de réception.
        Format: <VT>message<FS><CR>
        """
        if not self.socket:
            raise ConnectionError("Non connecté au serveur HL7")
        
        # Encadrer le message HL7
        vt = '\x0B'  # Vertical Tab
        fs = '\x1C'  # File Separator
        cr = '\x0D'  # Carriage Return
        
        trame = f"{vt}{commande}{fs}{cr}"
        self.socket.send(trame.encode())
        
        # Recevoir l'ACK
        reponse = self.socket.recv(4096).decode()
        
        # Extraire le message ACK
        if 'MSH|^~\\&|ACK' in reponse:
            return reponse
        else:
            raise TimeoutError("Pas de ACK reçu")
    
    def recevoir_reponse(self) -> str:
        """Recevoir un message HL7 complet."""
        if not self.socket:
            raise ConnectionError("Non connecté")
        
        data = self.socket.recv(8192).decode()
        
        # Extraire le message entre VT et FS
        vt_pos = data.find('\x0B')
        fs_pos = data.find('\x1C')
        
        if vt_pos != -1 and fs_pos != -1:
            return data[vt_pos + 1:fs_pos]
        else:
            return data
    
    def creer_message_oru(self, resultats: List[Dict]) -> str:
        """
        Créer un message HL7 ORU^R01 (résultats d'observation).
        """
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # MSH - Message Header
        msh = f"MSH|^~\\&|IGORS|LAB|AUTOMATE|SYS|{now}||ORU^R01|MSG{now}|P|2.5"
        
        # PID - Patient Identification (à remplir)
        pid = "PID|1||PATIENT_ID^^^MRN||PATIENT^NAME|||||||||||"
        
        # ORC - Common Order
        orc = f"ORC|RE||||CM|{now}"
        
        # OBX - Observation Result (un par résultat)
        obx_messages = []
        for i, res in enumerate(resultats, 1):
            obx = (
                f"OBX|{i}|NM|{res.get('code', '')}^{res.get('nom', '')}^LN|"
                f"|{res.get('valeur', '')}|{res.get('unite', '')}|"
                f"{res.get('ref_bas', '')}-{res.get('ref_haut', '')}||||F"
            )
            obx_messages.append(obx)
        
        # Assembler le message
        message = '\r'.join([msh, pid, orc] + obx_messages)
        return message
    
    def envoyer_resultats(self, resultats: List[Dict]) -> bool:
        """Envoyer des résultats via HL7."""
        message = self.creer_message_oru(resultats)
        reponse = self.envoyer_commande(message)
        
        # Vérifier que c'est un ACK positif
        if 'AA' in reponse:  # Application Accept
            return True
        else:
            logger.error(f"ACK négatif: {reponse}")
            return False
    
    def parser_resultat_astm_vers_hl7(self, message_astm: str) -> str:
        """
        Convertir un message ASTM en message HL7.
        Utile pour l'intégration avec des SI hospitaliers.
        """
        # Parser le message ASTM
        lignes = message_astm.split('\n')
        resultats = []
        
        for ligne in lignes:
            if ligne.startswith('R|'):  # Ligne résultat ASTM
                parts = ligne.split('|')
                if len(parts) >= 5:
                    resultats.append({
                        'code': parts[2],
                        'nom': parts[2],  # À mapper
                        'valeur': parts[3],
                        'unite': parts[4],
                        'ref_bas': '',
                        'ref_haut': ''
                    })
        
        return self.creer_message_oru(resultats)
