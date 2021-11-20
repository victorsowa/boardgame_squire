import xml.etree.ElementTree as ET
import html

import pandas as pd


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
