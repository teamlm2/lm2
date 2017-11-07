#!/usr/bin/python
# -*- coding: utf-8


class LM2Exception(Exception):

    def __init__(self, title, message):

        self.__title = title
        self.__message = message

    def message(self):

        return self.__message

    def title(self):

        return self.__title