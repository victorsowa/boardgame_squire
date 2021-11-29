import time
import xml.etree.ElementTree as ET

import requests

from .boardgame_xml_parser import BoardgameXMLParser
import boardgames.data.db_session as db_session
from boardgames.data.games import Game
from boardgames.data.users import User
from boardgames.data.user_games import UserGame

BASE_URI = "https://www.boardgamegeek.com/xmlapi2/"


def get_users_collection(username):
    collections_endpoint = BASE_URI + "collection?"
    parameters = f"username={username}&stats=1&own=1"
    return requests.get(collections_endpoint + parameters)


def get_xml_string_from_response(response):
    return ET.fromstring(response.text)


def get_game_ids_from_collection(collection_element_tree):
    return [child.attrib["objectid"] for child in collection_element_tree]


def get_user_ratings_from_collection(collection_element_tree):
    user_ratings_from_xml = [
        child.find(".//rating").get("value") for child in collection_element_tree
    ]
    return [
        None if user_rating == "N/A" else user_rating
        for user_rating in user_ratings_from_xml
    ]


def get_games_from_game_ids(game_ids):
    comma_seperated_game_ids = ",".join(game_ids)
    thing_endpoint = BASE_URI + "thing?"
    parameters = f"id={comma_seperated_game_ids}&stats=1"
    return requests.get(thing_endpoint + parameters)


def insert_user_into_database(username):
    session = db_session.create_session()
    user = User(name=username)
    session.add(user)
    session.commit()


def check_user_in_database(username):
    session = db_session.create_session()
    user_in_database = session.query(User).filter(User.name == username).first()
    return user_in_database is not None


def insert_user_games_into_database(username, user_games):
    session = db_session.create_session()
    user_id_from_name = session.query(User.id).filter(User.name == username).first()
    user_games_to_be_inserted = []
    for user_game in user_games:
        ug = UserGame(
            user_id=user_id_from_name[0],
            bgg_game_id=user_game[0],
            user_rating=user_game[1],
        )
        user_games_to_be_inserted.append(ug)
    session.bulk_save_objects(user_games_to_be_inserted)

    session.commit()


def get_user_games_from_boardgamegeek(username):
    collection = get_users_collection(username)
    collection_et = get_xml_string_from_response(collection)
    print(collection_et.text.strip())
    try:
        if collection_et.find(".//message").text == "Invalid username specified":
            return "invalid username"
    except AttributeError:
        pass
    try:
        if (
            collection_et.text.strip()
            == "Your request for this collection has been accepted and will be processed.  Please try again later for access."
        ):
            return "waiting"
    except AttributeError:
        pass
    user_game_ids = get_game_ids_from_collection(collection_et)
    user_ratings = get_user_ratings_from_collection(collection_et)
    return list(set(zip(user_game_ids, user_ratings)))


def get_game_ids_not_currently_in_db(game_ids):
    session = db_session.create_session()
    games_already_in_db = (
        session.query(Game.bgg_game_id).filter(Game.bgg_game_id.in_(game_ids)).all()
    )
    games_already_in_db = [game[0] for game in games_already_in_db]

    return [game_id for game_id in game_ids if int(game_id) not in games_already_in_db]


def get_user_games_not_currently_in_db(username, user_games):
    session = db_session.create_session()
    bgg_game_ids = [int(user_game[0]) for user_game in user_games]

    user_id = session.query(User.id).filter(User.name == username).first()[0]

    user_games_bgg_id_in_db = (
        session.query(UserGame.bgg_game_id)
        .filter(UserGame.user_id == user_id)
        .filter(UserGame.bgg_game_id.in_(bgg_game_ids))
        .all()
    )
    print(user_games_bgg_id_in_db)
    user_games_bgg_id_in_db = [game[0] for game in user_games_bgg_id_in_db]
    user_game_ids_in_db_but_not_in_collection = [
        db_user_game_id
        for db_user_game_id in user_games_bgg_id_in_db
        if db_user_game_id not in bgg_game_ids
    ]
    user_games_not_in_db = [
        user_game
        for user_game in user_games
        if int(user_game[0]) not in user_games_bgg_id_in_db
    ]
    return (user_games_not_in_db, user_game_ids_in_db_but_not_in_collection)


