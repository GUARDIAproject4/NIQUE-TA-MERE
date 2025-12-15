import webview
from pathlib import Path
import mysql.connector
from mysql.connector import Error
import bcrypt
import threading
import time
import json
import csv
import os
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime

class WebViewApp:
    def __init__(self):
        self.window = None
        self.base_path = Path(__file__).parent
        self.css_path = self.base_path / "style.css"
        self.css_text = self.css_path.read_text(encoding="utf-8") if self.css_path.exists() else ""
        self.current_page = "login"
        self.connection = self.connect_to_db()
        self.produits_file = self.base_path / "caca.csv"
        self.ensure_produits_file()
        self._stop_event = threading.Event()
        self._check_thread = None
    
    def ensure_produits_file(self):
        """Crée le fichier CSV s'il n'existe pas"""
        if not self.produits_file.exists():
            with open(self.produits_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'nom', 'produit', 'quantite', 'prix', 'date_ajout'])
    
    def is_connection_alive(self, connection):
        """Vérifie si la connexion à la base de données est toujours active"""
        try:
            if connection is None or not connection.is_connected():
                return False
            # Exécuter une requête simple pour vérifier la connexion
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except (Error, mysql.connector.errors.InterfaceError, mysql.connector.errors.OperationalError):
            return False

    def connect_to_db(self, max_retries=3, retry_delay=2):
        """Établit une connexion à la base de données MySQL avec gestion des tentatives"""
        last_error = None
        for attempt in range(max_retries):
            try:
                connection = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="",
                    database="db",
                    connection_timeout=5,
                    charset='utf8mb4',
                    collation='utf8mb4_unicode_ci',
                    autocommit=True
                )
                
                if connection.is_connected():
                    print(f"Connexion à la base de données réussie (tentative {attempt + 1}/{max_retries})")
                    return connection
                
            except Error as e:
                last_error = e
                print(f"Tentative de connexion {attempt + 1}/{max_retries} échouée: {str(e)}")
                if attempt < max_retries - 1:  # Ne pas attendre après la dernière tentative
                    import time
                    time.sleep(retry_delay)
        
        # Si on arrive ici, toutes les tentatives ont échoué
        error_msg = f"Impossible de se connecter à la base de données après {max_retries} tentatives"
        if last_error:
            error_msg += f": {str(last_error)}"
        print(error_msg)
        
        # Afficher un message à l'utilisateur
        if hasattr(self, 'window') and self.window:
            try:
                self.window.evaluate_js(f"""
                    alert('Erreur de connexion à la base de données. Assurez-vous que MySQL est en cours d\'exécution et que les paramètres de connexion sont corrects.\n\nDétails: {error_msg}');
                """)
            except:
                pass
                
        return None

    def hash_password(self, password):
        """Hash le mot de passe avec bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, stored_password, provided_password):
        """Vérifie si le mot de passe fourni correspond au hash stocké"""
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))
    
    def main_window(self):
        """Crée et affiche la fenêtre principale"""
        # Créer une classe API pour exposer les méthodes à JavaScript
        class API:
            def __init__(self, app):
                self.app = app
            
            def ajouter_produit(self, nom, prix, quantite, produit=""):
                return self.app.ajouter_produit(nom, prix, quantite, produit)
            
            def supprimer_produit(self, id_produit):
                return self.app.supprimer_produit(id_produit)
            
            def charger_produits(self):
                return self.app.charger_produits()
            
            def sauvegarder_produits(self, produits):
                return self.app.sauvegarder_produits(produits)
            
            def mettre_a_jour_produit(self, id_produit, nom, prix, quantite, produit=""):
                return self.app.mettre_a_jour_produit(id_produit, nom, prix, quantite, produit)
        
        # Créer l'instance de l'API
        api = API(self)
        
        # Créer la fenêtre avec l'API exposée
        self.window = webview.create_window(
            'Gestion des Produits',
            'dashboard.html',
            js_api=api,
            width=1200,
            height=800,
            min_size=(800, 600)
        )
        
        # Démarrer la boucle d'événements
        webview.start(debug=True)
    
    # Méthodes pour la gestion des produits
    def ajouter_produit(self, nom, prix, quantite, produit=""):
        """Ajoute un nouveau produit au fichier CSV"""
        produits = self.charger_produits()
        next_id = max((p['id'] for p in produits), default=0) + 1
        nouveau_produit = {
            'id': next_id,
            'nom': nom,
            'produit': produit or '',
            'quantite': int(quantite),
            'prix': float(prix),
            'date_ajout': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        produits.append(nouveau_produit)
        self.sauvegarder_produits(produits)
        return nouveau_produit
    
    def supprimer_produit(self, id_produit):
        """Supprime un produit par son ID"""
        produits = self.charger_produits()
        produits = [p for p in produits if p['id'] != int(id_produit)]
        return self.sauvegarder_produits(produits)
    
    def charger_produits(self):
        """Charge tous les produits depuis le fichier CSV"""
        if not self.produits_file.exists():
            return []
        
        with open(self.produits_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return [{
                'id': int(row.get('id', 0)),
                'nom': row.get('nom', ''),
                'produit': row.get('produit') or row.get('categorie', ''),
                'quantite': int(row.get('quantite', 0) or 0),
                'prix': float(row.get('prix', 0) or 0),
                'date_ajout': row.get('date_ajout', '')
            } for row in reader if row.get('id')]
    
    def sauvegarder_produits(self, produits):
        """Sauvegarde la liste des produits dans le fichier CSV"""
        try:
            champs = ['id', 'nom', 'produit', 'quantite', 'prix', 'date_ajout']
            with open(self.produits_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=champs)
                writer.writeheader()
                for produit in produits:
                    writer.writerow({
                        'id': produit['id'],
                        'nom': produit.get('nom', ''),
                        'produit': produit.get('produit', ''),
                        'quantite': int(produit.get('quantite', 0) or 0),
                        'prix': float(produit.get('prix', 0) or 0),
                        'date_ajout': produit.get('date_ajout', '')
                    })
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            return False

    def mettre_a_jour_produit(self, id_produit, nom, prix, quantite, produit=""):
        """Met à jour un produit existant"""
        produits = self.charger_produits()
        maj_effectuee = False
        for p in produits:
            if p['id'] == int(id_produit):
                p['nom'] = nom or p['nom']
                p['produit'] = produit or p.get('produit', '')
                try:
                    p['quantite'] = int(quantite)
                except (TypeError, ValueError):
                    pass
                try:
                    p['prix'] = float(prix)
                except (TypeError, ValueError):
                    pass
                if not p.get('date_ajout'):
                    p['date_ajout'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                maj_effectuee = True
                break
        if not maj_effectuee:
            return False
        return self.sauvegarder_produits(produits)
    
    def register_user(self, username, password):
        """Enregistre un nouvel utilisateur dans MySQL"""
        if not self.connection:
            return False, "Erreur de connexion à la base de données"
            
        try:
            cursor = self.connection.cursor()
            
            # Vérifier si l'utilisateur existe déjà
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return False, "Ce nom d'utilisateur est déjà pris"
            
            # Hachage du mot de passe
            hashed_password = self.hash_password(password)
            
            # Insérer le nouvel utilisateur
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, hashed_password)
            )
            
            self.connection.commit()
            return True, "Compte créé avec succès"
            
        except Error as e:
            self.connection.rollback()
            return False, f"Erreur lors de l'enregistrement: {str(e)}"
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def check_connection(self):
        """Vérifie périodiquement la connexion à la base de données"""
        if not self.is_connection_alive(self.connection):
            print("Vérification de la connexion: reconnexion nécessaire")
            self.connection = self.connect_to_db()
        return self.connection is not None
        
    def _check_connection_loop(self, interval=60):
        """Boucle de vérification de la connexion dans un thread séparé"""
        while not self._stop_event.is_set():
            self.check_connection()
            # Attendre l'intervalle spécifié ou jusqu'à ce qu'on nous dise d'arrêter
            self._stop_event.wait(interval)
    
    def start_connection_check(self, interval=60):
        """Démarre la vérification périodique de la connexion"""
        # Arrêter le thread précédent s'il existe
        self.stop_connection_check()
        
        # Démarrer un nouveau thread de vérification
        self._stop_event.clear()
        self._check_thread = threading.Thread(
            target=self._check_connection_loop,
            args=(interval,),
            daemon=True
        )
        self._check_thread.start()
    
    def stop_connection_check(self):
        """Arrête la vérification périodique de la connexion"""
        if hasattr(self, '_stop_event'):
            self._stop_event.set()
        if hasattr(self, '_check_thread') and self._check_thread:
            self._check_thread.join(timeout=1.0)
            self._check_thread = None
    
    def authenticate_user(self, username, password):
        """Authentifie un utilisateur avec MySQL"""
        cursor = None
        try:
            # Vérifier si la connexion est toujours active
            if not self.is_connection_alive(self.connection):
                print("La connexion à la base de données est perdue, tentative de reconnexion...")
                self.connection = self.connect_to_db()
                if not self.connection:
                    return False, "Impossible de se connecter à la base de données"

            cursor = self.connection.cursor(dictionary=True)
            
            # Récupérer l'utilisateur
            cursor.execute(
                "SELECT id, username, password_hash FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            
            if not user:
                return False, "Nom d'utilisateur ou mot de passe incorrect"
            
            # Vérifier le mot de passe
            try:
                if not self.verify_password(user['password_hash'], password):
                    return False, "Nom d'utilisateur ou mot de passe incorrect"
            except Exception as e:
                print(f"Erreur lors de la vérification du mot de passe: {e}")
                return False, "Erreur d'authentification"
            
            return True, "Connexion réussie"
            
        except Error as e:
            print(f"Erreur d'authentification: {e}")
            # Tenter de se reconnecter une fois
            try:
                self.connection = self.connect_to_db()
                if self.connection:
                    return self.authenticate_user(username, password)  # Réessayer une fois
            except Exception as e2:
                print(f"Échec de la reconnexion: {e2}")
            return False, "Erreur de connexion à la base de données"
        finally:
            if cursor:
                cursor.close()
    
    def load_template(self, template_name):
        """Charge un template HTML et injecte le CSS"""
        template_path = self.base_path / f"{template_name}.html"
        html_text = template_path.read_text(encoding="utf-8")
        
        # Ajouter le code JavaScript directement dans le HTML
        js_code = """
        <script>
        // Gestion des clics sur les liens
        document.addEventListener('DOMContentLoaded', function() {
            // Gestion de la soumission du formulaire d'inscription
            const registerForm = document.getElementById('registerForm');
            if (registerForm) {
                registerForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;
                    
                    window.pywebview.api.handle_register(username, password).then(function(response) {
                        const messageDiv = document.getElementById('message');
                        messageDiv.textContent = response.message;
                        messageDiv.className = response.success ? 'success' : 'error';
                        messageDiv.style.display = 'block';
                        
                        if (response.success) {
                            // Rediriger vers la page de connexion après un court délai
                            setTimeout(function() {
                                window.pywebview.api.navigate('login');
                            }, 1500);
                        }
                    });
                });
            }
            
            // Gestion de la soumission du formulaire de connexion
            const loginForm = document.getElementById('loginForm');
            if (loginForm) {
                loginForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const username = document.getElementById('username').value;
                    const password = document.getElementById('password').value;
                    const loginBtn = document.getElementById('loginBtn');
                    const progress = document.getElementById('progress');
                    
                    loginBtn.disabled = true;
                    loginBtn.textContent = 'Connexion...';
                    progress.style.display = 'block';
                    
                    window.pywebview.api.handle_login(username, password).then(function(response) {
                        const messageDiv = document.getElementById('message');
                        messageDiv.textContent = response.message;
                        messageDiv.style.color = response.success ? 'green' : 'red';
                        messageDiv.style.display = 'block';
                        
                        loginBtn.disabled = false;
                        loginBtn.textContent = 'Se connecter';
                        progress.style.display = 'none';
                        
                        if (response.success) {
                            // Rediriger vers la page d'accueil après connexion réussie
                            setTimeout(function() {
                                window.pywebview.api.navigate('dashboard');
                            }, 1000);
                        }
                    }).catch(function(error) {
                        const messageDiv = document.getElementById('message');
                        messageDiv.textContent = 'Erreur lors de la connexion';
                        messageDiv.style.color = 'red';
                        messageDiv.style.display = 'block';
                        
                        loginBtn.disabled = false;
                        loginBtn.textContent = 'Se connecter';
                        progress.style.display = 'none';
                        console.error('Login error:', error);
                    });
                });
            }
            
            // Gestion des clics sur les liens de navigation
            document.addEventListener('click', function(e) {
                if (e.target.tagName === 'A') {
                    e.preventDefault();
                    const href = e.target.getAttribute('href');
                    if (href.includes('login.html')) {
                        window.pywebview.api.navigate('login');
                    } else if (href.includes('template.html')) {
                        window.pywebview.api.navigate('template');
                    }
                }
            });
        });
        </script>
        """
        
        # Remplacer le placeholder CSS et ajouter le JavaScript
        html = html_text.replace(
            "<!-- INJECT_CSS -->", 
            f"<style>\n{self.css_text}\n</style>"
        )
        
        # Ajouter un div pour les messages s'il n'existe pas
        if '<main' in html and 'id="message"' not in html:
            html = html.replace(
                '<main',
                '<div id="message" style="margin: 10px 0; padding: 10px; border-radius: 4px; display: none;"></div><main'
            )
        
        # Insérer le JavaScript juste avant la fermeture du body
        if "</body>" in html:
            html = html.replace("</body>", f"{js_code}\n</body>")
        else:
            html += js_code
            
        return html
    
    def handle_register(self, username, password):
        """Gère l'inscription d'un nouvel utilisateur"""
        success, message = self.register_user(username, password)
        return {"success": success, "message": message}
    
    def handle_login(self, username, password):
        """Gère la connexion d'un utilisateur"""
        try:
            # Vérifier si la connexion est toujours active
            if not self.is_connection_alive(self.connection):
                print("La connexion à la base de données est perdue, tentative de reconnexion...")
                self.connection = self.connect_to_db()
                if not self.connection:
                    return {"success": False, "message": "Impossible de se connecter à la base de données"}

            # Authentifier l'utilisateur
            success, message = self.authenticate_user(username, password)
            
            if success:
                print(f"Utilisateur {username} connecté avec succès")
                # Démarrer la vérification périodique de la connexion
                if self.window:
                    self.start_connection_check()
                return {"success": True, "message": message, "redirect": "dashboard"}
            else:
                print(f"Échec de la connexion pour {username}: {message}")
                return {"success": False, "message": message}
                
        except Exception as e:
            error_msg = f"Erreur lors de la tentative de connexion: {str(e)}"
            print(error_msg)
            return {"success": False, "message": "Une erreur est survenue lors de la connexion"}
    
    def navigate(self, page):
        """Appelé depuis JavaScript pour changer de page"""
        if page != self.current_page:
            self.current_page = page
            try:
                # Charger le template avec le code JavaScript injecté
                if page == 'dashboard':
                    dashboard_path = self.base_path / "dashboard.html"
                    if not dashboard_path.exists():
                        # Créer un tableau de bord par défaut si le fichier n'existe pas
                        default_dashboard = """
                        <!doctype html>
                        <html lang="fr">
                        <head>
                            <meta charset="utf-8" />
                            <meta name="viewport" content="width=device-width,initial-scale=1" />
                            <title>Tableau de bord — Guardia</title>
                        </head>
                        <body>
                            <div class="container">
                                <header>
                                    <h1>Tableau de bord</h1>
                                    <nav>
                                        <a href="#" id="logout">Déconnexion</a>
                                    </nav>
                                </header>
                                <main>
                                    <h2>Bienvenue sur votre tableau de bord</h2>
                                    <p>Contenu du tableau de bord à venir...</p>
                                </main>
                            </div>
                            <script>
                            document.addEventListener('DOMContentLoaded', function() {
                                const logoutBtn = document.getElementById('logout');
                                if (logoutBtn) {
                                    logoutBtn.addEventListener('click', function(e) {
                                        e.preventDefault();
                                        window.pywebview.api.navigate('login');
                                    });
                                }
                            });
                            </script>
                            <!-- INJECT_CSS -->
                        </body>
                        </html>
                        """
                        with open(dashboard_path, 'w', encoding='utf-8') as f:
                            f.write(default_dashboard)
                
                html_content = self.load_template(page)
                self.window.load_html(html_content)
            except Exception as e:
                self.window.load_html(f"<h1>Erreur</h1><p>Impossible de charger la page {page}: {str(e)}</p>")
        
        # Mettre à jour le titre de la fenêtre
        titles = {
            'login': 'Connexion',
            'template': 'Inscription',
            'dashboard': 'Tableau de bord'
        }
        self.window.set_title(f"Guardia — {titles.get(page, 'Application')}")

def main():
    app = WebViewApp()
    
    # Vérifier la connexion à la base de données
    if not app.connection:
        print("Impossible de se connecter à la base de données. Vérifiez vos paramètres de connexion.")
        # On continue quand même pour permettre à l'utilisateur de voir l'interface
    
    # Créer la fenêtre webview avec la page de connexion par défaut
    app.window = webview.create_window(
        "Guardia — Connexion",
        html=app.load_template('login'),
        min_size=(400, 500),
        js_api=app  # Expose l'instance de l'application à JavaScript
    )
    
    try:
        # Démarrer la vérification périodique de la connexion
        app.start_connection_check(interval=60)  # Vérification toutes les 60 secondes
        
        # Démarrer l'application avec l'API exposée
        webview.start(debug=True, http_server=False)
    finally:
        # S'assurer que le thread de vérification est bien arrêté
        app.stop_connection_check()

if __name__ == "__main__":
    main()