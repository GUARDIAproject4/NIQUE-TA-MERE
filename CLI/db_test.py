from colorama.ansi import clear_screen
import mysql.connector
from mysql.connector import Error
from getpass import getpass
import hashlib
import bcrypt
import os 
import colorama
from colorama import Fore, Style
from ascii import login_ascii, principale_ascii, register_ascii, menu, produits_menu_cli1
import sys
from pathlib import Path
import csv
from datetime import datetime

# Ensure project root is on sys.path so sibling packages (like GUI) can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from GUI.gui import WebViewApp

def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="db"
        )
        return connection
    except Error as e:
        print(f"Erreur de connexion à la base de données: {e}")
        return None


def interface(connection):
    os.system("cls or clear")
    

def principale(connection):
    while True:

        principale_ascii()

        print("1. Voir le profil")
        print("2. Se déconnecter")
        print("3. Quitter")
        print("4. Gestion des produits")

        choix = input("\nVotre choix (1-4): ")
        
        if choix == '1':
            print("\nFonctionnalité en cours de développement...")
        elif choix == '2':
            print("\nDéconnexion réussie.")
            return False  # Retourne au menu de connexion
        elif choix == '3':
            print("\nAu revoir !")
            exit()
        elif choix == '4':
            produits_menu_cli()
        else:
            print("\nOption invalide. Veuillez réessayer.")


def _get_produits_file():
    return Path(__file__).resolve().parent.parent / 'GUI' / 'caca.csv'


