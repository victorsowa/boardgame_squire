from sqlalchemy import Column, Integer, String

from boardgames.data.modelbase import SqlAlchemyBase


class UserGame(SqlAlchemyBase):
    __tablename__ = 'user_games'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    bgg_game_id = Column(Integer, nullable=False)
    user_rating = Column(Integer)
