"""
MIDDLEWARE D'IMPRESSION - Restaurant MITAKE
===========================================
Script Python pour gérer l'impression automatique des tickets de commande
à partir de Supabase vers des imprimantes thermiques Epson ESC/POS.

Auteur: Backend & IoT Expert
Date: 2025-11-24
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import json
import random
from dotenv import load_dotenv

# ============================================================================
# DÉTECTION MODE EXE (PyInstaller) - Charge .env depuis le dossier de l'exe
# ============================================================================

def get_app_directory():
    """Retourne le répertoire de l'application (exe ou script)"""
    if getattr(sys, 'frozen', False):
        # Mode PyInstaller (exe)
        return os.path.dirname(sys.executable)
    else:
        # Mode développement (script Python)
        return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_app_directory()
ENV_FILE = os.path.join(APP_DIR, '.env')

# Charge le fichier .env du dossier de l'application
if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)
else:
    # Fallback: cherche .env dans le répertoire courant
    load_dotenv()

# Gestion des imports conditionnels (Windows vs Linux)
try:
    import win32print  # type: ignore
    import win32api    # type: ignore
    WINDOWS_PRINTING = True
except ImportError:
    WINDOWS_PRINTING = False
    print("⚠️ win32print non disponible (exécution sur Linux?)")

# ---------------------------------------------------------------------------
# Import Supabase avec tolérance si non installé en mode mock
# ---------------------------------------------------------------------------
SUPABASE_AVAILABLE = True
try:
    from supabase import create_client, Client  # type: ignore
except Exception:
    # On garde une interface minimale si la lib n'est pas installée
    SUPABASE_AVAILABLE = False
    class Client:  # stub pour hints uniquement
        pass
    def create_client(*_, **__):
        raise RuntimeError("Supabase non installé. Exécute: pip install -r requirements.txt")
    # Pas d'import supplémentaire non gardé (fix: suppression import en double)
try:
    from escpos.printer import Usb, Network, Win32Raw  # type: ignore
    from escpos.exceptions import Error as EscposError  # type: ignore
