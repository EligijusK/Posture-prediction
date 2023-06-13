const { NAMESPACE_SVG, CIRCLE_STROKE_WIDTH } = require("../constants");

class HistoryTotals {
    _width;
    _height;
    _radius;
    _circumference;

    _circles;
    _textPercentage = null;

    constructor(domElement, appSettings, totals) {
        const { width, height } = domElement.getBoundingClientRect();
        const svg = document.createElementNS(NAMESPACE_SVG, "svg");

        this._width = width;
        this._height = height;
        this._appSettings = appSettings;
        this._values = totals;
        this._domElement = domElement;

        const stroke = CIRCLE_STROKE_WIDTH;
        const hstroke = stroke * 0.5;

        let strokeOffset = 0;
        const r = this._radius = width * 0.5 - hstroke;
        const C = this._circumference = 2 * Math.PI * r;
        const offsets = [0.25, 0.25, 0.25, 0.25];

        this._circles = ["good", "poor", "grim", "none"].map((kls, i) => {
            const strokeSize = offsets[i];
            const circle = document.createElementNS(NAMESPACE_SVG, "circle");

            circle.setAttribute("cx", width * 0.5);
            circle.setAttribute("cy", height * 0.5);
            circle.setAttribute("r", r);

            circle.setAttribute("stroke-dashoffset", `${strokeOffset * C}`);
            circle.setAttribute("stroke-dasharray", `${strokeSize * C} ${(1 - strokeSize) * C}`);

            circle.classList.add(kls);

            svg.prepend(circle);

            strokeOffset -= strokeSize;

            return circle;
        });

        this._circles[0].style.setProperty("stroke-width", `calc(${stroke} / var(--base-height) * var(--true-height))`);

        this._textPercentage = document.createElementNS(NAMESPACE_SVG, "text");
        this._textPercentage.textContent = "--";
        this._textPercentage.setAttribute("x", width * 0.5);
        this._textPercentage.setAttribute("y", height * 0.5);
        this._textPercentage.classList.add("good", "percentage");

        this._textSittingStraight = document.createElementNS(NAMESPACE_SVG, "text");
        this._textSittingStraight.textContent = "sitting straight"
        this._textSittingStraight.setAttribute("x", width * 0.5);
        this._textSittingStraight.style.transform = `translateY(calc(calc(${height * 0.5}px + (${24 + 12} / var(--base-height) * var(--true-height)))))`;

        this._textSittingStraight.classList.add("straight");

        svg.appendChild(this._textPercentage);
        svg.appendChild(this._textSittingStraight);

        domElement.appendChild(svg);
        this.updateValues(totals);
    }

    onResize() {
        const { width, height } = this._domElement.getBoundingClientRect();
        const stroke = CIRCLE_STROKE_WIDTH;
        const hstroke = stroke * 0.5;
        const r = this._radius = width * 0.5 - hstroke;

        this._circles.forEach(circle => { 
            circle.setAttribute("cx", width * 0.5);
            circle.setAttribute("cy", height * 0.5);
            circle.setAttribute("r", r);
        });

        this._textPercentage.setAttribute("x", width * 0.5);
        this._textPercentage.setAttribute("y", height * 0.5);
        this._textSittingStraight.setAttribute("x", width * 0.5);
        this._textSittingStraight.style.transform = `translateY(calc(calc(${height * 0.5}px + (${24 + 12} / var(--base-height) * var(--true-height)))))`;
    }

    updateValues(totals) {
        const sum = totals.reduce((sum, v) => sum + v);
        const vals = sum === 0 ? [0.25, 0.25, 0.25, 0.25] : totals.map(v => v / sum);
        const C = this._circumference;
        let strokeOffset = 0;

        this._textPercentage.textContent = sum === 0 ? "--" : `${((totals[0] / sum) * 100).toFixed(0)}%`;
        this._values = totals;

        for (let i = 0, len = vals.length; i < len; i++) {
            const strokeSize = vals[i];
            const circle = this._circles[i];

            circle.setAttribute("stroke-dashoffset", `${strokeOffset * C}`);
            circle.setAttribute("stroke-dasharray", `${strokeSize * C} ${(1 - strokeSize) * C}`);

            strokeOffset -= strokeSize;
        }
    }
}

module.exports = HistoryTotals;