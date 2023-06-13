const fs = require("fs");
const path = require("path");
const yauzl = require("yauzl");
const { promisify } = require("util");
const { PATH_UNPACKED, PATH_MODULES } = require("./constants");
const { IS_WINDOWS_APPS, getSettingPath } = require("./writable-path-utils");

const fsExists = promisify(fs.exists);
const fsOpen = promisify(fs.open);
const fsClose = promisify(fs.close);
const fsMkDir = promisify(fs.mkdir);
const fsUnlink = promisify(fs.rm);
const fsReadDir = promisify(fs.readdir);
const fsCopyFile = promisify(fs.copyFile);

async function needsUnzip() {
    if (!IS_WINDOWS_APPS) return false;

    const pathUnpacked = getSettingPath(PATH_UNPACKED);

    if (await fsExists(pathUnpacked)) return false;

    return true;
}

/**
 *
 * @param {import("./app-window")} win 
 */
async function unzipAssets(win) {
    if (!await needsUnzip()) return;

    const pathUnpacked = getSettingPath(PATH_UNPACKED);

    console.log("Unzipping archive...");

    const pathArchive = `${PATH_MODULES}.bin`;

    if (await fsExists(pathArchive)) await extractZip(win, pathArchive, getSettingPath());
    else await copyArchive(win, PATH_MODULES, getSettingPath());

    console.log("Unpacking done, creating unpacked file...");

    const fd = await fsOpen(pathUnpacked, "w");
    await fsClose(fd);

    console.log("Finished unpacking.");
};

/**
 * 
 * @param {import("./app-window")} win
 * @param {string} pathArchive
 * @param {string} dirOut
 */
async function copyArchive(win, pathArchive, dirOut) {

    const files = await (async function collectFiles(src, dst, files) {
        const entries = await fsReadDir(src, { withFileTypes: true });

        for (let entry of entries) {
            const srcPath = path.join(src, entry.name);
            const dstPath = path.join(dst, entry.name);

            if (entry.isDirectory()) await collectFiles(srcPath, dstPath, files);
            else files.push([srcPath, dstPath]);
        }

        return files;
    })(pathArchive, dirOut, []);

    for (let i = 0, fcount = files.length; i < fcount; i++) {
        const [src, dst] = files[i];

        if (await fsExists(dst)) await fsUnlink(dst);

        const pathDir = path.dirname(dst);

        await fsMkDir(pathDir, { recursive: true });
        await fsCopyFile(src, dst);

        win.sendMessage("sysUnzip", (i + 1) / fcount);
    }
}

/**
 * 
 * @param {import("./app-window")} win
 * @param {string} pathArchive
 * @param {string} dirOut
 */
async function extractZip(win, pathArchive, dirOut) {
    return new Promise((resolve, reject) => {
        yauzl
            .open(pathArchive, { lazyEntries: true }, async function (err, zipfile) {
                win.sendMessage("sysFirstRun");

                if (err) {
                    reject(err);
                    return;
                }

                const fcount = zipfile.entryCount;

                zipfile.readEntry();

                zipfile.on("entry", async function (entry) {
                    const dname = path.resolve(`${dirOut}/${path.dirname(entry.fileName)}`);
                    const fname = path.basename(entry.fileName);

                    await fsMkDir(dname, { recursive: true });

                    if (/\/$/.test(entry.fileName)) {
                        win.sendMessage("sysUnzip", zipfile.entriesRead / fcount);
                        zipfile.readEntry();
                    } else {
                        // file entry
                        zipfile.openReadStream(entry, function (err, readStream) {
                            if (err) {
                                reject(err);
                                return;
                            }

                            const fstream = fs.createWriteStream(`${dname}/${fname}`);

                            readStream.on("end", async function () {
                                fstream.close();
                                win.sendMessage("sysUnzip", zipfile.entriesRead / fcount);
                                zipfile.readEntry();
                            });

                            readStream.pipe(fstream);
                        });
                    }
                });

                zipfile.once("end", function () {
                    zipfile.close();
                    resolve();
                });
            });
    });
}

module.exports = { unzipAssets, needsUnzip };