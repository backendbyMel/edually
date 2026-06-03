// sidebar.js — Claude-style collapsible sidebar
(function () {
  var sidebar = document.getElementById('cs-sidebar');
  var toggle  = document.getElementById('cs-toggle');
  if (!sidebar || !toggle) return;

  var STORAGE_KEY = 'cs-sidebar-collapsed';

  function setCollapsed(yes) {
    sidebar.classList.toggle('collapsed', yes);
    try { localStorage.setItem(STORAGE_KEY, yes ? '1' : '0'); } catch(e) {}
  }

  // Restore saved state on load
  try {
    if (localStorage.getItem(STORAGE_KEY) === '1') setCollapsed(true);
  } catch(e) {}

  toggle.addEventListener('click', function () {
    setCollapsed(!sidebar.classList.contains('collapsed'));
  });
})();
