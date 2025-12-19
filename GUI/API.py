import csv
import os
import hashlib
import requests

# On tente d'importer la DB, mais on évite le crash si XAMPP est éteint ou le fichier manquant
try:
    from add import Database
except:
    Database = None

class Api:
    def __init__(self):
        self.cancel = False
        # Connexion sécurisée à la base de données
        try:
            if Database:
                self.db = Database()
            else:
                self.db = None
                print("Attention: Base de données non connectée (XAMPP éteint ?)")
        except Exception as e:
            print(f"Erreur d'initialisation DB: {e}")
            self.db = None

    # --- 1. FONCTION LOGIN (Celle qui manquait peut-être) ---
    def login(self, username, password):
        print(f"Tentative de connexion : Utilisateur={username} Mdp={password}")
        
        # TEST : Accepte uniquement admin / admin
        if username == "admin" and password == "admin":
            return True
        
        # Si vous voulez accepter n'importe quel mot de passe pour tester, décommentez la ligne dessous :
        # return True
        
        return False

    # --- 2. FONCTION SECURITÉ (Have I Been Pwned) ---
    def check_security(self, password):
        if not password: return {"status": "error", "message": "Mot de passe vide"}
        
        sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix, suffix = sha1_password[:5], sha1_password[5:]
        
        try:
            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            r = requests.get(url, timeout=5)
            if suffix in r.text:
                count = [line.split(':')[1] for line in r.text.splitlines() if line.startswith(suffix)][0]
                return {"status": "danger", "message": f"⚠️ DANGER : Vu {count} fois !"}
            return {"status": "safe", "message": "✅ Mot de passe sûr"}
        except:
            return {"status": "error", "message": "Erreur connexion internet"}

    # --- 3. GESTION DES PRODUITS ---
    def get_products(self):
        filename = 'caca.csv'
        if not os.path.exists(filename): return []
        products = []
        try:
            with open(filename, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader: products.append(row)
        except Exception as e:
            print(f"Erreur lecture CSV: {e}")
        return products

    def add_product(self, name, price, quantity, category):
        # Sauvegarde SQL (si la DB est active)
        if self.db:
            try:
                self.db.add_product(name, price, quantity, category)
            except Exception as e:
                print(f"Erreur ajout SQL: {e}")

        # Sauvegarde CSV (Toujours active)
        import random
        new_id = random.randint(100, 999)
        file_exists = os.path.isfile('caca.csv')
        
        with open('caca.csv', mode='a', newline='', encoding='utf-8') as file:
            fieldnames = ['id', 'nom', 'produit', 'quantite', 'prix']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists: writer.writeheader()
            writer.writerow({'id': new_id, 'nom': name, 'produit': category, 'quantite': quantity, 'prix': price})
            
        return {"status": "success"}

    def delete_product(self, product_id):
        # Logique CSV simple pour la suppression
        filename = 'caca.csv'
        products = []
        if os.path.exists(filename):
            with open(filename, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if str(row['id']) != str(product_id): products.append(row)
            
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                fieldnames = ['id', 'nom', 'produit', 'quantite', 'prix']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(products)
        return True
    
    # Redirection simple pour le JS
    def navigate(self, page_name):
        # Cette fonction sert juste si le JS appelle navigate()
        pass