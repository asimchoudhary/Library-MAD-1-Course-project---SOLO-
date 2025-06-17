from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False, unique=True)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False, unique=True)
    date = db.Column(db.String, nullable=False)
    desc = db.Column(db.String, nullable=False)
    books = db.relationship('Book', backref='section', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False, unique=True)
    author = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    book_section = db.Column(db.String, nullable=False)
    feedback = db.relationship('Feedback', backref='book', lazy=True)
    price = db.Column(db.Integer, nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    feedback = db.Column(db.String, nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    books_requested = db.relationship('BookRequests', backref='user', lazy=True)

class BookRequests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bookId = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    granted = db.Column(db.Boolean, nullable=False)
    book = db.relationship('Book', backref='book_requests', lazy=True)
    userWhoRequested = db.relationship('User', backref='book_requests', lazy=True)
    time = db.Column(db.String, nullable=False)
    requestAcceptedTF = db.Column(db.Integer , nullable = True)
    requestRevokeTF = db.Column(db.Integer , nullable = True)
    
                                                 