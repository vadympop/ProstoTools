# Imports
import mysql.connector

from flask import Flask
from Site.utils import Utils

# Create a flask app
app = Flask(__name__)
app.config.from_object('Site.config.Config')


# Work with DB
conn = mysql.connector.connect(user='root', password='9fr8-PkM;M4+', host='localhost', database='data')
cursor = conn.cursor(buffered=True)


# Create object of utils module
utils = Utils()