except Exception:
    # En mode mock ou si librairie absente, on continue
    Usb = Network = Win32Raw = object  # sentinelles
    class EscposError(Exception):
        pass

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Configuration centralisée du système d'impression"""
    
    # Supabase (nettoyage automatique des variables d'environnement)
    SUPABASE_URL = (os.getenv("SUPABASE_URL", "https://votre-projet.supabase.co") or "").strip()
    SUPABASE_KEY = (os.getenv("SUPABASE_KEY", "votre-anon-key-ici") or "").strip()
    
    # Table et colonnes Supabase
    TABLE_NAME = "orders"
    STATUS_PENDING = "pending_print"
    STATUS_PRINTED = "printed"
    
    # Configuration des imprimantes
    # IMPORTANT: Pour trouver les Vendor ID et Product ID sur Windows:
    # 1. Ouvrir le Gestionnaire de périphériques
    # 2. Développer "Imprimantes" ou "Périphériques USB"
    # 3. Clic droit sur l'imprimante Epson > Propriétés
    # 4. Onglet "Détails" > Propriété: "ID matériel"
    # 5. Vous verrez: USB\VID_04B8&PID_0E28 (exemple)
    #    → VID = Vendor ID (0x04b8 pour Epson)
    #    → PID = Product ID (varie selon le modèle)
    
    # Mode d'impression: 'real' (défaut) ou 'mock'
    PRINTER_MODE = os.getenv("PRINTER_MODE", "normal").lower()
    if PRINTER_MODE == 'real':
        PRINTER_MODE = 'normal'

    # DÉTECTION OS WINDOWS
    IS_WINDOWS = (os.name == 'nt')

    # Imprimante CAISSE (Ticket client avec prix)
    PRINTER_CASHIER = {
        # Sur Windows, on force le type 'windows' sauf si on est en mode mock
        "type": "windows" if IS_WINDOWS else os.getenv("PRINTER_CASHIER_TYPE", "network"),
        # Nom exact Windows requis
        "name": os.getenv("PRINTER_CASHIER_NAME", "EPSON TM-T20IV"),
        # Fallback Network/USB (non utilisé si Windows détecté)
        "vendor_id": int(os.getenv("PRINTER_CASHIER_VID", "0x04b8"), 16) if os.getenv("PRINTER_CASHIER_VID") else 0x04b8,
        "product_id": int(os.getenv("PRINTER_CASHIER_PID", "0x0e28"), 16) if os.getenv("PRINTER_CASHIER_PID") else 0x0e28,
        "ip": os.getenv("PRINTER_CASHIER_IP", "192.168.1.100"),
        "port": int(os.getenv("PRINTER_CASHIER_PORT", "9100")),
    }
    
    # Imprimante CUISINE (Ticket cuisine sans prix)
    PRINTER_KITCHEN = {
        "type": "windows" if IS_WINDOWS else os.getenv("PRINTER_KITCHEN_TYPE", "network"),
        # Nom exact Windows pour la 2ème imprimante
        "name": os.getenv("PRINTER_KITCHEN_NAME", "EPSON TM-T20IV Receipt (1)"),
        "vendor_id": int(os.getenv("PRINTER_KITCHEN_VID", "0x04b8"), 16) if os.getenv("PRINTER_KITCHEN_VID") else 0x04b8,
        "product_id": int(os.getenv("PRINTER_KITCHEN_PID", "0x0e29"), 16) if os.getenv("PRINTER_KITCHEN_PID") else 0x0e29,
        "ip": os.getenv("PRINTER_KITCHEN_IP", "192.168.1.101"),
        "port": int(os.getenv("PRINTER_KITCHEN_PORT", "9100")),
    }
    
    # Paramètres généraux
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 5  # secondes
    LOG_FILE = "printer_agent.log"
    
    # Caractères pour la mise en page
    PAPER_WIDTH = 48  # Nombre de caractères (80mm ≈ 48 chars)


# ============================================================================
# CLASSE MOCK POUR SIMULATION D'IMPRESSION
# ============================================================================

class MockPrinter:
    """Simule une imprimante ESC/POS en affichant le ticket dans le terminal.
    Accumule le texte et le formate lors de l'appel à cut().
    Sauvegarde également dans un fichier 'ticket_test.txt'.
    """

    def __init__(self, name: str, width: int = Config.PAPER_WIDTH):
        self.name = name
        self.width = width
        self.buffer: List[str] = []
        self.current_style = {
            "bold": False,
            "wide": 1,
            "high": 1,
            "invert": False,
            "align": "left"
        }

    # Mimic ESC/POS set() signature usage in our code
    def set(self, align='left', bold=False, width=1, height=1, invert=False, **kwargs):
        """Accepte les paramètres standards de python-escpos"""
        self.current_style["align"] = align
        self.current_style["bold"] = bold
        self.current_style["wide"] = width
        self.current_style["high"] = height
        self.current_style["invert"] = invert

    def text(self, data: str):
        # Fragmenter par lignes pour appliquer style individuellement
        lines = data.split('\n')
        for line in lines:
            if line == "":
                self.buffer.append("")
                continue
            styled = self._apply_style(line)
            self.buffer.append(styled)

    def _apply_style(self, line: str) -> str:
        # Largeur/hauteur: on simule en capitalisant + préfixes
        if self.current_style["wide"] > 1 or self.current_style["high"] > 1:
            line = line.upper()
        if self.current_style["bold"]:
            line = f"**{line}**"
        if self.current_style["invert"]:
            line = f"!! {line} !!"
        # Alignement (simple padding)
        if self.current_style["align"] == 'center':
            pad = (self.width - len(line)) // 2
            if pad > 0:
                line = ' ' * pad + line
        elif self.current_style["align"] == 'right':
            pad = self.width - len(line)
            if pad > 0:
                line = ' ' * pad + line
        return line[:self.width]

    def cut(self):
        # Formater et afficher le ticket
        if not self.buffer:
            return
        w = self.width
        border = '+' + '-' * (w + 2) + '+'
        output_lines = [border]
        output_lines.append(f"| {('IMPRIMANTE MOCK: ' + self.name)[:w]:<{w}} |")
        output_lines.append(f"| {datetime.now().strftime('%d/%m/%Y %H:%M:%S'):<{w}} |")
        output_lines.append(border)
        for line in self.buffer:
            output_lines.append(f"| {line:<{w}} |")
        output_lines.append(border)
        ticket_text = '\n'.join(output_lines)
        print(ticket_text)
        # Append dans fichier
        try:
            with open('ticket_test.txt', 'a', encoding='utf-8') as f:
                f.write(ticket_text + '\n\n')
        except Exception as e:
            print(f"[MockPrinter] Impossible d'écrire ticket_test.txt: {e}")
        # Reset buffer
        self.buffer = []

    def close(self):
        # Rien à fermer en mode mock
        pass


