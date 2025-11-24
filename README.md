# 🖨️ Middleware d'Impression - Restaurant MITAKE

Système d'impression automatique pour tickets de commande (Caisse + Cuisine) connecté à Supabase.

## 📋 Prérequis

### Matériel
- **OS**: Windows 11
- **Imprimantes**: 2x Epson thermiques 80mm (ESC/POS)
- **Connexion**: USB ou Réseau (IP statique recommandée)

### Logiciels
- Python 3.10 ou supérieur
- Pilotes Epson installés
- Connexion internet (pour Supabase)

---

## 🚀 Installation

### 1. Cloner ou télécharger le projet

```bash
cd C:\mitake_printer
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
pip install websocket-client  # (si Realtime ne reçoit rien)
```

**Sur Windows**, installer également:
```bash
pip install pywin32
python Scripts\pywin32_postinstall.py -install
```

### 3. Configurer les variables d'environnement

Copier `.env.example` en `.env` et renseigner:

```env
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre-anon-key
```

### 4. Configuration des imprimantes

#### Option A: Imprimantes RÉSEAU (Recommandé)
1. Attribuer une IP statique à chaque imprimante via son panneau de configuration
2. Modifier dans `printer_agent.py`:

```python
PRINTER_CASHIER = {
    "type": "network",
    "ip": "192.168.1.100",  # IP de l'imprimante caisse
    "port": 9100,
}

PRINTER_KITCHEN = {
    "type": "network",
    "ip": "192.168.1.101",  # IP de l'imprimante cuisine
    "port": 9100,
}
```

#### Option B: Imprimantes USB
1. **Identifier le VID/PID**:
   - Ouvrir le Gestionnaire de périphériques Windows
   - Développer "Imprimantes" ou "Contrôleurs de bus USB"
   - Clic droit sur l'imprimante Epson → **Propriétés**
   - Onglet **Détails** → Propriété: **ID matériel**
   - Noter: `USB\VID_04B8&PID_0E28`
     - `VID` = Vendor ID (0x04b8 pour Epson)
     - `PID` = Product ID (spécifique au modèle)

2. Modifier dans `printer_agent.py`:

```python
PRINTER_CASHIER = {
    "type": "usb",
    "vendor_id": 0x04b8,  # VID trouvé
    "product_id": 0x0e28, # PID trouvé
}
```

#### Option C: Imprimantes Windows (via nom système)
```python
PRINTER_CASHIER = {
    "type": "windows",
    "name": "EPSON TM-T88V Receipt",  # Nom exact dans Windows
}
```

Pour trouver le nom:
```bash
python -c "import win32print; print(win32print.EnumPrinters(2))"
```

---

## 🧪 Mode MOCK (Sans imprimantes)

Permet de tester la chaîne Supabase → Script Python → Génération de ticket sans matériel.

### Activer
```bash
export SUPABASE_URL="https://votre-projet.supabase.co"
export SUPABASE_KEY="votre-anon-key"
export PRINTER_MODE=mock
python3 printer_agent.py
```

### Comportement
- Les tickets s'affichent dans le terminal (ASCII encadré)
- Ils sont sauvegardés dans `ticket_test.txt`
- Si Supabase n'est pas installé, des commandes factices locales sont générées périodiquement

### Insertion rapide de commande de test (Node)
```bash
npm install @supabase/supabase-js dotenv
node test_insert.js
```

### Vérifier Realtime WebSocket
```bash
sudo apt-get install -y websocat
websocat "wss://votre-projet.supabase.co/realtime/v1/websocket?apikey=$SUPABASE_KEY&vsn=1.0.0"
```
Tu dois voir des heartbeats réguliers.

Si rien ne s'affiche quand tu insères une commande:
1. Vérifie `SUPABASE_URL` & `SUPABASE_KEY`
2. Installe `websocket-client`
3. Active Realtime dans le dashboard Supabase
4. Vérifie RLS/policies

---

---

## 🎯 Structure de la base de données Supabase

