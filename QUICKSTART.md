# 📝 MITAKE PRINT MIDDLEWARE - DÉMARRAGE RAPIDE

## 🎯 Qu'est-ce que c'est?

Système d'impression automatique qui:
1. Récupère les commandes depuis **Supabase**
2. Les envoie à **l'imprimante thermale Epson** (USB ou Réseau)
3. Imprime des tickets **caisse** (avec prix) et **cuisine** (sans prix)

## 📂 Structure du projet

```
mitake_script/
├── printer_agent.py          ← Application Python principale
├── requirements.txt          ← Dépendances Python
├── .env.example              ← Template configuration (COPIER EN .env)
├── .gitignore                ← Fichiers à ignorer en git
├── .github/
│   └── workflows/
│       └── build.yml         ← GitHub Actions (build auto sur Windows)
├── COMPLETE_GUIDE.md         ← Documentation COMPLÈTE (lire ceci!)
├── README.md                 ← Vue d'ensemble
├── test_setup.py             ← Test dépendances
├── test_printers.py          ← Test imprimantes
└── test_insert.js            ← Test Supabase
```

## ⚡ Démarrage rapide (5 min)

### 1️⃣ Installer
```bash
# Cloner ou télécharger le repo
git clone https://github.com/idriss/mitake_script.git
cd mitake_script

# Installer dépendances
pip install -r requirements.txt
```

### 2️⃣ Configurer
```bash
# Copier le template
cp .env.example .env

# Éditer avec vos paramètres
# - SUPABASE_URL et SUPABASE_KEY
# - Adresses IP des imprimantes
# - Type de connexion (USB/réseau/Windows)
notepad .env
```

### 3️⃣ Lancer
```bash
# Mode test (sans imprimante)
set PRINTER_MODE=mock
python printer_agent.py

# Mode production
python printer_agent.py
```

### 4️⃣ Tester
```
1. Vérifier les logs: "✅ Connecté à l'imprimante..."
2. Insérer une commande dans Supabase
3. L'imprimante doit imprimer < 5 secondes
```

## 📖 Documentation complète

**Lire:** `COMPLETE_GUIDE.md` (tout est expliqué dedans!)

Sections:
- Vue d'ensemble
- Installation rapide
- Configuration (.env)
- Guide déploiement Windows
- Dépannage d'urgence
- Référence technique

## 🚀 Déploiement Windows

### Pour les devs/admins:
```
1. GitHub Actions construit automatiquement l'EXE
2. Télécharger mitake_printer_windows_bundle.zip
3. Extraire dans C:\Mitake\
4. Éditer .env
5. Lancer mitake_printer.exe
```

### Pour les non-techs:
→ **Lire**: `COMPLETE_GUIDE.md` (section "Guide de déploiement Windows")

## ✅ À retenir

| Fichier | Rôle |
|---------|------|
| `printer_agent.py` | L'application (main) |
| `requirements.txt` | Dépendances Python |
| `.env.example` → `.env` | Configuration |
| `COMPLETE_GUIDE.md` | **← LIRE CEL-CI!** |

## 🆘 Problème?

**1. Vérifier les logs:** `printer_agent.log`

**2. Consulter:** `COMPLETE_GUIDE.md` (section "Dépannage d'urgence")

**3. Checklist rapide:**
- [ ] `.env` configuré? 
- [ ] Imprimante allumée?
- [ ] IP correcte? (`ping 192.168.1.100`)
- [ ] Supabase accessible?

## 📞 Support

Pour toutes vos questions, **consultez `COMPLETE_GUIDE.md`** - vous y trouverez 100% de ce dont vous avez besoin!

---

**Last Update:** 2025-11-24  
**Status:** ✅ Production Ready  
**Next:** Read `COMPLETE_GUIDE.md` (seriously!)
