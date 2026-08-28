window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: Object.assign({}, (window.dash_clientside || {}).clientside, {

        /**
         * Read the persisted selection and tag it with the action type
         * based on which button triggered the callback.
         *
         * @param {number} n1 save-btn clicks
         * @param {number} n2 error-btn clicks
         * @param {number} n3 trivial-btn clicks
         * @returns {string|Object} JSON payload with text, start, end, type.
         */
        capture_selection: function (n1, n2, n3) {
            if (!n1 && !n2 && !n3) { return window.dash_clientside.no_update; }

            var prop_id = (dash_clientside.callback_context.triggered[0] || {}).prop_id || "";
            var types = { "save-btn": "missing", "error-btn": "error", "trivial-btn": "trivial" };
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

function _getSelectionPayload(container) {
    var selection = window.getSelection();
    var text = (selection || "").toString().trim();
    if (!text || !selection.rangeCount) { return null; }

    try {
        var range = selection.getRangeAt(0);
        if (!container.contains(range.startContainer)) { return null; }

        var preRange = document.createRange();
        preRange.selectNodeContents(container);
        preRange.setEnd(range.startContainer, range.startOffset);
        var start = preRange.toString().length;

        return JSON.stringify({ text: text, start: start, end: start + text.length });
    } catch (e) {
        return null;
    }
}

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
        _wireContainer("source-text", ["save-btn"], "_selCapture_missing");
        _wireContainer("source-text-errors", ["error-btn", "trivial-btn"], "_selCapture_review");
    }

    if (document.getElementById("source-text")) {
        _setup();
        return;
    }

    var observer = new MutationObserver(function (_, obs) {
        if (document.getElementById("source-text")) {
            obs.disconnect();
            _setup();
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
})();