"""
Script de diagnostic pour vérifier la configuration du système d'impression
Exécuter ce script AVANT de lancer printer_agent.py
"""

import os
import sys
import platform

print("=" * 70)
print("  DIAGNOSTIC SYSTÈME - Middleware d'Impression MITAKE")
print("=" * 70)
print()

# 1. Vérifier l'OS
print("1️⃣ SYSTÈME D'EXPLOITATION")
print(f"   OS: {platform.system()} {platform.release()}")
print(f"   Python: {sys.version}")
print()

# 2. Vérifier les dépendances
print("2️⃣ DÉPENDANCES PYTHON")
dependencies = [
    "supabase",
    "escpos",
    "usb",
    "dotenv"
]

missing = []
for dep in dependencies:
    try:
        __import__(dep)
        print(f"   ✅ {dep}")
    except ImportError:
        print(f"   ❌ {dep} - MANQUANT")
        missing.append(dep)

# Win32print (Windows uniquement)
if platform.system() == "Windows":
    try:
        import win32print
        print(f"   ✅ win32print")
    except ImportError:
        print(f"   ⚠️ win32print - Optionnel (pip install pywin32)")

print()

# 3. Vérifier les variables d'environnement
print("3️⃣ VARIABLES D'ENVIRONNEMENT")
env_file = ".env"
if os.path.exists(env_file):
    print(f"   ✅ Fichier .env trouvé")
    from dotenv import load_dotenv
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if supabase_url and supabase_url != "https://qrbqeyqvqzaltxmcyyuo.supabase.co":
        print(f"   ✅ SUPABASE_URL configuré")
    else:
        print(f"   ❌ SUPABASE_URL non configuré ou valeur par défaut")
    
    if supabase_key and supabase_key != "votre-anon-key-publique-ici":
        print(f"   ✅ SUPABASE_KEY configuré")
    else:
        print(f"   ❌ SUPABASE_KEY non configuré ou valeur par défaut")
else:
    print(f"   ⚠️ Fichier .env non trouvé (optionnel)")
    print(f"      → Copier .env.example en .env et renseigner les valeurs")

print()

# 4. Tester la connexion Supabase
print("4️⃣ CONNEXION SUPABASE")
try:
    from supabase import create_client
    url = os.getenv("SUPABASE_URL", "https://demo.supabase.co")
    key = os.getenv("SUPABASE_KEY", "demo-key")
    
    if url != "https://demo.supabase.co":
        client = create_client(url, key)
        print(f"   ✅ Client Supabase créé")
        
        # Tester une requête simple
        try:
            response = client.table("orders").select("*").limit(1).execute()
            print(f"   ✅ Connexion à la table 'orders' réussie")
        except Exception as e:
            print(f"   ⚠️ Erreur requête: {e}")
    else:
        print(f"   ⚠️ URL Supabase non configurée")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print()

# 5. Vérifier les imprimantes (Windows uniquement)
if platform.system() == "Windows":
    print("5️⃣ IMPRIMANTES INSTALLÉES (Windows)")
    try:
        import win32print
        printers = win32print.EnumPrinters(2)
        if printers:
            for printer in printers:
                print(f"   🖨️ {printer[2]}")
        else:
            print(f"   ⚠️ Aucune imprimante trouvée")
    except Exception as e:
        print(f"   ❌ Impossible de lister les imprimantes: {e}")
    print()

# 6. Résumé
print("=" * 70)
print("  RÉSUMÉ")
print("=" * 70)

if missing:
    print(f"❌ Dépendances manquantes: {', '.join(missing)}")
    print(f"   Installer avec: pip install {' '.join(missing)}")
else:
    print(f"✅ Toutes les dépendances de base sont installées")

print()
print("📋 PROCHAINES ÉTAPES:")
print("   1. Configurer .env avec vos vraies valeurs Supabase")
print("   2. Configurer les IP/VID-PID des imprimantes dans printer_agent.py")
print("   3. Tester avec: python test_printers.py")
print("   4. Lancer: python printer_agent.py")
print()
print("=" * 70)
