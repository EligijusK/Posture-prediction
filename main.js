const electron = require("electron");

electron.app.commandLine.appendSwitch('high-dpi-support', 1);
electron.app.commandLine.appendSwitch('force-device-scale-factor', 1);


const path = require("path");
const fs = require("fs");
const { promisify } = require("util");
const fappend = promisify(fs.appendFile);
const { createWritableDirs, IS_WINDOWS_APPS } = require("./eapp/main/writable-path-utils");
const { PATH_LOG_ERROR, PATH_LOG_CONSOLE } = require("./eapp/main/constants");
const { getConfigManager } = require("./eapp/main/config-man");
const sendCrashLog = require("./eapp/main/submit-crash");
const fsExists = promisify(fs.exists);
const fsUnlink = promisify(fs.unlink);


if (IS_WINDOWS_APPS) process.chdir(path.dirname(process.argv0));

async function writeError(tag, error) {
    await createWritableDirs();

    const errString = `[${new Date().toISOString()}] ${tag}\n${error.stack}`;
    console.error(errString);
    console.trace();
    await fappend(PATH_LOG_ERROR, `${errString}\n\n`);

    const manCfg = getConfigManager();

    if (!manCfg || manCfg.settings.sendLogs) await sendCrashLog();
}

async function _writeLog(tag, fn, ...args) {
    await createWritableDirs();

    const str = args.join("\n");
    const fstring = `[${tag} ${new Date().toISOString()}] \n${str}`;
    this[fn](str);
    await fappend(PATH_LOG_CONSOLE, `${fstring}\n\n`);
}


(async function () {
    if (await fsExists(PATH_LOG_ERROR)) await fsUnlink(PATH_LOG_ERROR);
    if (await fsExists(PATH_LOG_CONSOLE)) await fsUnlink(PATH_LOG_CONSOLE);

    console._log = console.log;
    console._error = console.error;
    console._info = console.info;
    console._warn = console.warn;
    console.log = _writeLog.bind(console, "LOG", "_log");
    console.error = _writeLog.bind(console, "ERROR", "_error");
    console.info = _writeLog.bind(console, "INFO", "_info");
    console.warn = _writeLog.bind(console, "WARN", "_warn");

    process
        .on("unhandledRejection", async function (error) { await writeError("Uncaught promise", error); process.exit(1); })
        .on("uncaughtException", async function (error) { await writeError("Uncaught error", error); process.exit(1); });

    require("./eapp/main/add-reloader");

    await electron.app.whenReady();

    electron.app.commandLine.appendSwitch("high-dpi-support", 1);
    electron.app.commandLine.appendSwitch("force-device-scale-factor", 1);

    const runApp = require("./eapp/main/app");

    runApp();
})();