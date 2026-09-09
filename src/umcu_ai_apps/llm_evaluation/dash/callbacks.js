window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: Object.assign({}, (window.dash_clientside || {}).clientside, {

        /**
         * Read the persisted selection and tag it with the action type
         * based on which button triggered the callback.
         *
         * @param {number} saveButtonClicks save-btn clicks
         * @param {number} errorButtonClicks error-btn clicks
         * @param {number} trivialButtonClicks trivial-btn clicks
         * @param {number} wordingButtonClicks wording-btn clicks
         * @returns {string|Object} JSON payload with text, start, end, type.
         */
        capture_selection: function (saveButtonClicks, errorButtonClicks, trivialButtonClicks, wordingButtonClicks) {
            if (!saveButtonClicks && !errorButtonClicks && !trivialButtonClicks && !wordingButtonClicks) { return window.dash_clientside.no_update; }

            var prop_id = (dash_clientside.callback_context.triggered[0] || {}).prop_id || "";
            var types = {
                "save-btn": "missing",
                "error-btn": "error",
                "trivial-btn": "trivial",
                "wording-btn": "wording",
            };
            var type = types[prop_id.split(".")[0]] || "missing";

            var val = window._selCapture_missing || window._selCapture_review;
            window._selCapture_missing = "";
            window._selCapture_review = "";

            if (!val) { return ""; }

            var payload = JSON.parse(val);
            payload.type = type;
            return JSON.stringify(payload);
        }
    })
});


/* ── DOM listeners (registered once at page load) ────────────── */

/**
 * Collects the currently selected text inside a DOM container and returns a
 * JSON-encoded payload with the selection range relative to the container.
 *
 * @param {HTMLElement} container - The container element that must own the selection.
 * @returns {string|null} A JSON string like { text, start, end } when a valid
 * selection exists inside the container; otherwise null.
 */
function _getSelectionPayload(container) {
    var selection = window.getSelection();
    var text = (selection || "").toString().trim();
    if (!text || !selection.rangeCount) { return null; }

    try {
        var range = selection.getRangeAt(0);
        if (!container.contains(range.startContainer) || !container.contains(range.endContainer)) { return null; }
        var preRange = document.createRange();
        preRange.selectNodeContents(container);
        preRange.setEnd(range.startContainer, range.startOffset);
        var start = preRange.toString().length;

        return JSON.stringify({ text: text, start: start, end: start + text.length });
    } catch (e) {
        return null;
    }
}

/**
 * Wires a DOM container and its associated action buttons so the current text
 * selection is captured and stored in a global window variable before a callback
 * is triggered.
 *
 * The selection is captured on `mouseup` for the container itself and on
 * `mousedown` for the configured buttons. This makes sure the browser has not
 * yet cleared the selection when the user clicks a review action button.
 *
 * @param {string} containerId - The DOM id of the container whose text may be selected.
 * @param {string[]} buttonIds - The ids of buttons that should preserve the current selection.
 * @param {string} storageKey - The window property used to store the serialized selection payload.
 * @returns {void}
 */
function _wireContainer(containerId, buttonIds, storageKey) {
    var container = document.getElementById(containerId);
    if (!container) { return; }

    container.addEventListener("mouseup", function () {
        var payload = _getSelectionPayload(container);
        if (payload) { window[storageKey] = payload; }
    }, { passive: true });

    buttonIds.forEach(function (btnId) {
        var button = document.getElementById(btnId);
        if (button) {
            button.addEventListener("mousedown", function () {
                var payload = _getSelectionPayload(container);
                if (payload) { window[storageKey] = payload; }
            }, { passive: true });
        }
    });
}

(function _initListeners() {
    function _setup() {
        _wireContainer("context-text", ["save-btn"], "_selCapture_missing");
        _wireContainer("llm-text", ["error-btn", "trivial-btn", "wording-btn"], "_selCapture_review");
    }

    if (document.getElementById("context-text")) {
        _setup();
        return;
    }

    var observer = new MutationObserver(function (_, obs) {
        if (document.getElementById("context-text")) {
            obs.disconnect();
            _setup();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();