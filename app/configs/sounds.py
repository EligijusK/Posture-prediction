from app.configs.section import Section


class Sounds(Section):
    def __init__(self, parser):
        DEFAULT_VALUES = [
            ("ENABLE_SOUND", True),
            ("ENABLE_NOTIFICATIONS", True),
            ("WARNING_DELAY", 120)
        ]

        super(Sounds, self).__init__("SOUND", parser, DEFAULT_VALUES)

    @property
    def ENABLE_NOTIFICATIONS(self): return self.get_value("ENABLE_NOTIFICATIONS", bool)
    @property
    def ENABLE_SOUND(self): return self.get_value("ENABLE_SOUND", bool)
    @property
    def WARNING_DELAY(self): return self.get_value("WARNING_DELAY", int)

    @ENABLE_NOTIFICATIONS.setter
    def ENABLE_NOTIFICATIONS(self, value): return self.set_value("ENABLE_NOTIFICATIONS", value)
    @ENABLE_SOUND.setter
    def ENABLE_SOUND(self, value): return self.set_value("ENABLE_SOUND", value)
    @WARNING_DELAY.setter
    def WARNING_DELAY(self, value): return self.set_value("WARNING_DELAY", value)