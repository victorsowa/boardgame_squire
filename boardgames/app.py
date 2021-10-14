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
    setup_db()
    app.run(debug=True)


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
    username = flask.request.form["username"]
    if not check_user_in_database(username):
        add_new_users_collection_to_db(username)
    return flask.redirect(f"/user_collection/{username}")


@app.route("/user_collection/<username>", methods=["GET"])
def collection_get(username):
    default_filter_values = fgs.DEFAULT_COLLECTION_FILTERS
    return flask.render_template(
        "user_collection.html",
        images=fgs.get_games(username),
        username=username,
        filters=default_filter_values,
    )


@app.route("/user_collection/<username>", methods=["POST"])
def collection_post(username):
    filters = fgs.GameCollectionFilters(
        player_count=flask.request.form["player_count"],
        player_count_filter_type=flask.request.form["player_count_filter_type"],
        min_playing_time=flask.request.form["min_playing_time"],
        max_playing_time=flask.request.form["max_playing_time"],
    )

    return flask.render_template(
        "shared/partials/games_list.html", images=fgs.get_games(username, filters)
    )


if __name__ == "__main__":
    # DEBUG is SET to TRUE. CHANGE FOR PROD
    main()
