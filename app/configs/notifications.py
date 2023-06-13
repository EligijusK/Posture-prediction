from app.configs.section import Section


class Notifications(Section):
    def __init__(self, parser):
        DEFAULT_VALUES = [
            ("ENABLE_NOTIFICATIONS", True),
            ("NOTIFICATION_DELAY", 120),
            ("TIME_OUT", 30)
        ]

        super(Notifications, self).__init__("NOTIFICATIONS", parser, DEFAULT_VALUES)

    @property
    def ENABLE_NOTIFICATIONS(self): return self.get_value("ENABLE_NOTIFICATIONS", bool)
    @property
    def NOTIFICATION_DELAY(self): return self.get_value("NOTIFICATION_DELAY", int)
    @property
    def TIME_OUT(self): return self.get_value("TIME_OUT", int)

    @ENABLE_NOTIFICATIONS.setter
    def ENABLE_NOTIFICATIONS(self, value): return self.set_value("ENABLE_NOTIFICATIONS", value)
    @NOTIFICATION_DELAY.setter
    def NOTIFICATION_DELAY(self, value): return self.set_value("NOTIFICATION_DELAY", value)
    @TIME_OUT.setter
    def TIME_OUT(self, value): return self.set_value("TIME_OUT", value)
