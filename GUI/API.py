from flask import Flask, request

app = Flask(__name__)

@app.route('/range/<prefix>', methods=['GET'])
def get_range(prefix):
    users_agents = request.headers.get('User-Agent')

    if not users_agents:
        return "Erreur 400 : User-Agent manquant ou non valide. Veulliez vous identifier.", 400

    print(f"Requête reçue pour le préfixe {prefix} par : {users_agents}")
    return "Contenu de la reponse HIPB simulée...,", 200
