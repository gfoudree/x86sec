// Label code blocks with their language (for pre[data-lang] label)
document.querySelectorAll('pre code[class]').forEach(el => {
  const m = el.className.match(/language-(\w+)/);
  if (m) el.parentElement.setAttribute('data-lang', m[1]);
});

// Click-to-copy for code blocks
document.querySelectorAll('pre').forEach(pre => {
  pre.style.cursor = 'pointer';
  pre.addEventListener('click', () => {
    const code = pre.querySelector('code');
    const text = code ? code.innerText : pre.innerText;
    navigator.clipboard.writeText(text).then(() => {
      const prev = pre.getAttribute('data-lang') || '';
      pre.setAttribute('data-lang', 'copied ✓');
      setTimeout(() => pre.setAttribute('data-lang', prev), 1500);
    });
  });
});

// Logo glitch — slow breathing glow + random chromatic glitch bursts
(function glitchLoop() {
  var logo = document.querySelector('.site-logo');
  if (!logo) return;
  var delay = 4000 + Math.random() * 5000;
  setTimeout(function() {
    // force reflow so Firefox re-triggers animation when class is re-added
    logo.classList.remove('glitching');
    void logo.offsetWidth;
    logo.classList.add('glitching');

    var doubleTap = Math.random() > 0.6;
    setTimeout(function() {
      logo.classList.remove('glitching');
      if (doubleTap) {
        setTimeout(function() {
          void logo.offsetWidth;
          logo.classList.add('glitching');
          setTimeout(function() { logo.classList.remove('glitching'); }, 200);
        }, 130);
      }
    }, 290);

    glitchLoop();
  }, delay);
})();

// De-obfuscate and render email placeholders inserted in content files.
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('[data-email-b64]').forEach(function(el) {
    try {
      const b64 = el.getAttribute('data-email-b64');
      if (!b64) return;
      const rev = atob(b64);
      const email = rev.split('').reverse().join('');
      const a = document.createElement('a');
      a.href = 'mailto:' + email;
      a.textContent = email;
      el.replaceWith(a);
    } catch (e) {
      console.error('email render failed', e);
    }
  });
});
