const os = require("os");
const process = require("process");
const crypto = require("crypto");

function getPlatformHash(date) {
    const shasum = crypto.createHash("sha1");
    const platform = process.platform;
    const user = process.env.USER || process.env.USERNAME;
    const osType = os.type();
    const cpus = os.cpus();
    const cpuCount = cpus.length;
    const cpuName = cpus[0].model;
    const array = [
        date.toString(),
        platform,
        user,
        osType,
        cpuCount,
        cpuName
    ];

    const osString = array.join(":");
    const hash = shasum.update(osString).digest("base64");

    return hash;
}

module.exports = getPlatformHash;