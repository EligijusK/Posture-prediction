const _path = require("path");
const app = require("electron");

const IS_WINDOWS_APPS = /\\WindowsApps/.test(__dirname);

function getSettingPath(path = "") {
    return IS_WINDOWS_APPS && process.env.APPDATA
        ? _path.resolve(`${process.env.APPDATA}/SitYEA/${path}`)
        : _path.resolve(path);
}

function getMacPathModules(path = "") {
    realPath = app.app.getAppPath();
    array = realPath.split('/')
    array = array.slice(0, array.length - 2);
    resultPath = array.join('/')
    return resultPath + "/" + path;
}

function getSettingPathMac(path = ""){
    return app.app.getAppPath() + "/" + path;
}

function getTrueSettingsPath(path = "") {
    let settingsPath = getSettingPath(path);

    if (!IS_WINDOWS_APPS) return settingsPath;

    const regexp = /WindowsApps\\(?<appname>[\w\d\.]+)_(?<version>\d+\.\d+\.\d+\.\d+)_(?<arch>x\d{2})_(?<unk>)_(?<apphash>[\w\d]+)/;
    const match = __dirname.match(regexp);

    return settingsPath.replace(
        "\\AppData\\",
        `\\AppData\\Local\\Packages\\${match.groups.appname}_${match.groups.apphash}\\LocalCache\\`
    );
}

async function createWritableDirs() {
    const fs = require("fs");
    const { promisify } = require("util");

    const fsExists = promisify(fs.exists);
    const fsMkdir = promisify(fs.mkdir);

    const dirname = getSettingPath();

    if (await fsExists(dirname)) return null;

    return await fsMkdir(dirname, { recursive: true });
}

module.exports = {
    IS_WINDOWS_APPS,
    getMacPathModules,
    getSettingPath,
    getSettingPathMac,
    createWritableDirs,
    getTrueSettingsPath
};