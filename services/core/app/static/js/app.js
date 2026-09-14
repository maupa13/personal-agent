"use strict";

(function loadAppBundle() {
  const version = new URL(document.currentScript?.src || location.href).search;
  for (const file of [
    "app-state.js",
    "app-render.js",
    "app-runtime.js",
    "app-actions.js",
  ]) {
    document.write(
      `<script src="/static/js/app/${file}${version}"><\\/script>`,
    );
  }
})();
