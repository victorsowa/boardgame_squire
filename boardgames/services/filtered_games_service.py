import pandas as pd

import boardgames.data.db_session as db_session
from boardgames.data.games import Game
from boardgames.data.user_games import UserGame
from boardgames.data.users import User


def get_user_id_from_username(username):
    session = db_session.create_session()
    return session.query(User.id).filter(User.name == username).first()[0]


def get_games(username):
    session = db_session.create_session()
    user_id = get_user_id_from_username(username)
    query = session.query(
        Game.thumbnail_url, Game.title, Game.year_published).join(
            UserGame, UserGame.bgg_game_id == Game.bgg_game_id).filter(
                UserGame.user_id == user_id)
    return query.all()
