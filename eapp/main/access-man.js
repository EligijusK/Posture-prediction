const fs = require("fs");
const { promisify } = require("util");
const { ipcMain } = require("electron");
const { PATH_ACCESS, PASS_CORRECT, PASS_TIME } = require("./constants");
const getPlatformHash = require("./platform-hash");
const { getSettingPath } = require("./writable-path-utils");

const fsExists = promisify(fs.exists);
const fsReadFile = promisify(fs.readFile);
const fsWriteFile = promisify(fs.writeFile);


async function checkAccess() {
    try {
        const accessPath = await fsExists(PATH_ACCESS)
            ? PATH_ACCESS
            : await fsExists(getSettingPath(PATH_ACCESS))
                ? getSettingPath(PATH_ACCESS)
                : null;

        if (accessPath === null) return false;

        const { passwordAccess, allowedUntil, sysHash } = JSON.parse(await fsReadFile(PATH_ACCESS, "UTF-8"));

        if (passwordAccess === PASS_CORRECT) return true;

        const validateHash = getPlatformHash(allowedUntil);

        if (validateHash !== sysHash) return false;

        return Date.now() < allowedUntil;
    } catch (e) { return false; }
}

async function addPasswordListener(onCorrectPassword) {
    async function onPasswordEvent(ev, password) {
        if (password === "#CHECK_ACCESS#") {
            onCorrectPassword();
            return;
        } else if (password !== PASS_CORRECT) {
            ev.reply("sysPassword-incorrect");
            return;
        }

        const allowedUntil = Date.now() + PASS_TIME;
        const sysHash = getPlatformHash(allowedUntil);
        const sysKey = { allowedUntil, sysHash };

        await fsWriteFile(PATH_ACCESS, JSON.stringify(sysKey));

        onCorrectPassword();
    }

    ipcMain.on("sysPassword", onPasswordEvent);
}

module.exports = { checkAccess, addPasswordListener };