from colorama.ansi import clear_screen
import mysql.connector
from mysql.connector import Error
from getpass import getpass
import hashlib
import bcrypt
import os 
import colorama
from colorama import Fore, Style
from ascii import login_ascii, principale_ascii, register_ascii

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
        
        choix = input("\nVotre choix (1-3): ")
        
        if choix == '1':
            print("\nFonctionnalité en cours de développement...")
        elif choix == '2':
            print("\nDéconnexion réussie.")
            return False  # Retourne au menu de connexion
        elif choix == '3':
            print("\nAu revoir !")
            exit()
        else:
            print("\nOption invalide. Veuillez réessayer.")

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
                interface(connection)

            else:
                print("Option non valide. Veuillez réessayer.")
                
    finally:
        if connection.is_connected():
            connection.close()
            print("Connexion à la base de données fermée.")

if __name__ == "__main__":
    main()
