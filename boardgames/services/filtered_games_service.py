import pandas as pd

import boardgames.data.db_session as db_session
from boardgames.data.games import Game

def get_games():
    session = db_session.create_session()
    query = session.query(Game.thumbnail_url, Game.title, Game.year_published)
    #return pd.read_sql(query.statement, query.session.bind)
    return query.all()