# ============================================================================
# LOGGING
# ============================================================================

def setup_logging():
    """Configure le système de logs"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# Log the .env loading information
logger.info("=" * 70)
logger.info("🚀 MIDDLEWARE D'IMPRESSION MITAKE - Démarrage")
logger.info("=" * 70)
if getattr(sys, 'frozen', False):
    logger.info(f"📦 Mode: PyInstaller EXE")
    logger.info(f"📂 Répertoire exe: {APP_DIR}")
else:
    logger.info(f"📝 Mode: Python script")
    logger.info(f"📂 Répertoire script: {APP_DIR}")

logger.info(f"🔧 Fichier .env: {ENV_FILE}")
if os.path.exists(ENV_FILE):
    logger.info(f"✅ Fichier .env trouvé et chargé")
else:
    logger.warning(f"⚠️  Fichier .env non trouvé - utilisation des variables d'environnement ou defaults")

# Listage des imprimantes Windows au démarrage pour débogage
if WINDOWS_PRINTING:
    try:
        logger.info("🖨️  LISTE DES IMPRIMANTES WINDOWS DÉTECTÉES:")
        printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        for p in printers:
            # p est un tuple (flags, description, name, comment)
            # On affiche le nom (index 2) qui est celui à utiliser dans la config
            logger.info(f"   🔹 Nom: '{p[2]}'")
    except Exception as e:
        logger.error(f"❌ Impossible de lister les imprimantes: {e}")

logger.info("=" * 70)


# ============================================================================
# GESTIONNAIRE D'IMPRIMANTES
# ============================================================================

class PrinterManager:
    """Gère la connexion et l'impression sur les imprimantes ESC/POS"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.printer = None
        self.printer_type = config.get("type", "network")
        
    def _scan_usb_devices(self):
        """Analyse les périphériques USB disponibles (Epson: VID 0x04b8)"""
        try:
            import usb.core
            devices = list(usb.core.find(find_all=True, idVendor=0x04b8))
            if not devices:
                logger.warning("⚠️  Aucun périphérique USB Epson trouvé (VID: 0x04b8)")
                return
            logger.info(f"📱 Périphériques USB détectés: {len(devices)}")
            for device in devices:
                logger.info(f"   └─ VID: 0x{device.idVendor:04x}, PID: 0x{device.idProduct:04x}")
        except Exception as e:
            logger.warning(f"⚠️  Impossible de scanner USB: {e}")
    
    def connect(self) -> bool:
        """Établit la connexion réelle ou mock selon PRINTER_MODE."""
        if Config.PRINTER_MODE == 'mock':
            self.printer = MockPrinter(self.config.get('name', 'MockPrinter'))
            logger.info(f"🧪 [MOCK] Imprimante simulée prête: {self.config.get('name', 'MockPrinter')}")
            return True
        try:
            if self.printer_type == "usb":
                return self._connect_usb()
            elif self.printer_type == "network":
                return self._connect_network()
            elif self.printer_type == "windows" and WINDOWS_PRINTING:
                return self._connect_windows()
            else:
                logger.error(f"❌ Type d'imprimante non supporté: {self.printer_type}")
                return False
        except EscposError as e:
            logger.error(f"❌ Erreur connexion imprimante {self.config['name']}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur inattendue connexion: {e}")
            return False
    
    def _connect_usb(self) -> bool:
        """Connexion USB avec détection d'erreurs détaillée"""
        try:
            # Conversion des VID/PID en entiers (formats: 0x04b8 ou 04b8)
            vendor_id = self.config.get("vendor_id", 0x04b8)
            product_id = self.config.get("product_id", 0x0e28)
            
            if isinstance(vendor_id, str):
                vendor_id = int(vendor_id, 16) if vendor_id.startswith("0x") else int(vendor_id, 16)
            if isinstance(product_id, str):
                product_id = int(product_id, 16) if product_id.startswith("0x") else int(product_id, 16)
            
            self.printer = Usb(vendor_id, product_id)
            logger.info(f"✅ Connecté à l'imprimante USB {self.config['name']} (VID: 0x{vendor_id:04x}, PID: 0x{product_id:04x})")
            return True
        except EscposError as e:
            logger.error(f"❌ USB: Imprimante non trouvée - VID: 0x{vendor_id:04x}, PID: 0x{product_id:04x}")
            logger.error(f"   Erreur: {e}")
            logger.error(f"   💡 Solutions:")
            logger.error(f"      1. Vérifier que l'imprimante est branchée en USB")
            logger.error(f"      2. Vérifier les VID/PID dans .env (Gestionnaire périphériques > Propriétés)")
            logger.error(f"      3. Installer libusb-win32 sur Windows (https://sourceforge.net/projects/libusb-win32/)")
            self._scan_usb_devices()
            return False
        except Exception as e:
            logger.error(f"❌ Erreur USB: {e}")
            self._scan_usb_devices()
            return False
    
    def _connect_network(self) -> bool:
        """Connexion réseau avec validation d'IP/port"""
        try:
            ip = self.config.get("ip")
            port = self.config.get("port", 9100)
            
            if not ip:
                logger.error(f"❌ Réseau: Adresse IP manquante dans .env")
                logger.error(f"   Ajouter: PRINTER_KITCHEN_IP=192.168.1.xxx")
                return False
            
            logger.info(f"📡 Tentative de connexion: {ip}:{port}")
            self.printer = Network(ip, port=port)
            logger.info(f"✅ Connecté à l'imprimante réseau {self.config['name']} ({ip}:{port})")
            return True
        except EscposError as e:
            logger.error(f"❌ Réseau: Impossible de joindre {ip}:{port}")
            logger.error(f"   Erreur: {e}")
            logger.error(f"   💡 Solutions:")
            logger.error(f"      1. Vérifier l'adresse IP: ping {ip}")
            logger.error(f"      2. Vérifier que le port est bien 9100 (port ESC/POS standard)")
            logger.error(f"      3. Vérifier que l'imprimante a une IP statique")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur réseau: {e}")
            return False
    
    def _connect_windows(self) -> bool:
        """Connexion Windows (Win32Raw) avec vérification de disponibilité"""
        try:
            if not WINDOWS_PRINTING:
                logger.error(f"❌ Windows: pywin32 n'est pas installé")
                logger.error(f"   Installer: pip install pywin32")
                return False
            
            printer_name = self.config.get("name")
            if not printer_name:
                logger.error(f"❌ Windows: Nom d'imprimante manquant dans .env")
                logger.error(f"   Ajouter: PRINTER_CASHIER_NAME=NOM_IMPRIMANTE")
                return False
            
            self.printer = Win32Raw(printer_name)
            logger.info(f"✅ Connecté à l'imprimante Windows {printer_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Windows: Impossible de connecter '{self.config.get('name')}'")
            logger.error(f"   Erreur: {e}")
            logger.error(f"   💡 Solutions:")
            logger.error(f"      1. Vérifier que l'imprimante est disponible dans Paramètres > Imprimantes")
            logger.error(f"      2. Vérifier le nom exact de l'imprimante")
            logger.error(f"      3. Vérifier que pywin32 est installé: pip list | grep pywin32")
            return False
    
    def disconnect(self):
        """Ferme la connexion avec l'imprimante"""
        if Config.PRINTER_MODE == 'mock':
            # Pas de déconnexion nécessaire
            return
        try:
            if self.printer:
                self.printer.close()
                logger.info(f"🔌 Déconnexion imprimante {self.config['name']}")
        except Exception as e:
            logger.warning(f"⚠️ Erreur déconnexion: {e}")
    
    def print_raw(self, commands: callable, retry: int = Config.RETRY_ATTEMPTS) -> bool:
        """
        Exécute les commandes d'impression avec gestion des erreurs
        Args:
            commands: Fonction contenant les commandes ESC/POS
            retry: Nombre de tentatives
        Returns: True si impression réussie
        """
        if Config.PRINTER_MODE == 'mock':
            try:
                if not self.printer:
                    self.connect()
                commands(self.printer)
                logger.info(f"🧪 [MOCK] Ticket simulé pour {self.config.get('name', 'MockPrinter')}")
                return True
            except Exception as e:
                logger.error(f"❌ [MOCK] Erreur simulation impression: {e}")
                return False
        # Mode réel
        for attempt in range(retry):
            try:
                if not self.printer and not self.connect():
                    raise Exception("Impossible de se connecter à l'imprimante")
                commands(self.printer)
                logger.info(f"✅ Impression réussie sur {self.config['name']}")
                return True
            except EscposError as e:
                logger.error(f"❌ Erreur impression (tentative {attempt+1}/{retry}): {e}")
                self.disconnect()
                if attempt < retry - 1:
                    time.sleep(Config.RETRY_DELAY)
            except Exception as e:
                logger.error(f"❌ Erreur inattendue (tentative {attempt+1}/{retry}): {e}")
                self.disconnect()
                if attempt < retry - 1:
                    time.sleep(Config.RETRY_DELAY)
        return False