def charger_produits_cli():
    produits_file = _get_produits_file()
    if not produits_file.exists():
        return []
    with open(produits_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        produits = []
        for row in reader:
            if not row.get('id'):
                continue
            try:
                quantite = int(row.get('quantite') or 0)
            except Exception:
                quantite = 0
            try:
                prix = float(row.get('prix') or 0)
            except Exception:
                prix = 0.0
            produits.append({
                'id': int(row.get('id', 0)),
                'nom': row.get('nom', ''),
                'produit': row.get('produit', '') or row.get('categorie', ''),
                'quantite': quantite,
                'prix': prix,
                'date_ajout': row.get('date_ajout', '')
            })
    return produits


def sauvegarder_produits_cli(produits):
    produits_file = _get_produits_file()
    produits_file.parent.mkdir(parents=True, exist_ok=True)
    champs = ['id', 'nom', 'produit', 'quantite', 'prix', 'date_ajout']
    with open(produits_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=champs)
        writer.writeheader()
        for p in produits:
            writer.writerow({
                'id': p['id'],
                'nom': p.get('nom', ''),
                'produit': p.get('produit', ''),
                'quantite': int(p.get('quantite', 0) or 0),
                'prix': float(p.get('prix', 0) or 0),
                'date_ajout': p.get('date_ajout', '')
            })
    return True


def afficher_produits_cli():
    produits = charger_produits_cli()
    if not produits:
        print('\nAucun produit trouvé.')
        return
    print('\n{:<4} {:<20} {:<15} {:<8} {:<8} {}'.format('ID', 'Nom', 'Produit', 'Quantité', 'Prix', 'Date'))
    for p in produits:
        print('{:<4} {:<20} {:<15} {:<8} {:<8} {}'.format(p['id'], p['nom'][:20], p.get('produit','')[:15], p['quantite'], p['prix'], p.get('date_ajout','')))


def ajouter_produit_cli():
    print('\nAjout d\'un produit')
    nom = input('Nom: ').strip()
    produit = input('Catégorie/produit: ').strip()
    quantite = input('Quantité: ').strip()
    prix = input('Prix: ').strip()
    try:
        quantite = int(quantite)
    except Exception:
        quantite = 0
    try:
        prix = float(prix)
    except Exception:
        prix = 0.0
    produits = charger_produits_cli()
    next_id = max((p['id'] for p in produits), default=0) + 1
    nouveau = {
        'id': next_id,
        'nom': nom,
        'produit': produit,
        'quantite': quantite,
        'prix': prix,
        'date_ajout': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    produits.append(nouveau)
    sauvegarder_produits_cli(produits)
    print('\nProduit ajouté avec succès.')


def supprimer_produit_cli():
    id_str = input('\nID du produit à supprimer: ').strip()
    try:
        idv = int(id_str)
    except Exception:
        print('ID invalide.')
        return
    produits = charger_produits_cli()
    nouveaux = [p for p in produits if p['id'] != idv]
    if len(nouveaux) == len(produits):
        print('Produit introuvable.')
        return
    sauvegarder_produits_cli(nouveaux)
    print('Produit supprimé.')


def rechercher_produits_cli():
    terme = input('\nTerme de recherche: ').strip().lower()
    if not terme:
        print('Terme vide.')
        return
    produits = charger_produits_cli()
    resultats = [p for p in produits if terme in (p.get('nom','').lower() or '') or terme in (p.get('produit','').lower() or '')]
    if not resultats:
        print('Aucun résultat.')
        return
    print('\nRésultats:')
    print('{:<4} {:<20} {:<15} {:<8} {:<8} {}'.format('ID', 'Nom', 'Produit', 'Quantité', 'Prix', 'Date'))
    for p in resultats:
        print('{:<4} {:<20} {:<15} {:<8} {:<8} {}'.format(p['id'], p['nom'][:20], p.get('produit','')[:15], p['quantite'], p['prix'], p.get('date_ajout','')))


def produits_menu_cli():
    produits_menu_cli1()
    while True:
        print('\n--- Gestion des produits (CLI) ---')
        print('1. Afficher les produits')
        print('2. Ajouter un produit')
        print('3. Supprimer un produit')
        print('4. Rechercher des produits')
        print('5. Retour')
        choix = input('Votre choix (1-5): ').strip()
        if choix == '1':
            afficher_produits_cli()
        elif choix == '2':
            ajouter_produit_cli()
        elif choix == '3':
            supprimer_produit_cli()
        elif choix == '4':
            rechercher_produits_cli()
        elif choix == '5':
            break
        else:
            print('Option invalide. Veuillez réessayer.')

def login_user(connection):
    try:
        login_ascii()

        username = input("Nom d'utilisateur: ")
        password = getpass("Mot de passe: ")
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            print(f"\nConnexion réussie ! Bienvenue, {user['username']} !")
            # Boucle tant que l'utilisateur ne se déconnecte pas
            while principale(connection):
                pass
            return True
        else:
            print("\nErreur: Nom d'utilisateur ou mot de passe incorrect.")
            return False
            
    except Error as e:
        print(f"Erreur lors de la connexion: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()

def add_user(connection):
    try:

        register_ascii()

        username = input("Nouveau nom d'utilisateur: ")
        password = getpass("Nouveau mot de passe: ")
        
        #Vérifier si l'utilisateur existe déjà
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            print("Erreur: Ce nom d'utilisateur est déjà pris.")
            return
            
        # Hachage du mot de passe avec bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, hashed.decode('utf-8'))
        )
        connection.commit()
        print("\nUtilisateur ajouté avec succès!")
        
    except Error as e:
        print(f"Erreur lors de l'ajout de l'utilisateur: {e}")
        connection.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()



def main():
    print("=== Gestion simple d'utilisateurs ===\n")
    
    # Connexion à la base de données
    connection = connect_to_db()
    if not connection:
        return
    
    try:
        while True:
            menu()
            print("\nOptions:")
            print("1. Inscription")
            print("2. Login")
            print("3. Quitter")
            print("4. Interface")
            
            choice = input("\nVotre choix (1-4): ")
            
            if choice == '2':
                login_user(connection)
            elif choice == '1':
                add_user(connection)
            elif choice == '3':
                print("Au revoir!")
                break
            elif choice == '4':
                app = WebViewApp()
                app.run()

            else:
                print("Option non valide. Veuillez réessayer.")
                
    finally:
        if connection.is_connected():
            connection.close()
            print("Connexion à la base de données fermée.")

if __name__ == "__main__":
    main()
