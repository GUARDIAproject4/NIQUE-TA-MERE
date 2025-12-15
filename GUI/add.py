from flask import *
import csv
from maincreatorcsv import read_csv



app = Flask(__name__)

@app.route('/')
def welcome():
    return render_template('index_flask.html')

@app.route('/product')
def product():
    rows = read_csv('caca.csv')
    html = '<br>'.join([','.join(row) for row in rows])
    return html

@app.route('/product', methods=['GET'])
def method():
    if request.method == 'GET':
        print("succesful")
    else:
        print("Fail")

@app.route('/product/id', methods=['GET'])
def method1():
    if request.method == 'GET':
        print("succesful")
    else:
        print("Fail")

@app.route('/product', methods=['POST'])
def method2():
    if request.method == 'POST':
        print("succesful")
    else:
        print("Fail")

app.run(host='localhost', port=8080)


