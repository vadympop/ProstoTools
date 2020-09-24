# Imports
import mysql.connector
from flask import Flask

# Create a flask app
app = Flask(__name__)
app.config.from_object('Site.config.Config')


# Work with DB
conn = mysql.connector.connect(user='root', passwd='9fr8-PkM;M4+', host='localhost', db='data')
cursor = conn.cursor(buffered=True)