def remove_user_games_in_database(username, user_game_ids_to_remove):
    session = db_session.create_session()
    user_id = session.query(User.id).filter(User.name == username).first()[0]

    session.query(UserGame).filter(UserGame.user_id == user_id).filter(
        UserGame.bgg_game_id.in_(user_game_ids_to_remove)
    ).delete(synchronize_session=False)

    session.commit()


def get_general_game_data_from_boardgamegeek(game_ids):
    if len(game_ids) > 1000:
        game_ids_in_sublists = [
            game_ids[i : i + 1000] for i in range(0, len(game_ids), 1000)
        ]
        game_objects = []
        for sublist in game_ids_in_sublists:
            games_request = get_games_from_game_ids(sublist)
            games_et = get_xml_string_from_response(games_request)
            game_objects += [BoardgameXMLParser(game) for game in games_et]
        return game_objects
    else:
        games_request = get_games_from_game_ids(game_ids)
        games_et = get_xml_string_from_response(games_request)
        return [BoardgameXMLParser(game) for game in games_et]


def add_new_users_collection_to_db(username, user_exists=False):
    username = username.lower()
    num_tries = 5
    for try_ in range(num_tries):
        user_games = get_user_games_from_boardgamegeek(username)
        if user_games == "invalid username":
            return "invalid username"
        elif user_games == "waiting":
            time.sleep(5)
            print("waiting for boardgamegeek")
        else:
            break

    if user_exists:
        (
            user_games_not_in_db,
            user_game_ids_in_db_but_not_in_collection,
        ) = get_user_games_not_currently_in_db(username, user_games)

    game_ids = [game_id for game_id, _ in user_games]
    unique_game_ids_not_already_in_database = prepare_set_of_games_not_already_in_db(
        game_ids
    )

    insert_board_game_info(unique_game_ids_not_already_in_database)
    if not user_exists:
        insert_user_into_database(username)
        insert_user_games_into_database(username, user_games)
    else:
        insert_user_games_into_database(username, user_games_not_in_db)
        remove_user_games_in_database(
            username, user_game_ids_in_db_but_not_in_collection
        )


def prepare_set_of_games_not_already_in_db(game_ids):
    game_ids_not_already_in_database = get_game_ids_not_currently_in_db(game_ids)
    return list(set(game_ids_not_already_in_database))


def insert_board_game_info(game_ids):
    if game_ids is None:
        return
    general_game_data_for_user_games = get_general_game_data_from_boardgamegeek(
        game_ids
    )
    session = db_session.create_session()
    games_to_be_inserted = []
    for i, bg in enumerate(general_game_data_for_user_games):

        bg_sql = Game(
            bgg_game_id=bg.id,
            title=bg.title,
            type=bg.type,
            description=bg.description,
            year_published=bg.year_published,
            image_url=bg.image,
            thumbnail_url=bg.thumbnail,
            min_players=bg.min_players_from_creators,
            max_players=bg.max_players_from_creators,
            playing_time=bg.playing_time,
            min_playing_time=bg.min_playing_time,
            max_playing_time=bg.max_playing_time,
            min_age=bg.min_age,
            average_rating=bg.average_rating,
            bayes_average_rating=bg.bayes_average_rating,
            board_game_rank=bg.board_game_rank,
            average_weight=bg.average_weight,
            weight_votes=bg.weight_votes,
            designers=bg.designers,
            mechanics=bg.mechanics,
            categories=bg.categories,
            user_suggested_best_number_of_players=bg.user_suggested_best_number_of_players,
            user_suggested_recommended_number_of_players=bg.user_suggested_recommended_number_of_players,
            user_suggested_recommended_not_best_number_of_players=bg.user_suggested_recommended_not_best_number_of_players,
        )
        games_to_be_inserted.append(bg_sql)

    session.bulk_save_objects(games_to_be_inserted)

    session.commit()
