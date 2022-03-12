"""Models for application"""

from datetime import datetime
import string
import random

from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

from src.database import db


class User(db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(Text(), nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, onupdate=datetime.now())
    bookmarks = relationship('Bookmark', backref='user')

    def __repr__(self):
        return f"User: {self.username}"


class Bookmark(db.Model):
    id = Column(Integer, primary_key=True)
    body = Column(Text, nullable=True)
    url = Column(Text, nullable=False)
    short_url = Column(String(3), nullable=True)
    visits = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey('user.id'))
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, onupdate=datetime.now())

    def generate_short_characters(self):
        """Generate short url"""
        characters = string.digits + string.ascii_letters
        picked_chars = ''.join(random.choices(characters, k=3))
        link = self.query.filter_by(short_url=picked_chars).first()

        if link:
            self.generate_short_characters()
        else:
            return picked_chars

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.short_url = self.generate_short_characters()

    def __repr__(self):
        return f"Bookmark: {self.url}"
