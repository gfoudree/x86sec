from flask import Flask
from flask import render_template
from models import db
import os

app = Flask(__name__)
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'x86sec.db'),
    SQLALCHEMY_DATABASE_URI= 'sqlite3://' + os.path.join(app.root_path, 'x86sec.db')
))
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')
