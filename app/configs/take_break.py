from app.configs.notification_section import NotificationSection


class TakeBreak(NotificationSection):
    def __init__(self, parser):
        super(TakeBreak, self).__init__("TAKE_BREAK", parser)
