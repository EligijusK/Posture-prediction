from app.configs.section import Section


class Models(Section):
    def __init__(self, parser):
        DEFAULT_VALUES = [
            ("PATH_CHECKPOINT", "./model/model.xth"),
            ("PATH_MODEL", "./model"),

            ("CALIBRATION_ENABLED", True),
            ("CALIBRATION_HISTORY", 20),
            ("CALIBRATION_SIZE", 60),
            ("CALIBRATION_BOUNDS", "2147483647,2147483647,-2147483647,-2147483647")
        ]

        super(Models, self).__init__("MODEL", parser, DEFAULT_VALUES)

    @property
    def PATH_MODEL(self): return self.get_value("PATH_MODEL")

    @property
    def PATH_CHECKPOINT(self): return self.get_value("PATH_CHECKPOINT")

    @property
    def CALIBRATION_HISTORY(self): return self.get_value("CALIBRATION_HISTORY", int)

    @property
    def CALIBRATION_SIZE(self): return self.get_value("CALIBRATION_SIZE", int)
    @property
    def CALIBRATION_BOUNDS(self): return self.get_value("CALIBRATION_BOUNDS", str)

    @property
    def CALIBRATION_ENABLED(self): return self.get_value("CALIBRATION_ENABLED", str)

    @CALIBRATION_HISTORY.setter
    def CALIBRATION_HISTORY(self, value): return self.set_value("CALIBRATION_HISTORY", value)

    @CALIBRATION_SIZE.setter
    def CALIBRATION_SIZE(self, value): return self.set_value("CALIBRATION_SIZE", value)

    @CALIBRATION_ENABLED.setter
    def CALIBRATION_ENABLED(self, value): return self.set_value("CALIBRATION_ENABLED", value)

    @CALIBRATION_BOUNDS.setter
    def CALIBRATION_BOUNDS(self, value): return self.set_value("CALIBRATION_BOUNDS", value)
