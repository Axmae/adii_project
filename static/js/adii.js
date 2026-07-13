(function() {
  'use strict';

  // Notification dropdown
  const notifBtn = document.querySelector('[data-toggle="notif"]');
  const notifMenu = document.getElementById('notif-menu');

  if (notifBtn && notifMenu) {
    notifBtn.addEventListener('click', function(e) {
      const isOpen = notifMenu.classList.contains('open');
      closeAllDropdowns();
      if (!isOpen) {
        notifMenu.classList.add('open');
        notifBtn.setAttribute('aria-expanded', 'true');
      }
      e.stopPropagation();
    });

    document.addEventListener('click', function() {
      notifMenu.classList.remove('open');
      notifBtn.setAttribute('aria-expanded', 'false');
    });

    notifMenu.addEventListener('click', function(e) {
      e.stopPropagation();
    });

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && notifMenu.classList.contains('open')) {
        notifMenu.classList.remove('open');
        notifBtn.setAttribute('aria-expanded', 'false');
        notifBtn.focus();
      }
    });
  }

  function closeAllDropdowns() {
    document.querySelectorAll('.dropdown-menu.open').forEach(function(m) {
      m.classList.remove('open');
    });
    const btn = document.querySelector('[data-toggle="notif"]');
    if (btn) btn.setAttribute('aria-expanded', 'false');
  }

  // Modal helpers
  window.openModal = function(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    const firstInput = modal.querySelector('input, textarea, button');
    if (firstInput) firstInput.focus();
    document.body.style.overflow = 'hidden';
  };

  window.closeModal = function(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  };

  document.addEventListener('click', function(e) {
    const modal = e.target.closest('.modal-overlay.open');
    if (modal && !e.target.closest('.modal')) {
      modal.classList.remove('open');
      modal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      const openModal = document.querySelector('.modal-overlay.open');
      if (openModal) {
        openModal.classList.remove('open');
        openModal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
      }
    }
  });

  // Auth tabs
  window.showTab = function(tab) {
    document.querySelectorAll('.auth-tab').forEach(function(t) { t.classList.remove('active'); });
    document.querySelectorAll('.auth-panel').forEach(function(p) { p.style.display = 'none'; });
    const activeTab = document.querySelector('[data-tab="' + tab + '"]');
    if (activeTab) activeTab.classList.add('active');
    const panel = document.getElementById('panel-' + tab);
    if (panel) panel.style.display = 'block';
  };

  // Auto-dismiss alerts
  setTimeout(function() {
    document.querySelectorAll('.alert-auto').forEach(function(a) {
      a.style.transition = 'opacity .5s';
      a.style.opacity = '0';
      setTimeout(function() { a.style.display = 'none'; }, 500);
    });
  }, 4000);
})();
