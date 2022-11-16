# Парсинг книг и заполнение базы данных для проекта online_book_store


import requests
from bs4 import BeautifulSoup
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import random


app = Flask(__name__)
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

book_genre = db.Table('book_genre',
                      db.Column('book_id', db.Integer, db.ForeignKey('book.id')),
                      db.Column('genre.id', db.Integer, db.ForeignKey('genre.id')))

order_book = db.Table('order_book',
                      db.Column('order_id', db.Integer, db.ForeignKey('order.id')),
                      db.Column('book_id', db.Integer, db.ForeignKey('book.id')),
                      db.Column('amount', db.Integer))

order_step = db.Table('order_step',
                      db.Column('order_id', db.Integer, db.ForeignKey('order.id')),
                      db.Column('step_id', db.Integer, db.ForeignKey('step.id')),
                      db.Column('date', db.DateTime))


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    books = db.relationship('Book', backref='author')

    def __init__(self, name):
        self.name = name


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    image_path = db.Column(db.String)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))
    genres = db.relationship('Genre', secondary=book_genre, backref='books')
    orders = db.relationship('Order', secondary=order_book, backref='books')

    def __init__(self, title, price, amount, image_path, author):
        self.title = title
        self.price = price
        self.amount = amount
        self.image_path = image_path
        self.author = author


class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    def __init__(self, name):
        self.name = name


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_city = db.Column(db.String, nullable=False)
    days_delivery = db.Column(db.Integer, nullable=False)
    clients = db.relationship('Client', backref='city')

    def __init__(self, name_city, days_delivery):
        self.name_city = name_city
        self.days_delivery = days_delivery


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    steps = db.relationship('Step', secondary=order_step, backref='orders')

    def __init__(self, client):
        self.client = client


class Step(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_step = db.Column(db.String, nullable=False)

    def __init__(self, name_step):
        self.name_step = name_step


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    login = db.Column(db.String, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'))
    orders = db.relationship('Order', backref='client')

    def __init__(self, first_name, last_name, email, login, password_hash, city):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.login = login
        self.password_hash = password_hash
        self.city = city


with app.app_context():
    db.create_all()

genres = ('Проза', 'Детектив', 'Боевик', 'Триллер', 'фантастика', 'Фэнтези', 'Романтика', 'Поэзия', 'Мемуары',
          'Приключения', 'Комиксы', 'Юмор', 'Афоризмы', 'Фольклор')

# Добавление жанров в базу данных.
with app.app_context():
    for g in genres:
        db.session.add(Genre(g))
    db.session.commit()

for i in range(1, 6):
    url = 'https://www.chitai-gorod.ru/catalog/books/khudozhestvennaya_literatura-9657/?page=' + str(i)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    product_cards = soup.find_all('div', 'product-card')
    for card in product_cards:
        title = card.find('div', 'product-card__title').text.strip()
        # author_name = card.find('div', 'product-card__author').text.strip()
        author_name = card.find('div', 'product-card__author').text.split(',')[0].strip()
        price = card.find('span', 'product-price__value').text.split()[0]
        amount = random.randint(10, 100)
        img_path = card.find('img')['data-src'].replace('preview', 'detail')
        img_name = img_path.split('/')[-1].split('_')[0] + '.jpg'
        img = requests.get(img_path)
        # Скачивание обложки книги
        with open(img_name, 'wb') as f:
            f.write(img.content)

        with app.app_context():
            # Проверка на существование автора в базе.
            author_in_db = db.session.query(Author).filter_by(name=author_name).first()
            author = author_in_db or Author(author_name)
            # Добавление книги и автора в базу.
            db.session.add(Book(title, price, amount, img_name, author))
            db.session.commit()

with app.app_context():
    # Все книги в базе.
    all_books = db.session.query(Book).all()
    # Все жанры в базе.
    all_genres = db.session.query(Genre).all()
    for b in all_books:
        # Выбираем случайный жанр.
        genre_1 = random.choice(all_genres)
        # Связываем случайный жанр с книгой.
        b.genres.append(genre_1)
        # В одном из пяти случаев связываем второй жанр с книгой.
        if random.randint(1, 5) == 1:
            genre_2 = random.choice(all_genres)
            if genre_1 != genre_2:
                b.genres.append(genre_2)

    db.session.commit()
