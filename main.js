// Mobile nav toggle
const toggle = document.getElementById('navToggle');
const navLinks = document.getElementById('navLinks');
if (toggle) {
  toggle.addEventListener('click', () => navLinks.classList.toggle('open'));
}

// Auto-dismiss flash messages
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(f => f.remove());
}, 4000);

// Cart count live update
async function updateCartBadge() {
  try {
    const r = await fetch('/cart/count');
    const d = await r.json();
    const badge = document.getElementById('cartBadge');
    if (badge) badge.textContent = d.count;
  } catch(e) {}
}
