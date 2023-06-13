from app.configs.section import Section


class NotificationSection(Section):
    def __init__(self, section_name, parser):
        DEFAULT_VALUES = [
            ("NOTIFICATION_SOUND", True),
            ("NOTIFICATION_DESKTOP", True),
            ("NOTIFICATION_TIME", 30)
        ]

        super(NotificationSection, self).__init__(section_name, parser, DEFAULT_VALUES)

    @property
    def NOTIFICATION_SOUND(self): return self.get_value("NOTIFICATION_SOUND", bool)
    @property
    def NOTIFICATION_DESKTOP(self): return self.get_value("NOTIFICATION_DESKTOP", bool)
    @property
    def NOTIFICATION_TIME(self): return self.get_value("NOTIFICATION_TIME", int)

    @NOTIFICATION_SOUND.setter
    def NOTIFICATION_SOUND(self, value): return self.set_value("NOTIFICATION_SOUND", value)
    @NOTIFICATION_DESKTOP.setter
    def NOTIFICATION_DESKTOP(self, value): return self.set_value("NOTIFICATION_DESKTOP", value)
    @NOTIFICATION_TIME.setter
    def NOTIFICATION_TIME(self, value): return self.set_value("NOTIFICATION_TIME", value)
