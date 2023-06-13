from configparser import ConfigParser as _ConfigParser


class Section:
    def __init__(self, section: str, parser: _ConfigParser, default_values):
        self.__section = section
        self.__parser = parser

        if section not in parser:
            parser.add_section(section)

        for key, value in default_values:
            if not self.has_value(key):
                self.set_value(key, value)

    def has_value(self, key):
        return self.__parser.has_option(self.__section, key)

    def get_value(self, key, type="str"):
        if type == int:
            return self.__parser.getint(self.__section, key)
        elif type == bool:
            return self.__parser.getboolean(self.__section, key)
        elif type == float:
            return self.__parser.getfloat(self.__section, key)
        else:
            return self.__parser.get(self.__section, key)

    def set_value(self, key, value):
        return self.__parser.set(self.__section, key, str(value))