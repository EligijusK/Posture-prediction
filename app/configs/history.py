from app.configs.section import Section


class History(Section):
    def __init__(self, parser):
        DEFAULT_VALUES = [
            ("TIME_PREDICTION", 15),
            ("HISTORY_BUCKET_SIZE", 20),
            ("HISTORY_BUCKET_COUNT", 20)
        ]

        super(History, self).__init__("HISTORY", parser, DEFAULT_VALUES)

    @property
    def TIME_PREDICTION(self): return self.get_value("TIME_PREDICTION", int)
    @property
    def HISTORY_BUCKET_SIZE(self): return self.get_value("HISTORY_BUCKET_SIZE", int)
    @property
    def HISTORY_BUCKET_COUNT(self): return self.get_value("HISTORY_BUCKET_COUNT", int)

    @TIME_PREDICTION.setter
    def TIME_PREDICTION(self, value): return self.set_value("TIME_PREDICTION", value)
    @HISTORY_BUCKET_SIZE.setter
    def HISTORY_BUCKET_SIZE(self, value): return self.set_value("HISTORY_BUCKET_SIZE", value)
    @HISTORY_BUCKET_COUNT.setter
    def HISTORY_BUCKET_COUNT(self, value): return self.set_value("HISTORY_BUCKET_COUNT", value)