# ============================================================================
# GÉNÉRATEURS DE TICKETS
# ============================================================================

class TicketGenerator:
    """Génère le contenu des tickets pour caisse et cuisine"""
    
    @staticmethod
    def _center(text: str, width: int = Config.PAPER_WIDTH) -> str:
        """Centre un texte sur la largeur du ticket"""
        return text.center(width)
    
    @staticmethod
    def _line(char: str = "-", width: int = Config.PAPER_WIDTH) -> str:
        """Génère une ligne de séparation"""
        return char * width
    
    @staticmethod
    def _format_price(price: float) -> str:
        """Formate un prix en euros"""
        return f"{price:.2f}€"
    
    @staticmethod
    def print_cashier_ticket(printer, order: Dict):
        """
        Génère le ticket CAISSE avec tous les détails et prix
        Args:
            printer: Instance de l'imprimante ESC/POS
            order: Dictionnaire contenant les données de commande
        """
        try:
            # En-tête
            printer.set(align='center', bold=True, width=2, height=2)
            printer.text("RESTAURANT MITAKE\n")
            printer.set(align='center', bold=False)
            printer.text("Ticket de Caisse\n")
            printer.text(TicketGenerator._line("=") + "\n")
            
            # Informations commande
            printer.set(align='left', bold=False)
            printer.text(f"Commande N°: {order.get('order_number', 'N/A')}\n")
            printer.text(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            printer.text(f"Client: {order.get('customer_name', 'Anonyme')}\n")
            
            if order.get('customer_phone'):
                printer.text(f"Tel: {order['customer_phone']}\n")
            
            printer.text(TicketGenerator._line("-") + "\n")
            
            # Produits
            items = order.get('items', [])
            total = 0.0
            
            for item in items:
                name = item.get('name', 'Produit')
                quantity = item.get('quantity', 1)
                price = item.get('price', 0.0)
                subtotal = quantity * price
                total += subtotal
                
                # Nom du produit et prix
                printer.set(bold=True)
                printer.text(f"{quantity}x {name}\n")
                printer.set(bold=False, align='right')
                printer.text(f"{TicketGenerator._format_price(subtotal)}\n")
                printer.set(align='left')
                
                # Options/Modifications
                if item.get('options'):
                    for option in item['options']:
                        printer.text(f"  + {option}\n")
                
                # Commentaire
                if item.get('comment'):
                    printer.text(f"  Note: {item['comment']}\n")
                
                printer.text("\n")
            
            # Total
            printer.text(TicketGenerator._line("-") + "\n")
            printer.set(bold=True, width=2, height=2, align='right')
            printer.text(f"TOTAL: {TicketGenerator._format_price(total)}\n")
            printer.set(bold=False, width=1, height=1, align='center')
            
            # Statut de paiement
            printer.text("\n")
            payment_status = order.get('payment_status', 'pending')
            if payment_status == 'paid':
                printer.set(bold=True)
                printer.text("✓ PAYÉ EN LIGNE\n")
            else:
                printer.set(bold=True, invert=True)
                printer.text("  À PAYER EN CAISSE  \n")
            
            printer.set(bold=False, invert=False)
            printer.text("\n")
            printer.text(TicketGenerator._line("=") + "\n")
            printer.text("Merci de votre visite !\n")
            printer.text(TicketGenerator._line("=") + "\n")
            
            # Coupe du papier
            printer.text("\n\n")
            printer.cut()
            
        except Exception as e:
            logger.error(f"❌ Erreur génération ticket caisse: {e}")
            raise
    
    @staticmethod
    def print_kitchen_ticket(printer, order: Dict):
        """
        Génère le ticket CUISINE avec nom en GROS, options, sans prix
        Args:
            printer: Instance de l'imprimante ESC/POS
            order: Dictionnaire contenant les données de commande
        """
        try:
            # En-tête
            printer.set(align='center', bold=True, width=2, height=2)
            printer.text("*** CUISINE ***\n")
            printer.set(bold=False, width=1, height=1)
            printer.text(TicketGenerator._line("=") + "\n")
            
            # Numéro de commande en TRÈS GROS
            printer.set(align='center', bold=True, width=3, height=3)
            printer.text(f"N° {order.get('order_number', '???')}\n")
            printer.set(width=1, height=1)
            printer.text("\n")
            
            # Heure
            printer.set(align='center', bold=False)
            printer.text(f"{datetime.now().strftime('%H:%M')}\n")
            printer.text(TicketGenerator._line("-") + "\n")
            
            # Produits
            items = order.get('items', [])
            
            for idx, item in enumerate(items, 1):
                name = item.get('name', 'Produit')
                quantity = item.get('quantity', 1)
                
                # Nom du produit en TRÈS GROS
                printer.set(align='left', bold=True, width=2, height=2)
                printer.text(f"{quantity}x {name}\n")
                printer.set(width=1, height=1, bold=False)
                
                # Options/Modifications en gras
                if item.get('options'):
                    printer.set(bold=True)
                    for option in item['options']:
                        printer.text(f"  >> {option}\n")
                    printer.set(bold=False)
                
                # Commentaire en surbrillance si présent
                if item.get('comment'):
                    printer.set(invert=True, bold=True)
                    printer.text(f"  NOTE: {item['comment'].upper()}\n")
                    printer.set(invert=False, bold=False)
                
                printer.text("\n")
                
                # Séparateur entre produits
                if idx < len(items):
                    printer.text(TicketGenerator._line("-") + "\n")
            
            # Pied de page
            printer.set(align='center')
            printer.text(TicketGenerator._line("=") + "\n")
            printer.text("\n\n")
            
            # Coupe automatique du papier
            printer.cut()
            
        except Exception as e:
            logger.error(f"❌ Erreur génération ticket cuisine: {e}")
            raise


# ============================================================================
# GESTIONNAIRE SUPABASE
# ============================================================================

class SupabaseManager:
    """Gère la connexion et les interactions avec Supabase"""
    
    def __init__(self):
        if not SUPABASE_AVAILABLE:
            if Config.PRINTER_MODE == 'mock':
                logger.warning("⚠️ Supabase non installé. Mode mock actif: les événements Realtime ne fonctionneront pas. Installe avec 'pip install -r requirements.txt'.")
            else:
                logger.error("❌ Supabase non installé. Exécute 'pip install -r requirements.txt'.")
                raise RuntimeError("Supabase library missing")
        else:
            self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            logger.info("✅ Connexion à Supabase établie")
    
    def get_pending_orders(self) -> List[Dict]:
        """Récupère les commandes en attente d'impression"""
        if not SUPABASE_AVAILABLE:
            # Mode dégradé: retourne une commande factice pour test manuel
            logger.info("🧪 [MOCK] Génération d'une commande factice locale (Supabase absent)")
            return [{
                "id": random.randint(1000, 9999),
                "order_number": f"LOCAL-{int(time.time())}",
                "customer_name": "Client Local",
                "payment_status": "paid",
                "items": [
                    {"name": "Ramen Shoyu", "quantity": 1, "price": 11.5, "options": ["Extra œuf"], "comment": "Moins salé"},
                    {"name": "Gyoza", "quantity": 2, "price": 6.0, "options": [], "comment": None}
                ],
                "status": Config.STATUS_PENDING
            }]
        try:
            response = self.client.table(Config.TABLE_NAME)\
                .select("*")\
                .eq("status", Config.STATUS_PENDING)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"❌ Erreur récupération commandes: {e}")
            return []
    
    def mark_as_printed(self, order_id: int) -> bool:
        """Marque une commande comme imprimée"""
        if not SUPABASE_AVAILABLE:
            logger.info(f"🧪 [MOCK] Commande {order_id} marquée comme imprimée (local)")
            return True
        try:
            # Mise à jour du statut uniquement (colonne printed_at optionnelle)
            self.client.table(Config.TABLE_NAME)\
                .update({"status": Config.STATUS_PRINTED})\
                .eq("id", order_id)\
                .execute()
            logger.info(f"✅ Commande {order_id} marquée comme imprimée")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour statut: {e}")
            return False
    
    def subscribe_to_new_orders(self, callback):
        """
        S'abonne aux nouvelles commandes (polling simple sans WebSocket)
        Args:
            callback: Fonction appelée lors d'une nouvelle insertion
        """
        if not SUPABASE_AVAILABLE:
            logger.error("❌ Supabase non installé. Impossible de s'abonner aux commandes. Installe: pip install -r requirements.txt")
            logger.info("⏳ En attente de commandes... (Aucune ne sera traitée sans Supabase)")
            return None
        
        # Polling simple : vérifie les commandes toutes les 2 secondes
        last_check = time.time()
        
        class PollingChannel:
            def __init__(self, manager, cb):
                self.manager = manager
                self.cb = cb
                self.last_id = None
                
            def run_forever(self):
                logger.info(f"🔔 Écoute activée sur '{Config.TABLE_NAME}' (polling)")
                while True:
                    try:
                        response = self.manager.client.table(Config.TABLE_NAME)\
                            .select("*")\
                            .eq("status", Config.STATUS_PENDING)\
                            .execute()
                        
                        for order in response.data:
                            if self.last_id is None or order.get('id') > self.last_id:
                                if order.get('status') == Config.STATUS_PENDING:
                                    logger.info(f"📩 Nouvelle commande détectée: {order.get('order_number')}")
                                    self.cb(order)
                                    self.last_id = order.get('id')
                        
                        time.sleep(2)  # Polling toutes les 2 secondes
                        
                    except Exception as e:
                        logger.error(f"❌ Erreur polling: {e}")
                        time.sleep(5)
            
            def close(self):
                pass
        
        return PollingChannel(self, callback)


