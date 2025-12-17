import webview
from pathlib import Path
import mysql.connector
from mysql.connector import Error
import bcrypt
import threading
import time
import csv
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
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except (Error, mysql.connector.errors.InterfaceError, mysql.connector.errors.OperationalError):
            return False

    def connect_to_db(self, max_retries=3, retry_delay=2):
        """Établit une connexion à la base de données MySQL"""
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
                    print(f"Connexion réussie (tentative {attempt + 1})")
                    return connection
            except Error as e:
                last_error = e
                print(f"Tentative {attempt + 1} échouée: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        print(f"Erreur finale DB: {str(last_error)}")
        return None

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, stored_password, provided_password):
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

    # --- MÉTHODES PRODUITS (DÉPLACÉES ICI À L'INTÉRIEUR DE LA CLASSE) ---
    def ajouter_produit(self, nom, prix, quantite, produit=""):
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
        produits = self.charger_produits()
        produits = [p for p in produits if p['id'] != int(id_produit)]
        return self.sauvegarder_produits(produits)
    
    def charger_produits(self):
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
    
    def rechercher_produits(self, terme_recherche):
        produits = self.charger_produits()
        if not terme_recherche or terme_recherche.strip() == "":
            return produits
        terme_recherche = terme_recherche.lower().strip()
        resultats = []
        for produit in produits:
            nom = produit.get('nom', '').lower()
            cat_produit = produit.get('produit', '').lower()
            if terme_recherche in nom or terme_recherche in cat_produit:
                resultats.append(produit)
        return resultats

    def sauvegarder_produits(self, produits):
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
            print(f"Erreur sauvegarde: {e}")
            return False

    def mettre_a_jour_produit(self, id_produit, nom, prix, quantite, produit=""):
        produits = self.charger_produits()
        maj_effectuee = False
        for p in produits:
            if p['id'] == int(id_produit):
                p['nom'] = nom or p['nom']
                p['produit'] = produit or p.get('produit', '')
                try: p['quantite'] = int(quantite)
                except: pass
                try: p['prix'] = float(prix)
                except: pass
                if not p.get('date_ajout'):
                    p['date_ajout'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                maj_effectuee = True
                break
        if not maj_effectuee:
            return False
        return self.sauvegarder_produits(produits)
    # ----------------------------------------------------------------

    def register_user(self, username, password):
        if not self.connection:
            return False, "Erreur de connexion DB"
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return False, "Nom d'utilisateur déjà pris"
            hashed_password = self.hash_password(password)
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
            self.connection.commit()
            return True, "Compte créé avec succès"
        except Error as e:
            self.connection.rollback()
            return False, f"Erreur: {str(e)}"
        finally:
            if 'cursor' in locals(): cursor.close()

    def check_connection(self):
        if not self.is_connection_alive(self.connection):
            print("Reconnexion DB...")
            self.connection = self.connect_to_db()
        return self.connection is not None
        
    def _check_connection_loop(self, interval=60):
        while not self._stop_event.is_set():
            self.check_connection()
            self._stop_event.wait(interval)
    
    def start_connection_check(self, interval=60):
        self.stop_connection_check()
        self._stop_event.clear()
        self._check_thread = threading.Thread(target=self._check_connection_loop, args=(interval,), daemon=True)
        self._check_thread.start()
    
    def stop_connection_check(self):
        if hasattr(self, '_stop_event'): self._stop_event.set()
        if hasattr(self, '_check_thread') and self._check_thread:
            self._check_thread.join(timeout=1.0)
            self._check_thread = None

    def authenticate_user(self, username, password):
        try:
            if not self.is_connection_alive(self.connection):
                self.connection = self.connect_to_db()
                if not self.connection: return False, "Pas de connexion DB"
            
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if not user or not self.verify_password(user['password_hash'], password):
                return False, "Identifiants incorrects"
            return True, "Connexion réussie"
        except Error as e:
            return False, "Erreur DB"
        finally:
            if 'cursor' in locals() and cursor: cursor.close()

    def handle_register(self, username, password):
        success, message = self.register_user(username, password)
        return {"success": success, "message": message}
    
    def handle_login(self, username, password):
        success, message = self.authenticate_user(username, password)
        if success:
            if self.window: self.start_connection_check()
            return {"success": True, "message": message, "redirect": "dashboard"}
        return {"success": False, "message": message}

    def navigate(self, page):
        if page != self.current_page:
            self.current_page = page
            try:
                # Création du dashboard si inexistant
                if page == 'dashboard':
                    dashboard_path = self.base_path / "dashboard.html"
                    if not dashboard_path.exists():
                        with open(dashboard_path, 'w', encoding='utf-8') as f:
                            f.write("<h1>Dashboard</h1>") # Version simplifiée pour l'exemple
                
                html_content = self.load_template(page)
                self.window.load_html(html_content)
            except Exception as e:
                self.window.load_html(f"<h1>Erreur</h1><p>{str(e)}</p>")
            
            titles = {'login': 'Connexion', 'template': 'Inscription', 'dashboard': 'Tableau de bord'}
            self.window.set_title(f"Guardia — {titles.get(page, 'Application')}")

    def load_template(self, template_name):
        template_path = self.base_path / f"{template_name}.html"
        html_text = template_path.read_text(encoding="utf-8") if template_path.exists() else "<h1>404</h1>"
        
        js_code = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Register
            const registerForm = document.getElementById('registerForm');
            if (registerForm) {
                registerForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const u = document.getElementById('username').value;
                    const p = document.getElementById('password').value;
                    window.pywebview.api.handle_register(u, p).then(r => {
                        const m = document.getElementById('message');
                        m.textContent = r.message;
                        m.className = r.success ? 'success' : 'error';
                        m.style.display = 'block';
                        if(r.success) setTimeout(() => window.pywebview.api.navigate('login'), 1500);
                    });
                });
            }
            // Login
            const loginForm = document.getElementById('loginForm');
            if (loginForm) {
                loginForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const u = document.getElementById('username').value;
                    const p = document.getElementById('password').value;
                    window.pywebview.api.handle_login(u, p).then(r => {
                        const m = document.getElementById('message');
                        m.textContent = r.message;
                        m.style.display = 'block';
                        m.style.color = r.success ? 'green' : 'red';
                        if(r.success) setTimeout(() => window.pywebview.api.navigate('dashboard'), 1000);
                    });
                });
            }
            // Links
            document.addEventListener('click', function(e) {
                if (e.target.tagName === 'A') {
                    e.preventDefault();
                    const href = e.target.getAttribute('href');
                    if (href.includes('login')) window.pywebview.api.navigate('login');
                    else if (href.includes('template')) window.pywebview.api.navigate('template');
                    else if (href.id === 'logout') window.pywebview.api.navigate('login');
                }
            });
        });
        </script>
        """
        html = html_text.replace("", f"<style>\n{self.css_text}\n</style>")
        if '<main' in html and 'id="message"' not in html:
            html = html.replace('<main', '<div id="message" style="display:none;padding:10px;"></div><main')
        if "</body>" in html:
            html = html.replace("</body>", f"{js_code}\n</body>")
        else:
            html += js_code
        return html


def main():
    app = WebViewApp()
    
    if not app.connection:
        print("Attention: Pas de connexion DB.")

    # --- CLASSE API wrapper pour éviter la récursion infinie ---
    class MainAPI:
        def __init__(self, app_instance):
            self.app = app_instance
        
        # Auth
        def handle_login(self, u, p): return self.app.handle_login(u, p)
        def handle_register(self, u, p): return self.app.handle_register(u, p)
        def navigate(self, p): return self.app.navigate(p)
        
        # Produits
        def ajouter_produit(self, n, p, q, prod=""): return self.app.ajouter_produit(n, p, q, prod)
        def supprimer_produit(self, id): return self.app.supprimer_produit(id)
        def charger_produits(self): return self.app.charger_produits()
        def mettre_a_jour_produit(self, id, n, p, q, prod=""): return self.app.mettre_a_jour_produit(id, n, p, q, prod)
        def rechercher_produits(self, terme): return self.app.rechercher_produits(terme)

    api_instance = MainAPI(app)
    # ---------------------------------------------------------

    app.window = webview.create_window(
        "Guardia — Connexion",
        html=app.load_template('login'),
        min_size=(400, 500),
        js_api=api_instance  # On passe le wrapper API, pas 'app' !
    )
    
    try:
        app.start_connection_check(interval=60)
        webview.start(debug=True, http_server=False)
    finally:
        app.stop_connection_check()

if __name__ == "__main__":
    main()