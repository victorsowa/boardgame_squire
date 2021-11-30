import sys
import os

import flask
import jinja_partials

folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, folder)

import boardgames.data.db_session as db_session
import boardgames.services.filtered_games_service as fgs
from boardgames.services.collection_service import (
    add_new_users_collection_to_db,
    check_user_in_database,
)

app = flask.Flask(__name__)
jinja_partials.register_extensions(app)


def main():
    configure()
    app.run()


def configure():
    print("Setting up db")
    setup_db()


def setup_db():
    db_file = os.path.join(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "db.sqlite")
    )
    print(db_file)
    db_session.global_init(db_file)


@app.route("/", methods=["GET"])
def index_get():
    return flask.render_template("index.html")


@app.route("/", methods=["POST"])
def index_post():
    username = flask.request.form["username"].lower()
    if not check_user_in_database(username):
        add_new_users_collection_to_db(username)
    return flask.redirect(f"/user_collection/{username}")


@app.route("/user_collection/<username>", methods=["GET"])
def collection_get(username):
    games = fgs.get_games(username)
    sorted_games = fgs.sort_filtered_games(games, "Title", "asc")
    collection_stats = fgs.get_collection_stats(games)
    sorting_options = fgs.SORTING_FIELDS.keys()
    possible_mechanics = fgs.get_unique_from_sperated_pipe_seperatedcolumns(
        games, "mechanics"
    )
    possible_categories = fgs.get_unique_from_sperated_pipe_seperatedcolumns(
        games, "categories"
    )
    possible_designers = fgs.get_unique_from_sperated_pipe_seperatedcolumns(
        games, "designers"
    )

    return flask.render_template(
        "user_collection.html",
        images=sorted_games,
        collection_stats=collection_stats,
        username=username,
        sorting_options=sorting_options,
        possible_categories=possible_categories,
        possible_mechanics=possible_mechanics,
        possible_designers=possible_designers,
    )


@app.route("/user_collection/<username>", methods=["POST"])
def collection_post(username):
    filters = create_collection_filter(flask.request.form)
    filtered_games = fgs.get_games(username, filters)
    sorted_games = fgs.sort_filtered_games(
        filtered_games, filters.sort_field, filters.sort_type
    )
    collection_stats = fgs.get_collection_stats(filtered_games)

    return flask.render_template(
        "shared/partials/games_list.html",
        images=sorted_games,
        collection_stats=collection_stats,
    )


@app.route("/user_collection/<username>/refresh", methods=["GET"])
def refresh_user_collection(username):
    add_new_users_collection_to_db(username, user_exists=True)
    return flask.redirect(f"/user_collection/{username}")


def create_collection_filter(form):
    return fgs.GameCollectionFilters(
        player_count=form["player_count"],
        player_count_filter_type=form["player_count_filter_type"],
        min_playing_time=form["min_playing_time"],
        max_playing_time=form["max_playing_time"],
        min_weight=form["min_weight"],
        max_weight=form["max_weight"],
        category=form["category"],
        mechanic=form["mechanic"],
        designer=form["designer"],
        include_expansions=form.get("include_expansions", False),
        sort_field=form["sort_field"],
        sort_type=form["sort_type"],
    )


if __name__ == "__main__":
    # DEBUG is SET to TRUE. CHANGE FOR PROD
    main()
else:
    configure()
