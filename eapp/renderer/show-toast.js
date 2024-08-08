
const toast = document.getElementById("toast");
const toastError = document.getElementById("toast-error");
let timeoutId = null, waitToastId = null;

function showToast(toastText) {
    if (timeoutId !== null) {
        clearTimeout(timeoutId);
        timeoutId = null;
        toast.classList.add("hidden");
    }

    if (waitToastId !== null) {
        clearTimeout(waitToastId);
        waitToastId = null;
    }

    waitToastId = setTimeout(function () {
        waitToastId = null;

        toast.innerHTML = toastText;
        toast.classList.remove("hidden");

        timeoutId = setTimeout(function () {
            timeoutId = null;
            toast.classList.add("hidden");
        }, 1000);
    }, 250);
}

function showToastError(toastText) {
    if (timeoutId !== null) {
        clearTimeout(timeoutId);
        timeoutId = null;
        toastError.classList.add("hidden");
    }

    if (waitToastId !== null) {
        clearTimeout(waitToastId);
        waitToastId = null;
    }

    waitToastId = setTimeout(function () {
        waitToastId = null;

        toastError.innerHTML = toastText;
        toastError.classList.remove("hidden");

        timeoutId = setTimeout(function () {
            timeoutId = null;
            toastError.classList.add("hidden");
        }, 1000);
    }, 250);
}

module.exports = {
    showToast: showToast,
    showToastError: showToastError,
};