### Table `orders`

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending_print',
    customer_name VARCHAR(100),
    customer_phone VARCHAR(20),
    payment_status VARCHAR(20) DEFAULT 'pending',
    items JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    printed_at TIMESTAMP
);
```

### Format du champ `items` (JSONB)

```json
[
    {
        "name": "Ramen Miso",
        "quantity": 2,
        "price": 12.50,
        "options": ["Extra chashu", "Sans oignons"],
        "comment": "Bien chaud SVP"
    },
    {
        "name": "Gyoza",
        "quantity": 1,
        "price": 6.00,
        "options": [],
        "comment": null
    }
]
```

### Exemple d'insertion (pour tester)

```sql
INSERT INTO orders (order_number, customer_name, payment_status, items)
VALUES (
    'CMD-2025-001',
    'Jean Dupont',
    'paid',
    '[
        {
            "name": "Ramen Tonkotsu",
            "quantity": 1,
            "price": 13.50,
            "options": ["Extra œuf"],
            "comment": "Épicé niveau 3"
        }
    ]'::jsonb
);
```

---

## ▶️ Utilisation

### Lancer le script

```bash
python printer_agent.py
```

### Comportement attendu

1. ✅ Connexion à Supabase
2. 🔍 Traitement des commandes en attente (`status = 'pending_print'`)
3. 🎧 Écoute en temps réel des nouvelles insertions
4. 🖨️ Impression automatique:
   - **Ticket CAISSE**: Client, produits, prix, total, statut paiement
   - **Ticket CUISINE**: Produits en GROS, options, commentaires, SANS prix
5. ✔️ Mise à jour du statut → `printed`

### Arrêter le script

Appuyer sur `Ctrl+C`

---

## 🧪 Tests

### 1. Test de connexion aux imprimantes

```python
# Créer un fichier test_printers.py
from printer_agent import PrinterManager, Config

cashier = PrinterManager(Config.PRINTER_CASHIER)
if cashier.connect():
    print("✅ Imprimante CAISSE OK")
    cashier.disconnect()
else:
    print("❌ Échec connexion CAISSE")

kitchen = PrinterManager(Config.PRINTER_KITCHEN)
if kitchen.connect():
    print("✅ Imprimante CUISINE OK")
    kitchen.disconnect()
else:
    print("❌ Échec connexion CUISINE")
```

### 2. Test d'impression simple

```python
from escpos.printer import Network

p = Network("192.168.1.100")
p.text("Test impression\n")
p.cut()
p.close()
```

---

## 📊 Logs

Les logs sont sauvegardés dans `printer_agent.log`:

```
2025-11-23 14:30:15 - INFO - ✅ Connexion à Supabase établie
2025-11-23 14:30:16 - INFO - ✅ Connecté à l'imprimante réseau 192.168.1.100
2025-11-23 14:30:45 - INFO - 📩 Nouvelle commande détectée: CMD-2025-042
2025-11-23 14:30:47 - INFO - ✅ Impression réussie sur Epson_Caisse
2025-11-23 14:30:48 - INFO - ✅ Commande #CMD-2025-042 traitée avec succès
```

---

## ⚙️ Configuration avancée

### Modifier la largeur du papier

Dans `printer_agent.py`:

```python
class Config:
    PAPER_WIDTH = 48  # 48 caractères pour 80mm
                      # 32 caractères pour 58mm
```

### Désactiver la coupe automatique

Dans `TicketGenerator.print_kitchen_ticket()`:

```python
# Commenter cette ligne:
# printer.cut()
```

### Changer le nombre de tentatives

```python
class Config:
    RETRY_ATTEMPTS = 5  # 3 par défaut
    RETRY_DELAY = 10    # 5 secondes par défaut
```

---

## 🐛 Dépannage

### Erreur: "Could not find libusb"
**Solution**: Installer libusb-win32
- Télécharger: https://sourceforge.net/projects/libusb-win32/
- Ou utiliser des imprimantes réseau

### Erreur: "Access denied" (USB)
**Solution**: Exécuter PowerShell en **Administrateur**

### Erreur: "Connection refused" (Réseau)
1. Vérifier l'IP: `ping 192.168.1.100`
2. Vérifier le port (9100 par défaut)
3. Désactiver temporairement le pare-feu Windows

### L'imprimante n'imprime pas
1. Vérifier qu'elle est allumée et a du papier
2. Tester avec un document Windows
3. Réinstaller les pilotes Epson

### Le script ne détecte pas les nouvelles commandes
1. Vérifier la connexion internet
2. Vérifier que le Realtime est activé dans Supabase:
   - Dashboard → Settings → API → Realtime: **Enabled**
3. Vérifier les logs Supabase pour les erreurs

---

## 🔒 Sécurité

- ⚠️ **Ne jamais commiter le fichier `.env`**
- Utiliser la clé `anon` de Supabase (publique)
- Configurer les Row Level Security (RLS) dans Supabase:

```sql
-- Autoriser uniquement la lecture des commandes
CREATE POLICY "Allow read orders" ON orders
FOR SELECT USING (true);

-- Autoriser uniquement la mise à jour du statut
CREATE POLICY "Allow update status" ON orders
FOR UPDATE USING (true)
WITH CHECK (status IN ('pending_print', 'printed'));
```

---

## 📞 Support

Pour toute question:
1. Consulter les logs: `printer_agent.log`
2. Vérifier la configuration dans `printer_agent.py`
3. Tester les imprimantes manuellement

---

## 📝 Licence

Développé pour Restaurant MITAKE - 2025

---

**Bon service ! 🍜**