# ============================================================================
# ORCHESTRATEUR PRINCIPAL
# ============================================================================

class PrinterAgent:
    """Orchestrateur principal du système d'impression"""
    
    def __init__(self):
        self.supabase = SupabaseManager()
        self.cashier_printer = PrinterManager(Config.PRINTER_CASHIER)
        self.kitchen_printer = PrinterManager(Config.PRINTER_KITCHEN)
        logger.info("🚀 PrinterAgent initialisé")
    
    def process_order(self, order: Dict):
        """
        Traite une commande: imprime les tickets et met à jour le statut
        Args:
            order: Dictionnaire contenant les données de commande
        """
        order_id = order.get('id')
        order_number = order.get('order_number', 'N/A')
        
        logger.info(f"📄 Traitement commande #{order_number} (ID: {order_id})")
        
        # Impression ticket CAISSE
        cashier_success = self.cashier_printer.print_raw(
            lambda p: TicketGenerator.print_cashier_ticket(p, order)
        )
        
        # Impression ticket CUISINE
        kitchen_success = self.kitchen_printer.print_raw(
            lambda p: TicketGenerator.print_kitchen_ticket(p, order)
        )
        
        # Mise à jour du statut si au moins une impression réussie
        if cashier_success or kitchen_success:
            self.supabase.mark_as_printed(order_id)
            logger.info(f"✅ Commande #{order_number} traitée avec succès")
        else:
            logger.error(f"❌ Échec total impression commande #{order_number}")
    
    def process_pending_orders(self):
        """Traite toutes les commandes en attente au démarrage"""
        logger.info("🔍 Vérification des commandes en attente...")
        pending = self.supabase.get_pending_orders()
        
        if pending:
            logger.info(f"📦 {len(pending)} commande(s) en attente trouvée(s)")
            for order in pending:
                self.process_order(order)
        else:
            logger.info("✓ Aucune commande en attente")
    
    def start_realtime_listening(self):
        """Démarre l'écoute en temps réel des nouvelles commandes"""
        logger.info("🎧 Démarrage de l'écoute en temps réel...")
        
        # Traite d'abord les commandes en attente
        self.process_pending_orders()
        
        # Lance la souscription Realtime
        ws = self.supabase.subscribe_to_new_orders(self.process_order)
        
        if ws:
            logger.info("✅ Système d'impression actif - En attente de commandes...")
            logger.info("Press Ctrl+C pour arrêter")
            try:
                ws.run_forever()  # Boucle WebSocket (bloquant)
            except KeyboardInterrupt:
                logger.info("\n🛑 Arrêt du système demandé")
                ws.close()
                self.shutdown()
        else:
            logger.error("❌ Impossible de démarrer l'écoute Realtime")
            logger.info("⏳ Le script reste actif en attente manuelle...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("\n🛑 Arrêt du système demandé")
                self.shutdown()
    
    def shutdown(self):
        """Arrêt propre du système"""
        logger.info("🔌 Déconnexion des imprimantes...")
        self.cashier_printer.disconnect()
        self.kitchen_printer.disconnect()
        logger.info("👋 PrinterAgent arrêté")


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

def main():
    """Fonction principale"""
    logger.info("=" * 60)
    logger.info("  MIDDLEWARE D'IMPRESSION - RESTAURANT MITAKE")
    logger.info("=" * 60)
    logger.info(f"Démarrage: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info("")
    
    # Vérification de la configuration
    if Config.SUPABASE_URL == "https://votre-projet.supabase.co":
        logger.error("❌ ERREUR: Veuillez configurer SUPABASE_URL dans les variables d'environnement!")
        logger.error("   Définissez les variables: SUPABASE_URL et SUPABASE_KEY")
        sys.exit(1)
    
    # Affichage mode mock
    if Config.PRINTER_MODE == 'mock':
        logger.info("🧪 MODE MOCK ACTIVÉ - Aucune impression physique. Les tickets seront affichés dans le terminal et sauvegardés dans ticket_test.txt")
    # Initialisation et démarrage
    agent = PrinterAgent()
    agent.start_realtime_listening()


if __name__ == "__main__":
    main()
