__author__ = 'mwagner'

from ..utils.SessionHandler import SessionHandler


class DatabaseHelper():

    def __init__(self):

        self.__transaction_count = 1

    def create_savepoint(self):

        session = SessionHandler().session_instance()
        session.begin_nested()
        self.__transaction_count += 1

    def rollback_to_savepoint(self):

        session = SessionHandler().session_instance()
        session.rollback()
        self.__transaction_count -= 1

    def rollback(self):

        session = SessionHandler().session_instance()
        for idx in range(self.__transaction_count):
            session.rollback()

        self.__transaction_count = 1

    def commit(self):

        session = SessionHandler().session_instance()
        for idx in range(self.__transaction_count):
            session.commit()

        self.__transaction_count = 1