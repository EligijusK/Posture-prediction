const { NAMESPACE_SVG } = require("../constants");

class HistoryHourly {
    _rects = [];
    _width;
    _height;

    constructor(domElement, appSettings, hourly) {
        const { width, height } = domElement.getBoundingClientRect();
        const svg = document.createElementNS(NAMESPACE_SVG, "svg");

        this._width = Math.round(width);
        this._height = Math.round(height);
        this._appSettings = appSettings;
        this._domElement = domElement;
        this._values = hourly;

        const { bucketCount, bucketSize } = appSettings.settings.history;
        const totalGroups = bucketCount * 2;
        const groupWidth = width / (totalGroups - 1);
        const blockHeight = height / bucketSize;

        console.log("start", width, height)

        for (let i = 0; i < bucketCount; i++) {
            const group = document.createElementNS(NAMESPACE_SVG, "g");
            const offX = i * 2 * groupWidth;
            let offY = 0;

            const rects = ["good", "poor", "grim", "none"].map(kls => {
                const rect = document.createElementNS(NAMESPACE_SVG, "rect");

                rect.setAttribute("x", offX);
                rect.setAttribute("y", height - blockHeight - offY);
                rect.setAttribute("width", groupWidth);
                rect.setAttribute("height", blockHeight);

                rect.classList.add(kls);
                offY += blockHeight;

                group.appendChild(rect);

                return rect;
            });

            this._rects.push(rects);
            svg.appendChild(group);
        }

        domElement.appendChild(svg);
        this.updateValues(hourly);
    }

    onResize() {
        const { width, height } = this._domElement.getBoundingClientRect();

        this._width = width;
        this._height = height;

        const { bucketCount, bucketSize } = this._appSettings.settings.history;
        const totalGroups = bucketCount * 2;
        const groupWidth = width / (totalGroups - 1);
        const blockHeight = height / bucketSize;

        for (let i = 0; i < bucketCount; i++) {
            const rects = this._rects[i];
            const offX = i * 2 * groupWidth;
            let offY = 0;

            rects.forEach(rect => {
                rect.setAttribute("x", offX);
                rect.setAttribute("y", height - blockHeight - offY);
                rect.setAttribute("width", groupWidth);
                rect.setAttribute("height", blockHeight);

                offY += blockHeight;
            });
        }

        this.updateValues(this._values);
    }

    updateValues(hourly) {
        const height = this._height;
        const { bucketSize } = this._appSettings.settings.history;
        const blockHeight = height / bucketSize;

        for (let i = 0; i < bucketSize; i++) {
            const values = hourly[i];
            const rects = this._rects[i];
            let offY = 0;

            for (let j = 0, len = values.length; j < len; j++) {
                const rect = rects[j], value = values[j];
                const rh = blockHeight * value;

                rect.setAttribute("y", height - rh - offY);
                rect.setAttribute("height", rh);

                offY += rh;
            }
        }

        this._values = hourly;
    }
}

module.exports = HistoryHourly;
