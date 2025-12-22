from flask import Flask, jsonify, request
import csv
import os
from datetime import datetime

app = Flask(__name__)
CSV_FILE = 'caca.csv'

# --- Fonctions utilitaires pour le CSV ---

def load_products():
    """Charge les produits depuis le CSV dans une liste de dictionnaires."""
    products = []
    if not os.path.exists(CSV_FILE):
        return products
    
    with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Conversion des types (car le CSV lit tout en string)
            try:
                row['id'] = int(row['id'])
                row['quantite'] = int(row['quantite'])
                row['prix'] = float(row['prix'])
            except ValueError:
                continue # Ignore les lignes mal formées
            products.append(row)
    return products

def save_products(products):
    """Écrase le CSV avec la nouvelle liste de produits."""
    if not products:
        return
    
    fieldnames = ['id', 'nom', 'produit', 'quantite', 'prix', 'date_ajout']
    
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(products)

# --- Routes API ---

@app.route('/api/products', methods=['GET'])
def get_products():
    products = load_products()
    
    # Pagination
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    start = (page - 1) * limit
    end = start + limit
    
    return jsonify({
        "page": page,
        "total": len(products),
        "data": products[start:end]
    })

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_one_product(product_id):
    products = load_products()
    # On cherche le produit qui a le bon ID
    product = next((p for p in products if p['id'] == product_id), None)
    
    if product:
        return jsonify(product)
    return jsonify({"error": "Produit non trouvé"}), 404

@app.route('/api/products', methods=['POST'])
def create_product():
    # Ici, tu devrais vérifier l'authentification
    new_data = request.get_json()
    products = load_products()
    
    # Génération d'un nouvel ID (max id actuel + 1)
    new_id = 1
    if products:
        new_id = max(p['id'] for p in products) + 1
        
    new_product = {
        "id": new_id,
        "nom": new_data.get('nom', 'Inconnu'),
        "produit": new_data.get('produit', 'Sans nom'),
        "quantite": int(new_data.get('quantite', 0)),
        "prix": float(new_data.get('prix', 0.0)),
        "date_ajout": datetime.now().strftime("%Y-%m-%d") # Date du jour auto
    }
    
    products.append(new_product)
    save_products(products) # Sauvegarde dans le CSV
    
    return jsonify(new_product), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    new_data = request.get_json()
    products = load_products()
    
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        return jsonify({"error": "Produit non trouvé"}), 404
    
    # Mise à jour des champs seulement s'ils sont présents dans le JSON envoyé
    if 'nom' in new_data: product['nom'] = new_data['nom']
    if 'produit' in new_data: product['produit'] = new_data['produit']
    if 'quantite' in new_data: product['quantite'] = int(new_data['quantite'])
    if 'prix' in new_data: product['prix'] = float(new_data['prix'])
    
    save_products(products) # Sauvegarde les modifs
    return jsonify(product), 200

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    products = load_products()
    
    # On garde tous les produits SAUF celui qu'on veut supprimer
    initial_length = len(products)
    products = [p for p in products if p['id'] != product_id]
    
    if len(products) == initial_length:
        return jsonify({"error": "Produit non trouvé"}), 404
        
    save_products(products)
    return jsonify({"message": "Produit supprimé avec succès"}), 200

# Endpoint Auth simple (simulé)
@app.route('/api/auth/login', methods=['POST'])
def login():
    return jsonify({"token": "ceci-est-un-faux-token-jwt"}), 200

if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)