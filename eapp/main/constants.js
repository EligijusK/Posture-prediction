const { getSettingPathMac, getMacPathModules } = require("./writable-path-utils");

const CONSTANTS = {
    COUNT_GROUPS: 20,
    COUNT_STEPS: 20,
    DEPTH_MAX: 1.5,

    PATH_UNPACKED: ".unpacked",
    PATH_MODULES: "python_modules",

    PATH_ACCESS: ".access",
    PASS_CORRECT: "20210309",
    PASS_TIME: 60 * 60 * 24 * 30 * 3 * 1000,

    PATH_SETTINGS: getSettingPathMac(".configs"),
    PATH_CALIBRATION: getSettingPathMac(".calibration"),
    PATH_HISTORY: getSettingPathMac(".history"),
    PATH_RAM: ".sock",
    PATH_RAM_2: ".sock_2",
    PATH: getMacPathModules(""),

    PATH_LOG_ERROR: getSettingPathMac("error.log"),
    PATH_LOG_CONSOLE: getSettingPathMac("console.log")
};

module.exports = CONSTANTS;