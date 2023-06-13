const path = require("path");

const BASE_DIR = path.join(__dirname, "../..");

function getAssetPath(pathAsset) {
    return path.resolve(path.join(BASE_DIR, pathAsset));
}

module.exports = getAssetPath;