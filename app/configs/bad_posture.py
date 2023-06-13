from app.configs.notification_section import NotificationSection


class BadPosture(NotificationSection):
    def __init__(self, parser):
        super(BadPosture, self).__init__("BAD_POSTURE", parser)
