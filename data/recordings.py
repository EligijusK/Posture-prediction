import json


class Person:
    def __init__(self, data):
        self.id = data["id"]
        self.angle = data["angle"]
        self.gender = data["gender"]
        self.person_id = data["person"]


class Recordings:
    def __init__(self, path):
        self.__recordings = {}

        with open(path, "r") as f:
            for data in json.load(f):
                self.__recordings[data["id"]] = Person(data)

    def get_person(self, id):
        return self.__recordings[id] if id in self.__recordings else None
