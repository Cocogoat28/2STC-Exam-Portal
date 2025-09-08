document.addEventListener('DOMContentLoaded', function () {
  try {
    // Remove Dashboard and Groups from sidebar
    document.querySelectorAll('.nav-sidebar a').forEach(a => {
      const t = a.textContent.trim().toLowerCase();
      if (t === 'dashboard' || t === 'groups') {
        const li = a.closest('li');
        if (li) li.remove();
      }
    });

    // Find the Exams section UL
    const examsHeader = Array.from(document.querySelectorAll('.nav-sidebar .nav-header'))
      .find(h => h.textContent.trim().toLowerCase() === 'exams');
    let ul = examsHeader ? examsHeader.nextElementSibling : null;
    if (!ul || !ul.classList.contains('nav-treeview')) {
      // fallback: first .nav-sidebar ul
      ul = document.querySelector('.nav-sidebar');
    }

    function addItem(text, href, icon='fas fa-file-import') {
      const li = document.createElement('li');
      li.className = 'nav-item';
      li.innerHTML = `<a href="${href}" class="nav-link">
          <i class="nav-icon ${icon}"></i>
          <p>${text}</p>
        </a>`;
      ul.appendChild(li);
    }

    // Clear existing "Import Excel" or similar links we may have added earlier
    // Add the three items
    
  } catch(e) {
    console.warn('Sidebar customization failed', e);
  }
});
document.addEventListener('DOMContentLoaded', function () {
  try {
    // Remove "Dashboard" from the sidebar
    document.querySelectorAll('.nav-sidebar a').forEach(a => {
      const t = a.textContent.trim().toLowerCase();
      if (t === 'dashboard') {
        const li = a.closest('li');
        if (li) li.remove();
      }
    });
  } catch (e) {
    console.warn('Sidebar customization failed', e);
  }
});
