import pandas as pd
from collections import namedtuple

import boardgames.data.db_session as db_session
from boardgames.data.games import Game
from boardgames.data.user_games import UserGame
from boardgames.data.users import User


GameCollectionFilters = namedtuple(
    "GameCollectionFilters",
    [
        "player_count",
        "player_count_filter_type",
        "min_playing_time",
        "max_playing_time",
        "include_expansions",
    ],
)


DEFAULT_COLLECTION_FILTERS = GameCollectionFilters(
    player_count="Any",
    player_count_filter_type="Possible",
    min_playing_time="Any",
    max_playing_time="Any",
    include_expansions=False,
)


def get_user_id_from_username(username):
    session = db_session.create_session()
    return session.query(User.id).filter(User.name == username).first()[0]


def get_games(username, filters=DEFAULT_COLLECTION_FILTERS):
    session = db_session.create_session()
    user_id = get_user_id_from_username(username)
    base_query = (
        session.query(
            Game.thumbnail_url,
            Game.title,
            Game.year_published,
            Game.description,
            Game.min_players,
            Game.max_players,
            Game.min_playing_time,
            Game.max_playing_time,
            Game.average_weight,
            Game.average_rating,
            Game.board_game_rank,
            Game.user_suggested_best_number_of_players,
            Game.user_suggested_recommended_number_of_players,
            Game.user_suggested_recommended_not_best_number_of_players,
        )
        .join(UserGame, UserGame.bgg_game_id == Game.bgg_game_id)
        .filter(UserGame.user_id == user_id)
    )
    query = apply_filters_to_get_games(base_query, filters)
    return query.all()


def apply_filters_to_get_games(query, filters):
    print("Applying filters")
    filter_functions = [
        apply_player_count_filter,
        apply_min_playing_time_filter,
        apply_max_playing_time_filter,
        apply_expansion_filter,
    ]

    for filter_function in filter_functions:
        query = filter_function(query, filters)
    return query


def apply_player_count_filter(query, filters):
    if filters.player_count == DEFAULT_COLLECTION_FILTERS.player_count:
        return query
    if filters.player_count_filter_type == "Possible":
        return query.filter(Game.min_players <= filters.player_count).filter(
            Game.max_players >= filters.player_count
        )
    if filters.player_count_filter_type == "Recommended":
        return query.filter(
            Game.user_suggested_recommended_number_of_players.like(
                f"%{filters.player_count}%"
            )
        )
    if filters.player_count_filter_type == "Best":
        return query.filter(
            Game.user_suggested_best_number_of_players.like(f"%{filters.player_count}%")
        )


def apply_min_playing_time_filter(query, filters):
    if filters.min_playing_time == DEFAULT_COLLECTION_FILTERS.min_playing_time:
        return query
    return query.filter(Game.min_playing_time >= filters.min_playing_time)


def apply_max_playing_time_filter(query, filters):
    if filters.max_playing_time == DEFAULT_COLLECTION_FILTERS.max_playing_time:
        return query
    return query.filter(Game.max_playing_time <= filters.max_playing_time)


def apply_expansion_filter(query, filters):
    if not filters.include_expansions:
        return query.filter(Game.type != "boardgameexpansion")
    else:
        return query
