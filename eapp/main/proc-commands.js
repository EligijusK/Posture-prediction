const { createWritableDirs, getSettingPathMac, getTrueSettingsPath, getMacPathModules } = require("./writable-path-utils");
// const commandRS = ["python3.10", "module_rs.py"];
const commandRS = [getMacPathModules("Projektai/Posture-prediction/Executable/SitYEA/js/SitYEA.app/Contents/Frameworks/modules.app/Contents/MacOS/module_rs")];
const commandMDL = ["python3.10", "module_mdl.py"];
const commandNotify = ["python3.10", "module_notify.py"];

module.exports = { commandRS, commandMDL, commandNotify };