from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class BattleResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, nullable=False)
    opponent_id = db.Column(db.Integer, nullable=False)
    winner_id = db.Column(db.Integer, nullable=False)
    rounds = db.Column(db.Integer, nullable=False)

    def __init__(self, user_id, opponent_id, winner_id, rounds):
        self.user_id = user_id
        self.opponent_id = opponent_id
        self.winner_id = winner_id
        self.rounds = rounds