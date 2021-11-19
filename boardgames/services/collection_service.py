import time
import xml.etree.ElementTree as ET
import html

import pandas as pd
import requests

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


class BoardgameXMLParser:
    def __init__(self, board_game_element):
        self.board_game_element = board_game_element
        self.type = self.board_game_element.get("type")
        self.id = self.board_game_element.get("id")
        self.title = self._get_attribute_from_element('name[@type="primary"]', "value")

        try:
            self.description = html.unescape(
                self.board_game_element.find("description").text
            )
        except TypeError:
            self.description = None

        self.image = self._get_optional_element("image")
        self.thumbnail = self._get_optional_element("thumbnail")

        self.year_published = self._get_attribute_from_element("yearpublished", "value")
        self.min_players_from_creators = self._get_attribute_from_element(
            "minplayers", "value"
        )
        self.max_players_from_creators = self._get_attribute_from_element(
            "maxplayers", "value"
        )
        self.playing_time = self._get_attribute_from_element("playingtime", "value")
        self.min_playing_time = self._get_attribute_from_element("minplaytime", "value")
        self.max_playing_time = self._get_attribute_from_element("maxplaytime", "value")
        self.min_age = self._get_attribute_from_element("minage", "value")
        self.average_rating = self._get_attribute_from_element(".//average", "value")
        self.bayes_average_rating = self._get_attribute_from_element(
            ".//bayesaverage", "value"
        )
        self.average_weight = self._get_attribute_from_element(
            ".//averageweight", "value"
        )
        self.weight_votes = self._get_attribute_from_element(".//numweights", "value")
        self.board_game_rank = self._get_attribute_from_element(
            './/rank[@name="boardgame"]', "value"
        )

        self.designers = self._get_attributes_from_element(
            'link[@type="boardgamedesigner"]', "value"
        )
        self.mechanics = self._get_attributes_from_element(
            'link[@type="boardgamemechanic"]', "value"
        )
        self.categories = self._get_attributes_from_element(
            'link[@type="boardgamecategory"]', "value"
        )

        (
            suggested_player_poll_element,
            suggested_players_total_votes,
        ) = self._get_poll_results('poll[@name="suggested_numplayers"]')

        if suggested_players_total_votes == 0:
            self.user_suggested_best_number_of_players = ""
            self.user_suggested_recommended_number_of_players = ""
            self.user_suggested_recommended_not_best_number_of_players = ""
        else:
            suggested_player_counts_df = self._get_suggested_player_counts_dataframe(
                suggested_player_poll_element
            )
            suggested_player_counts_df_with_poll_result = (
                self._get_suggested_player_counts_data_with_realtive_amounts(
                    suggested_player_counts_df
                )
            )
            self.user_suggested_best_number_of_players = self._get_best_player_counts(
                suggested_player_counts_df_with_poll_result
            )
            self.user_suggested_recommended_number_of_players = (
                self._get_recommended_player_counts(
                    suggested_player_counts_df_with_poll_result
                )
            )
            self.user_suggested_recommended_not_best_number_of_players = (
                self._get_recommended_player_not_best_counts(
                    suggested_player_counts_df_with_poll_result
                )
            )

    def _get_optional_element(self, element_name):
        try:
            return self.board_game_element.find(element_name).text
        except AttributeError:
            return None

    def _get_attribute_from_element(self, find_string, attribute_name):
        element = self.board_game_element.find(f"{find_string}")
        return element.get(attribute_name)

    def _get_attributes_from_element(self, find_string, attribute_name):
        elements = self.board_game_element.findall(f"{find_string}")
        attributes = [element.get(attribute_name) for element in elements]
        return "|".join(attributes)

    def _get_poll_results(self, poll_pattern):
        poll = self.board_game_element.find(poll_pattern)
        return (poll.findall("results"), int(poll.get("totalvotes")))

    def _get_suggested_player_counts_dataframe(self, suggested_player_poll_element):
        options = []
        for option in suggested_player_poll_element:
            option_row = {"num_players": option.get("numplayers")}
            option_row["best"] = int(
                option.find('result[@value="Best"]').get("numvotes")
            )
            option_row["recommended"] = int(
                option.find('result[@value="Recommended"]').get("numvotes")
            )
            option_row["not_recommended"] = int(
                option.find('result[@value="Not Recommended"]').get("numvotes")
            )
            options.append(option_row)
        return pd.DataFrame(options)

    def _get_suggested_player_counts_data_with_realtive_amounts(
        self, suggested_player_counts_df
    ):
        df = suggested_player_counts_df
        df.loc[
            df["not_recommended"] > df["recommended"] + df["best"], "poll_result"
        ] = "not_recommended"
        df.loc[
            (df["poll_result"] != "not_recommended") & (df["recommended"] < df["best"]),
            "poll_result",
        ] = "best"
        df.loc[
            (df["poll_result"] != "not_recommended") & (df["poll_result"] != "best"),
            "poll_result",
        ] = "recommended"
        return df

    def _get_best_player_counts(self, poll_result):
        best_player_counts = poll_result.loc[
            poll_result["poll_result"] == "best", "num_players"
        ].tolist()
        return "|".join(best_player_counts)

    def _get_recommended_player_counts(self, poll_result):
        recommended_player_counts = poll_result.loc[
            poll_result["poll_result"] != "not_recommended", "num_players"
        ].tolist()
        return "|".join(recommended_player_counts)

    def _get_recommended_player_not_best_counts(self, poll_result):
        recommended_player_counts = poll_result.loc[
            poll_result["poll_result"] == "recommended", "num_players"
        ].tolist()
        return "|".join(recommended_player_counts)


def insert_user_into_database(username):
    session = db_session.create_session()
    user = User(name=username)
    session.add(user)
    session.commit()


def check_user_in_database(username):
    session = db_session.create_session()
    user_in_database = session.query(User).filter(User.name == username).first()
    return user_in_database is not None


def insert_user_games_into_database(username, data_list):
    session = db_session.create_session()
    user_id_from_name = session.query(User.id).filter(User.name == username).first()
    user_games_to_be_inserted = []
    for user_game in data_list:
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
    print("games already in db", games_already_in_db)

    print(
        len(
            [game_id for game_id in game_ids if int(game_id) not in games_already_in_db]
        ),
        len(game_ids),
    )
    return [game_id for game_id in game_ids if int(game_id) not in games_already_in_db]


def get_general_game_data_from_boardgamegeek(game_ids):
    print(len(game_ids), type(game_ids))
    if len(game_ids) > 1000:
        game_ids_in_sublists = [
            game_ids[i : i + 1000] for i in range(0, len(game_ids), 1000)
        ]
        game_objects = []
        for sublist in game_ids_in_sublists:
            print("len", len(sublist), sublist)
            games_request = get_games_from_game_ids(sublist)
            games_et = get_xml_string_from_response(games_request)
            game_objects += [BoardgameXMLParser(game) for game in games_et]
        return game_objects
    else:
        games_request = get_games_from_game_ids(game_ids)
        games_et = get_xml_string_from_response(games_request)
        return [BoardgameXMLParser(game) for game in games_et]


def add_new_users_collection_to_db(username):
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

    game_ids = [game_id for game_id, _ in user_games]
    unique_game_ids_not_already_in_database = prepare_set_of_games_not_already_in_db(
        game_ids
    )

    insert_board_game_info(unique_game_ids_not_already_in_database)
    insert_user_into_database(username)
    insert_user_games_into_database(username, user_games)


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
