from db import DatabaseOperation
from flask_login import UserMixin

class UserLogin(UserMixin):
    def __init__(self):
        self.__user = None

    def from_db(self, user_id, db):
        operation = DatabaseOperation(db)
        self.__user = operation.get_data(f"select * from Account where Id = '{user_id}'")
        return self

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user[0][0])
