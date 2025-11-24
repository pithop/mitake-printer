# 📖 MITAKE PRINT MIDDLEWARE - DOCUMENTATION COMPLÈTE

**Status:** ✅ Production Ready  
**Date:** 2025-11-24  
**Version:** 1.0.0

---

## 📚 TABLE DES MATIÈRES

1. [Vue d'ensemble](#vue-densemble)
2. [Installation rapide](#installation-rapide)
3. [Configuration](#configuration)
4. [Guide de déploiement Windows](#guide-de-déploiement-windows)
5. [Dépannage d'urgence](#dépannage-durgence)
6. [Référence technique](#référence-technique)

---

## 🎯 Vue d'ensemble

### Qu'est-ce que c'est?
Middleware Python qui gère l'impression automatique des tickets de commande depuis Supabase vers des imprimantes thermales Epson ESC/POS sur Windows 11.

### Flux de travail
```
React App (Website)
    ↓
Supabase Database
    ↓
Python Middleware (printer_agent.py)
    ↓
Imprimante Thermale (USB ou Réseau)
    ↓
Ticket Imprimé ✓
```

### Caractéristiques principales
- ✅ Support USB, Réseau, et Windows natif
- ✅ Configuration externe (.env) - pas de recompilation requise
- ✅ Mode mock pour tester sans imprimante
- ✅ Messages d'erreur détaillés avec solutions
- ✅ Logs complets (console + fichier)
- ✅ Tickets caisse (avec prix) et cuisine (sans prix)
- ✅ Déploiement automatisé GitHub Actions

---

## ⚡ Installation rapide

### Étape 1: Prérequis
- Windows 11 (ou Windows 10)
- Python 3.10+ (ou utiliser l'EXE fourni)
- Supabase (compte + clés API)
- Imprimante Epson thermale (optionnel pour tester)

### Étape 2: Télécharger & Extraire
```powershell
# Option A: GitHub Actions
# 1. Aller à GitHub Actions
# 2. Télécharger mitake_printer_windows_bundle.zip
# 3. Extraire dans C:\Mitake\

# Option B: Clone du repo
git clone https://github.com/idriss/mitake_script.git
cd mitake_script
```

### Étape 3: Configurer .env
```powershell
# Copier le template
copy .env.example .env

# Éditer .env avec Notepad
notepad .env
```

**Remplir ces variables (OBLIGATOIRES):**
```env
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
PRINTER_MODE=normal
```

**Pour imprimante réseau:**
```env
PRINTER_CASHIER_TYPE=network
PRINTER_CASHIER_IP=192.168.1.100
PRINTER_CASHIER_PORT=9100

PRINTER_KITCHEN_TYPE=network
PRINTER_KITCHEN_IP=192.168.1.101
PRINTER_KITCHEN_PORT=9100
```

### Étape 4: Lancer
```powershell
# Avec EXE (recommandé)
.\mitake_printer.exe

# Ou avec Python
python printer_agent.py
```

**Vous devriez voir:**
```
======================================================================
🚀 MIDDLEWARE D'IMPRESSION MITAKE - Démarrage
======================================================================
📂 Répertoire exe: C:\Users\Chef\Desktop
✅ Fichier .env trouvé et chargé
✅ Connecté à l'imprimante réseau Caisse (192.168.1.100:9100)
✅ Connecté à l'imprimante réseau Cuisine (192.168.1.101:9100)
⏳ En attente de nouvelles commandes...
```

---

## ⚙️ Configuration

### Fichier .env - Toutes les variables

```env
# ============================================================================
# SUPABASE (Base de données)
# ============================================================================
SUPABASE_URL=https://qrbqeyqvqzaltxmcyyuo.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ============================================================================
# IMPRIMANTE CAISSE (Tickets avec prix et statut paiement)
# ============================================================================
PRINTER_CASHIER_TYPE=network          # Options: "network", "usb", "windows"
PRINTER_CASHIER_IP=192.168.1.100      # Pour réseau
PRINTER_CASHIER_PORT=9100             # Port ESC/POS standard
# PRINTER_CASHIER_VENDOR_ID=0x04b8    # Pour USB
# PRINTER_CASHIER_PRODUCT_ID=0x0e28   # Pour USB
# PRINTER_CASHIER_NAME=EPSON TM-m30   # Pour Windows

# ============================================================================
# IMPRIMANTE CUISINE (Tickets sans prix, commandes uniquement)
# ============================================================================
PRINTER_KITCHEN_TYPE=network
PRINTER_KITCHEN_IP=192.168.1.101
PRINTER_KITCHEN_PORT=9100

# ============================================================================
# MODE (Simulation ou production)
# ============================================================================
PRINTER_MODE=normal
# Changer à "mock" pour tester sans imprimante (affiche ASCII art)
```

### Type de connexion: Décider lequel utiliser

**RÉSEAU (Recommandé - 80% des cas):**
```env
PRINTER_CASHIER_TYPE=network
PRINTER_CASHIER_IP=192.168.1.100
PRINTER_CASHIER_PORT=9100
```
- ✅ Plus stable
- ✅ Pas de pilotes USB complexes
- ✅ Configurable depuis n'importe quel PC

**USB (Pour imprimantes branchées en USB):**
```env
PRINTER_CASHIER_TYPE=usb
PRINTER_CASHIER_VENDOR_ID=0x04b8
PRINTER_CASHIER_PRODUCT_ID=0x0e28
```
- Comment trouver VID/PID:
  1. Brancher l'imprimante USB
  2. Ouvrir Gestionnaire de périphériques
  3. Clic droit imprimante → Propriétés
  4. Onglet "Détails" → "ID matériel"
  5. Chercher: `USB\VID_04B8&PID_0E28`
  6. Mettre dans .env: `PRINTER_CASHIER_VENDOR_ID=0x04b8`

**WINDOWS (Imprimante ajoutée dans Paramètres):**
```env
PRINTER_CASHIER_TYPE=windows
PRINTER_CASHIER_NAME=EPSON TM-m30
```

### Mode MOCK (Pour tester sans imprimante)

```env
PRINTER_MODE=mock
```

Affichage dans la console:
```
╔════════════════════════════════════════╗
║       ** RESTAURANT MITAKE **          ║
║  CMD-12345 | Pierre Martin             ║
║  2x Ramen  ......................... 14€ ║
║  TOTAL: ....................... 14.00€ ║
║  ✓ PAYÉ EN LIGNE                       ║
╚════════════════════════════════════════╝
```

---

## 🪟 Guide de déploiement Windows

### Jour -1: Préparation (30 min)

1. **Télécharger l'EXE**
   ```
   GitHub → Actions → Dernière build (vert ✅)
   → Télécharger mitake_printer_windows_bundle.zip
   ```

2. **Extraire et vérifier**
   ```
   C:\Mitake\
   ├── mitake_printer.exe ✓
   ├── .env ✓
   └── README.md ✓
   ```

3. **Configurer .env**
   - Ouvrir `.env` avec Notepad
   - Remplir `SUPABASE_URL` et `SUPABASE_KEY`
   - Remplir les IPs des imprimantes
   - Enregistrer (Ctrl+S)

### Jour 0: Test et déploiement (1-2 heures avant ouverture)

**Test 1: Mode MOCK (5 min)**
```
1. Modifier .env: PRINTER_MODE=mock
2. Lancer: mitake_printer.exe
3. Attendre: "⏳ En attente de nouvelles commandes..."
4. Fermer
```

**Test 2: Mode RÉEL (10 min)**
```
1. Allumer les imprimantes (15 min avant)
2. Modifier .env: PRINTER_MODE=normal
3. Lancer: mitake_printer.exe
4. Vérifier logs: "✅ Connecté à l'imprimante..."
5. Insérer test dans Supabase:
   INSERT INTO orders (order_number, customer_name, items, status, payment_status)
   VALUES ('TEST-001', 'Test', '[{"name":"Ramen","price":12}]'::jsonb, 'pending_print', 'online');
6. Attendre: Ticket doit imprimer < 5 sec
```

**GO/NO-GO Checklist:**
- [ ] Ticket caisse imprime correctement
- [ ] Ticket cuisine imprime correctement
- [ ] Temps de réaction < 5 secondes
- [ ] Aucune erreur rouge dans logs
- [ ] .env est chargé ("✅ Fichier .env trouvé")

### Service en direct

- Lancer `mitake_printer.exe` le matin
- Laisser ouvert en arrière-plan
- Consulter `GUIDE_URGENCE.md` si problème

---

## 🆘 Dépannage d'urgence

### ❌ Erreur: "Impossible de joindre 192.168.1.100:9100"

**Cause:** L'imprimante réseau est offline ou IP incorrecte

**Fix (< 2 min):**
```powershell
# 1. Vérifier l'IP
ping 192.168.1.100
# Doit répondre "Bytes=32" (pas "Request timed out")

# 2. Si timeout:
#    - Vérifier que l'imprimante est allumée
#    - Vérifier l'IP réelle sur le panneau imprimante
#    - Mettre à jour .env
#    - Relancer exe
```

### ❌ Erreur: "USB: Imprimante non trouvée"

**Cause:** Imprimante USB non branchée ou VID/PID incorrect

**Fix (< 2 min):**
```
1. Vérifier que l'imprimante USB est branchée
2. Ouvrir Gestionnaire de périphériques
3. Vérifier VID/PID (voir section Configuration)
4. Mettre à jour .env
5. Relancer exe
```

### ❌ Le script ne démarre pas: "ModuleNotFoundError"

**Cause:** Dépendances Python manquantes

**Fix:**
```powershell
# Réinstaller
pip install -r requirements.txt

# Ou utiliser l'EXE (recommandé - tout inclus)
.\mitake_printer.exe
```

### ❌ .env introuvable

**Cause:** Fichier `.env` n'est pas dans le même dossier que l'exe

**Fix:**
```
1. Créer fichier .env à côté de mitake_printer.exe
2. Copier le contenu de .env.example
3. Éditer avec vos paramètres
4. Enregistrer
5. Relancer exe
```

### 🟢 Le script fonctionne mais rien ne s'imprime

**Checklist:**
1. La commande arrive-t-elle dans Supabase?
   - Vérifier directement dans Supabase console
   - Status doit être `pending_print`
2. Le script détecte-t-il la commande?
   - Chercher dans logs: "📩 Nouvelle commande détectée"
3. L'imprimante est-elle connectée?
   - Vérifier: "✅ Connecté à l'imprimante..."

**Solution de dernier recours:**
```
1. Fermer exe (Ctrl+C)
2. Redémarrer ordinateur
3. Redémarrer imprimante (éteindre 10 sec)
4. Relancer exe
```

---

## 📚 Référence technique

### Architecture

```
┌─────────────────────────────────────────────────────┐
│           printer_agent.py (851 lignes)             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Config:                                            │
│  ├─ Supabase URL/Key                               │
│  ├─ Imprimante Caisse (USB/Réseau/Windows)        │
│  └─ Imprimante Cuisine (USB/Réseau/Windows)       │
│                                                     │
│  PrinterManager:                                    │
│  ├─ connect() → Établit connexion                  │
│  ├─ _connect_usb()                                 │
│  ├─ _connect_network()                             │
│  ├─ _connect_windows()                             │
│  └─ print_raw() → Envoie à l'imprimante            │
│                                                     │
│  TicketGenerator:                                   │
│  ├─ print_cashier_ticket() → Ticket client         │
│  └─ print_kitchen_ticket() → Ticket cuisine        │
│                                                     │
│  SupabaseManager:                                   │
│  ├─ get_pending_orders() → Récupère commandes      │
│  └─ update_order_status() → Marque imprimé         │
│                                                     │
│  PrinterAgent:                                      │
│  └─ run() → Boucle principale (polling 2s)         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Schéma Supabase requis

**Table: `orders`**
```sql
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_number VARCHAR(50) NOT NULL,
  customer_name VARCHAR(100),
  items JSONB NOT NULL,
  status VARCHAR(50) DEFAULT 'pending_print',
  payment_status VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Format JSON des commandes

```json
{
  "order_number": "CMD-12345",
  "customer_name": "Pierre Martin",
  "items": [
    {
      "name": "Ramen",
      "quantity": 2,
      "price": 12.50,
      "options": ["Bouillon chaud", "Œuf cuit dur"]
    },
    {
      "name": "Bière",
      "quantity": 1,
      "price": 5.00,
      "options": []
    }
  ],
  "status": "pending_print",
  "payment_status": "online"
}
```

### Variables de configuration Python

**printer_agent.py - Config class**
```python
class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "...")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "...")
    PRINTER_MODE = os.getenv("PRINTER_MODE", "normal")  # "normal" ou "mock"
    RETRY_ATTEMPTS = 3                                   # Tentatives connexion
    RETRY_DELAY = 5                                      # Délai entre tentatives (sec)
    PAPER_WIDTH = 48                                     # Chars par ligne
```

### Fichiers générés

- `printer_agent.log` → Logs de chaque exécution
- `ticket_test.txt` → Exemples de tickets (mode mock)

### Commandes utiles

**Trouver l'IP de l'imprimante réseau:**
```powershell
# Méthode 1: Depuis l'imprimante (PLUS RAPIDE)
# Appuyer sur Menu/Setup sur le panneau imprimante
# Chercher "Network" ou "TCP/IP"
# Noter l'IP affichée

# Méthode 2: Depuis Windows (ping)
ping 192.168.1.100  # Adapter l'IP

# Méthode 3: Scanner toutes les imprimantes
nmap -p 9100 192.168.1.0/24
```

**Tester la connexion:**
```powershell
# Tester que l'imprimante répond
telnet 192.168.1.100 9100
# Si ça se connecte: L'imprimante est là ✓
# Ctrl+] puis quit pour fermer
```

---

## 🔗 Ressources

- **Supabase:** https://supabase.com
- **ESC/POS Protocol:** https://www.epson.com/en/pos/receipt-printers
- **Python-escpos:** https://github.com/python-escpos/python-escpos
- **Support Epson:** https://www.epson.fr/support/printers

---

## 📞 Support rapide

| Problème | Solution | Temps |
|----------|----------|-------|
| Imprimante non trouvée | Vérifier IP/USB/branchement | 2 min |
| Pas d'impression | Vérifier status dans Supabase | 3 min |
| Erreur Python | Réinstaller requirements.txt | 5 min |
| Configuration incorrecte | Reconfigurer .env | 5 min |
| Redémarrage complet | Rebooter ordinateur + imprimante | 3 min |

---

## ✅ Checklist de déploiement

**Avant ouverture du restaurant:**
- [ ] EXE téléchargé et testé
- [ ] .env configuré avec vraies clés
- [ ] Mode MOCK testé
- [ ] Mode RÉEL testé avec commande test
- [ ] Ticket caisse imprime correctement
- [ ] Ticket cuisine imprime correctement
- [ ] Logs montrent "✅ Connecté..."
- [ ] Temps de réaction < 5 secondes

**GO/NO-GO:**
- ✅ GO si tous les points ci-dessus sont OK
- ❌ NO-GO si un seul point échoue

---

## 🎉 Vous êtes prêt!

Tous les outils sont en place. Bonne chance pour le déploiement!

Pour plus de détails techniques, voir `printer_agent.py` (code bien commenté).

_Last Update: 2025-11-24_
