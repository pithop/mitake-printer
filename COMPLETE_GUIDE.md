# GUIDE D'INSTALLATION ET D'UTILISATION - MITAKE PRINTER AGENT

Ce guide explique comment installer et lancer le logiciel d'impression sur le PC Caisse (Windows).

## 1. PRÉREQUIS

Avant de commencer, assurez-vous que :
1.  **Les imprimantes sont allumées et connectées** (USB ou Réseau).
2.  **Les pilotes Epson sont installés** et les imprimantes apparaissent dans "Imprimantes et scanners" de Windows.
3.  **Les noms des imprimantes sont EXACTEMENT** :
    *   Caisse : `EPSON TM-T20IV`
    *   Cuisine : `EPSON TM-T20IV Receipt (1)`
    *   *Si les noms sont différents, vous devrez modifier le fichier `.env` (voir section 2).*

## 2. INSTALLATION

1.  Créez un dossier sur le Bureau (ex: `C:\Users\Caisse\Desktop\MitakePrinter`).
2.  Copiez le fichier **`mitake_printer.exe`** dans ce dossier.
3.  Dans ce même dossier, créez un fichier nommé **`.env`** (attention, pas `.env.txt`).
4.  Ouvrez ce fichier `.env` avec le Bloc-notes et collez-y le contenu suivant :

```ini
# CONFIGURATION MITAKE PRINTER
SUPABASE_URL=https://qrbqeyqvqzaltxmcyyuo.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFyYnFleXF2cXphbHR4bWN5eXVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM5MjEyMDksImV4cCI6MjA3OTQ5NzIwOX0.H6BLQ-49QNZQn0ZZ4IB-bwwOQTJqpUPwOdFaFUTvujg

# NOMS DES IMPRIMANTES (Doivent correspondre à Windows)
PRINTER_CASHIER_NAME=EPSON TM-T20IV
PRINTER_KITCHEN_NAME=EPSON TM-T20IV Receipt (1)

PRINTER_MODE=normal
```

## 3. LANCEMENT

### Méthode 1 : Double-clic (Standard)
Double-cliquez simplement sur `mitake_printer.exe`. Une fenêtre noire (console) va s'ouvrir.
*   **NE FERMEZ PAS CETTE FENÊTRE**. Tant qu'elle est ouverte, le logiciel écoute les commandes.
*   Vous pouvez la réduire dans la barre des tâches.

### Méthode 2 : Lancement automatique (Recommandé)
Pour que le logiciel se lance au démarrage du PC :
1.  Faites un clic droit sur `mitake_printer.exe` > **Créer un raccourci**.
2.  Appuyez sur `Windows + R`, tapez `shell:startup` et faites Entrée.
3.  Déplacez le raccourci créé dans ce dossier.

## 4. VÉRIFICATION

Au démarrage, regardez la fenêtre noire. Vous devriez voir :

```text
======================================================================
🚀 MIDDLEWARE D'IMPRESSION MITAKE - Démarrage
======================================================================
✅ Fichier .env trouvé et chargé
🖨️  LISTE DES IMPRIMANTES WINDOWS DÉTECTÉES:
   🔹 Nom: 'EPSON TM-T20IV'
   🔹 Nom: 'EPSON TM-T20IV Receipt (1)'
   🔹 Nom: 'Microsoft Print to PDF'
...
✅ Connecté à l'imprimante Windows EPSON TM-T20IV
✅ Connecté à l'imprimante Windows EPSON TM-T20IV Receipt (1)
✅ Connexion à Supabase établie
🎧 Démarrage de l'écoute en temps réel...
✅ Système d'impression actif - En attente de commandes...
```

Si vous voyez ces lignes vertes (`✅`), tout fonctionne !

## 5. DÉPANNAGE (Erreurs fréquentes)

### ❌ Erreur : "Fichier .env non trouvé"
*   **Cause** : Le fichier `.env` n'est pas dans le même dossier que l'exe, ou il s'appelle `.env.txt`.
*   **Solution** : Vérifiez l'extension du fichier. Dans l'explorateur Windows, onglet "Affichage", cochez "Extensions de noms de fichiers". Renommez `config.env.txt` en `.env`.

### ❌ Erreur : "Impossible de connecter 'EPSON TM-T20IV'"
*   **Cause** : Le nom dans le fichier `.env` ne correspond pas au nom Windows.
*   **Solution** :
    1.  Regardez la liste "LISTE DES IMPRIMANTES WINDOWS DÉTECTÉES" au début de la fenêtre noire.
    2.  Copiez le nom exact qui apparaît (ex: `EPSON TM-T20IV (Copie 1)`).
    3.  Modifiez le fichier `.env` : `PRINTER_CASHIER_NAME=EPSON TM-T20IV (Copie 1)`.
    4.  Relancez le programme.

### ❌ La fenêtre se ferme tout de suite
*   **Cause** : Une erreur critique empêche le démarrage.
*   **Solution** :
    1.  Ouvrez le dossier où se trouve l'exe.
    2.  Tapez `cmd` dans la barre d'adresse en haut et faites Entrée.
    3.  Dans la fenêtre noire, tapez `mitake_printer.exe` et faites Entrée.
    4.  L'erreur restera affichée à l'écran. Prenez une photo et envoyez-la au support technique.

### ❌ "win32print non disponible"
*   **Cause** : Vous essayez de lancer la version Linux sur Windows ou l'exe est mal compilé.
*   **Solution** : Assurez-vous d'utiliser le fichier `.exe` généré par GitHub (pas le script python direct).
