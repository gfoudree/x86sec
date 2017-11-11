from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(120))
    tags = db.Column(db.String(120))
    pub_date = db.Column(db.DateTime())
    content = db.Column(db.Text())
