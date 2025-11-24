"""
Script de test des imprimantes
Permet de vérifier la connexion et d'imprimer un ticket de test
"""

import sys
from datetime import datetime

# Import du module principal
try:
    from printer_agent import (
        PrinterManager,
        TicketGenerator,
        Config,
        logger
    )
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    print("Assurez-vous que printer_agent.py est dans le même dossier")
    sys.exit(1)


def test_printer_connection(printer_config, name):
    """Teste la connexion à une imprimante"""
    print(f"\n{'='*60}")
    print(f"TEST IMPRIMANTE: {name}")
    print(f"{'='*60}")
    print(f"Type: {printer_config['type']}")
    
    if printer_config['type'] == 'network':
        print(f"IP: {printer_config['ip']}:{printer_config.get('port', 9100)}")
    elif printer_config['type'] == 'usb':
        print(f"VID: 0x{printer_config['vendor_id']:04x}")
        print(f"PID: 0x{printer_config['product_id']:04x}")
    elif printer_config['type'] == 'windows':
        print(f"Nom: {printer_config['name']}")
    
    print("\n🔌 Tentative de connexion...")
    
    manager = PrinterManager(printer_config)
    
    if manager.connect():
        print("✅ Connexion réussie!")
        
        # Test d'impression
        print("\n🖨️ Test d'impression...")
        
        def print_test(p):
            # API python-escpos: utiliser bold=True au lieu de text_type='B'
            p.set(align='center', bold=True, width=2, height=2)
            p.text("TEST IMPRESSION\n")
            # Retour au style normal
            p.set(bold=False, width=1, height=1)
            p.text(f"{name}\n")
            p.text(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            p.text("\n")
            p.text("Si vous voyez ce ticket,\n")
            p.text("l'imprimante fonctionne!\n")
            p.text("\n" * 2)
            if hasattr(p, 'cut'):
                try:
                    p.cut()
                except Exception:
                    pass  # Certaines imprimantes/mock peuvent ne pas supporter cut
        
        success = manager.print_raw(print_test)
        
        if success:
            print("✅ Impression réussie!")
        else:
            print("❌ Échec de l'impression")
        
        manager.disconnect()
        return True
    else:
        print("❌ Échec de connexion")
        print("\n💡 CONSEILS:")
        if printer_config['type'] == 'network':
            print("   - Vérifier l'IP avec: ping", printer_config['ip'])
            print("   - Vérifier que le port 9100 est ouvert")
            print("   - Vérifier que l'imprimante est allumée")
        elif printer_config['type'] == 'usb':
            print("   - Vérifier que l'imprimante est branchée")
            print("   - Exécuter en Administrateur")
            print("   - Vérifier les VID/PID dans le Gestionnaire de périphériques")
        return False


def test_ticket_generation():
    """Teste la génération d'un ticket complet"""
    print(f"\n{'='*60}")
    print(f"TEST GÉNÉRATION DE TICKET")
    print(f"{'='*60}")
    
    # Données de test
    test_order = {
        "id": 999,
        "order_number": "TEST-001",
        "customer_name": "Client Test",
        "customer_phone": "06 12 34 56 78",
        "payment_status": "paid",
        "items": [
            {
                "name": "Ramen Tonkotsu",
                "quantity": 2,
                "price": 13.50,
                "options": ["Extra chashu", "Œuf mariné"],
                "comment": "Bien chaud SVP"
            },
            {
                "name": "Gyoza",
                "quantity": 1,
                "price": 6.00,
                "options": [],
                "comment": None
            },
            {
                "name": "Thé vert",
                "quantity": 2,
                "price": 2.50,
                "options": ["Sans sucre"],
                "comment": None
            }
        ]
    }
    
    print("\n🧾 Test ticket CAISSE...")
    cashier = PrinterManager(Config.PRINTER_CASHIER)
    if cashier.connect():
        success = cashier.print_raw(
            lambda p: TicketGenerator.print_cashier_ticket(p, test_order)
        )
        cashier.disconnect()
        
        if success:
            print("✅ Ticket CAISSE imprimé")
        else:
            print("❌ Échec impression ticket CAISSE")
    else:
        print("❌ Impossible de se connecter à l'imprimante CAISSE")
    
    print("\n🍜 Test ticket CUISINE...")
    kitchen = PrinterManager(Config.PRINTER_KITCHEN)
    if kitchen.connect():
        success = kitchen.print_raw(
            lambda p: TicketGenerator.print_kitchen_ticket(p, test_order)
        )
        kitchen.disconnect()
        
        if success:
            print("✅ Ticket CUISINE imprimé")
        else:
            print("❌ Échec impression ticket CUISINE")
    else:
        print("❌ Impossible de se connecter à l'imprimante CUISINE")


def main():
    """Menu principal"""
    print("=" * 60)
    print("  TEST DES IMPRIMANTES - MITAKE")
    print("=" * 60)
    print("\nQue voulez-vous tester?")
    print("1. Connexion imprimante CAISSE")
    print("2. Connexion imprimante CUISINE")
    print("3. Les deux imprimantes")
    print("4. Impression d'un ticket complet (CAISSE + CUISINE)")
    print("5. Quitter")
    
    choice = input("\nVotre choix (1-5): ").strip()
    
    if choice == "1":
        test_printer_connection(Config.PRINTER_CASHIER, "CAISSE")
    elif choice == "2":
        test_printer_connection(Config.PRINTER_KITCHEN, "CUISINE")
    elif choice == "3":
        test_printer_connection(Config.PRINTER_CASHIER, "CAISSE")
        test_printer_connection(Config.PRINTER_KITCHEN, "CUISINE")
    elif choice == "4":
        test_ticket_generation()
    elif choice == "5":
        print("\n👋 Au revoir!")
        sys.exit(0)
    else:
        print("\n❌ Choix invalide")
    
    print("\n" + "=" * 60)
    print("✅ Tests terminés")
    print("=" * 60)


if __name__ == "__main__":
    main()
