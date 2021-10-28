from sqlalchemy import Column, Integer, String

from boardgames.data.modelbase import SqlAlchemyBase


class Game(SqlAlchemyBase):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    bgg_game_id = Column(Integer, nullable=False, unique=True)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)
    year_published = Column(Integer, nullable=False)
    description = Column(String)
    image_url = Column(String)
    thumbnail_url = Column(String)
    min_players = Column(Integer, nullable=False)
    max_players = Column(Integer, nullable=False)
    playing_time = Column(Integer, nullable=False)
    min_playing_time = Column(Integer, nullable=False)
    max_playing_time = Column(Integer, nullable=False)
    min_age = Column(Integer, nullable=False)
    average_rating = Column(Integer, nullable=False)
    bayes_average_rating = Column(Integer, nullable=False)
    board_game_rank = Column(Integer, nullable=False)
    designers = Column(String, nullable=False)
    mechanics = Column(String, nullable=False)
    categories = Column(String, nullable=False)
    user_suggested_best_number_of_players = Column(String, nullable=False)
    user_suggested_recommended_number_of_players = Column(String, nullable=False)
    user_suggested_recommended_not_best_number_of_players = Column(
        String, nullable=False
    )
