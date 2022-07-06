import sqlite3

class Database:
    __slots__ = "__path", "__app", "__g"

    def __init__(self, app, g):
        self.__path = app.config["DATABASE"]
        self.__app = app
        self.__g = g

    def __connect_db(self):
        connection = sqlite3.connect(self.__path)
        return connection

    def create_db(self):
        db = self.__connect_db()
        with self.__app.open_resource("database.sql", mode="r") as sql_f:
            db.cursor().executescript(sql_f.read())
        db.commit()
        db.close()

    def get_db(self):
        if not hasattr(self.__g, "link_db"):
            self.__g.link_db = self.__connect_db()

        return self.__g.link_db

    def close_connection(self):
        if hasattr(self.__g, "link_db"):
            self.__g.link_db.close()


class DatabaseOperation:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    @property
    def db(self):
        return self.__db

    @db.setter
    def db(self, value):
        if value is not sqlite3.Connection:
            raise ValueError("Value must have type Connection")

        self.__db = value
        self.__cur = self.__db.cursor()

    def get_data(self, sql_command):
        res = []
        try:
            self.__cur.execute(sql_command)
            res = self.__cur.fetchall()
        except sqlite3.Error as e:
            print("Error reading from database", e, sep="\n")
        finally:
            return res

    def change_db(self, sql_command, params):
        try:
            if params is None:
                self.__cur.execute(sql_command)
            else:
                self.__cur.execute(sql_command, params)

            self.__db.commit()
        except sqlite3.Error as e:
            print("Error inserting in database", e, sep="\n")

    def get_albums(self):
        select_res = self.get_data(f"select * from Playlist")
        res = {}

        for i in range(1, len(select_res) + 1):
            res[f"Album{i}"] = select_res[i - 1]

        return res

    def get_album(self, name):
        select_res = self.get_data(f"select * from Playlist where Name = '{name}'")
        return select_res

    def get_tracks(self, album):
        select_res = self.get_data(f"select s.Name, s.Path from Song as s "
                                   f"left join Playlist as p "
                                   f"on s.PlaylistId = p.Id "
                                   f"where p.Name = '{album}'")
        return select_res

