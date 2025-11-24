@echo off
REM ============================================================================
REM MITAKE PRINT MIDDLEWARE - Git Setup (Windows)
REM ============================================================================

echo.
echo 🚀 INITIALISATION GIT POUR MITAKE PRINT MIDDLEWARE
echo ====================================================
echo.

REM Vérifier si git est installé
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Git n'est pas installé!
    echo    Télécharger depuis: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Initialiser git si nécessaire
if not exist .git (
    echo 📦 Initialisation du repo git...
    call git init
    call git config user.name "MITAKE Dev"
    call git config user.email "dev@mitake.local"
) else (
    echo ✅ Repo git déjà initialisé
)

echo.
echo 📝 Fichiers à pousser:
echo   ✅ printer_agent.py
echo   ✅ requirements.txt
echo   ✅ .env.example
echo   ✅ .gitignore
echo   ✅ README.md
echo   ✅ QUICKSTART.md
echo   ✅ COMPLETE_GUIDE.md
echo   ✅ test_*.py
echo   ✅ test_insert.js
echo   ✅ .github\workflows\build.yml

echo.
echo ❌ Fichiers IGNORÉS (protégés):
echo   ❌ .env (credentials)
echo   ❌ __pycache__/
echo   ❌ .venv/
echo   ❌ *.log
echo   ❌ ticket_test.txt

echo.
echo 📋 Commandes à exécuter:
echo.
echo   git add .
echo   git commit -m "Initial: MITAKE Print Middleware v1.0"
echo   git remote add origin https://github.com/idriss/mitake_script.git
echo   git branch -M main
echo   git push -u origin main
echo.
echo ✅ FAIT! Votre code est maintenant sur GitHub.
echo 📦 GitHub Actions construira l'EXE Windows automatiquement!
echo.
pause
