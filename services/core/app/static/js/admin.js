"use strict";

(function loadAdminBundle() {
  const version = new URL(document.currentScript?.src || location.href).search;
  for (const file of ["admin-core.js", "admin-extras.js"]) {
    document.write(
      `<script src="/static/js/admin/${file}${version}"><\\/script>`,
    );
  }
})();
