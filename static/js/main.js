// Helper to update selected file count indicator
function updateFileCount(input, targetId) {
    const count = input.files.length;
    const target = document.getElementById(targetId);
    if (!target) return;
    
    if (count > 1) {
        target.innerText = " 📂 " + count + " קבצים נבחרו ומוכנים!";
    } else if (count === 1) {
        target.innerText = " 📄 קובץ אחד נבחר ומוכן!";
    } else {
        target.innerText = "";
    }
}

// Global copy result helper
function copyResult(targetId, btnId) {
    const target = document.getElementById(targetId);
    if (!target || !target.value.trim()) return;
    
    navigator.clipboard.writeText(target.value).then(() => {
        const btn = document.getElementById(btnId);
        if (!btn) return;
        const oldText = btn.innerText;
        btn.innerText = "✅ הועתק!";
        btn.style.background = "var(--success)";
        setTimeout(() => {
            btn.innerText = oldText;
            btn.style.background = "";
        }, 2000);
    });
}

// Hamburger menu setup
document.addEventListener('DOMContentLoaded', function() {
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebar = document.getElementById('mainSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');

    function openSidebar() {
        if (sidebar) sidebar.classList.add('open');
        if (backdrop) backdrop.classList.add('open');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove('open');
        if (backdrop) backdrop.classList.remove('open');
        document.body.style.overflow = '';
    }

    if (hamburgerBtn) hamburgerBtn.addEventListener('click', openSidebar);
    if (sidebarClose) sidebarClose.addEventListener('click', closeSidebar);
    if (backdrop) backdrop.addEventListener('click', closeSidebar);

    if (sidebar) {
        sidebar.querySelectorAll('a').forEach(function(link) {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 768) closeSidebar();
            });
        });
    }
});
