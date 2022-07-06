import os
import shutil
from db import *
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from UserLogin import UserLogin
from flask import Flask, render_template, request, flash, session, url_for, redirect, g, abort

# Configuration
SECRET_KEY = "th985y3489th34yutjfngrjkejhi43utirorjt348tyh4"

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(DATABASE=os.path.join(app.root_path, "flsite.db")))

database = Database(app, g)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Увійдіть до облікового запису виконавця"

app.jinja_env.globals.update(database=database)
app.jinja_env.globals.update(DatabaseOperation=DatabaseOperation)


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().from_db(user_id, database.get_db())

@app.route("/")
def index():
    return render_template("index.html", title="Головна сторінка")


@app.route("/groupHistory.html")
def groupHistory():
    return render_template("groupHistory.html", title="Історія групи")


@app.route("/aboutProject.html")
def about_project():
    return render_template("aboutProject.html", title="Про проект")


@app.route("/albums.html")
def albums():
    return render_template("albums.html", title="Альбоми")


@app.route("/albums/<album_name>")
def about_album(album_name):
    db_operation = DatabaseOperation(database.get_db())
    current_album_name = album_name.replace("_deleted", "")
    tracks = db_operation.get_tracks(current_album_name)
    album = db_operation.get_album(current_album_name)

    if album:
        if "_deleted" in album_name:
            if current_user.is_anonymous:
                abort(404)

            db_operation.change_db(f"delete from Song where PlaylistId = ?", (album[0][0], ))
            db_operation.change_db(f"delete from Playlist where Id = ?", (album[0][0], ))
            db_operation.change_db(f"update sqlite_sequence set seq = seq - 1 where name = 'Playlist'", None)
            db_operation.change_db(
                f"update sqlite_sequence set seq = seq - :num where name = 'Song'", {"num": len(tracks)})

            if os.path.isdir(f"static/{current_album_name}"):
                shutil.rmtree(f"static/{current_album_name}")

            return redirect(url_for("albums"))

        return render_template("aboutAlbums.html", title=f"{current_album_name}",
                               name=album_name, image=album[0][2], tracks=tracks)
    abort(404)


@app.route("/login.html", methods=["POST", "GET"])
def login():
    db = database.get_db()
    db_operation = DatabaseOperation(db)

    if request.method == "POST":
        print(request.form)
        data = db_operation.get_data(
            f"select * from Account where Login = '{request.form['login']}' and "
            f"Password = '{request.form['password']}'")

        if data:
            userlogin = UserLogin().create(data)

            login_user(userlogin)
            return redirect(request.args.get("next") or url_for("index"))

        flash("Логін або пароль введено неправильно", category="error")

    return render_template("login.html", title="Вхід")


@app.route("/add_new_album.html", methods=["POST", "GET"])
@login_required
def add_new_album():
    if request.method == "POST":
        if request.files:
            album_name = request.form["album_name"]
            album_image = request.files["album_image"]
            image_path = f"{album_name}/{album_name}_image.jpg"

            if not os.path.isdir(f"static/{album_name}"):
                os.makedirs(f"static/{album_name}", mode=0o777)
            else:
                flash("Такий альбом вже існує", category="error")
                return redirect(url_for("add_new_album"))

            with open("static/" + image_path, mode="wb") as image_file:
                image_file.write(album_image.read())

            db_operation = DatabaseOperation(database.get_db())
            db_operation.change_db(
                f"insert into Playlist (Name, Path) "
                f"values (?, ?)", (album_name, image_path))

            try:
                for i in range(1, len(request.files)):
                    path = f"{album_name}/{request.form[f'track_name{i}']}.wav"

                    with open("static/" + path, mode="wb") as audio:
                        audio.write(request.files[f"track{i}"].read())

                    album_id = db_operation.get_data(f"select Id from Playlist order by Id desc limit 1")
                    db_operation.change_db(f"insert into Song (Name, Path, PlaylistId) "
                                             f"values (?, ?, ?)",
                                             (request.form[f'track_name{i}'],
                                              path, album_id[0][0]))
            except:
                pass

    return render_template("add_new_album.html", title="Новий альбом")


@app.route("/logout.html")
@login_required
def logout():
    logout_user()
    return render_template("logout.html", title="Вихід")


@app.errorhandler(404)
def page_not_found(error):
    return render_template("error_page.html", title="Невідома сторінка")


@app.teardown_appcontext
def close_db(error):
    database.close_connection()


if __name__ == "__main__":
    app.run()

