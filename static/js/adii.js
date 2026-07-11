// Notification dropdown
document.addEventListener('click', function(e) {
  const btn = e.target.closest('[data-toggle="notif"]');
  const menu = document.getElementById('notif-menu');
  if (btn && menu) { menu.classList.toggle('open'); e.stopPropagation(); return; }
  if (menu) menu.classList.remove('open');
});

// Auth tabs
function showTab(tab) {
  document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.auth-panel').forEach(p => p.style.display = 'none');
  document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
  document.getElementById(`panel-${tab}`).style.display = 'block';
}

// Auto-dismiss alerts
setTimeout(() => {
  document.querySelectorAll('.alert-auto').forEach(a => a.style.opacity = '0');
}, 4000);
