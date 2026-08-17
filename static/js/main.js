// ==========================================
// ToolHub Modern Interactive JS Core
// ==========================================

// Global Toast Notification Helper
function showToast(message, type = 'success') {
    let toast = document.getElementById('globalToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'globalToast';
        toast.className = 'toast-container';
        document.body.appendChild(toast);
    }
    
    const icon = type === 'success' ? '✨' : '⚠️';
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 2400);
}

// Global Copy Result Helper with Toast
function copyResult(targetId, btnId) {
    const target = document.getElementById(targetId);
    if (!target) return;
    const val = target.value || target.innerText;
    if (!val.trim()) {
        showToast('אין תוכן להעתקה', 'warning');
        return;
    }
    
    navigator.clipboard.writeText(val).then(() => {
        showToast('התוכן הועתק ללוח בהצלחה!');
        const btn = document.getElementById(btnId);
        if (btn) {
            const oldText = btn.innerText;
            btn.innerText = '✅ הועתק!';
            setTimeout(() => { btn.innerText = oldText; }, 2000);
        }
    }).catch(() => {
        showToast('שגיאה בהעתקה ללוח', 'warning');
    });
}

// Helper to update selected file indicator
function updateFileCount(input, targetId) {
    const count = input.files.length;
    const target = document.getElementById(targetId);
    if (!target) return;
    
    if (count > 1) {
        target.innerHTML = `<span class="file-selected-badge">📂 ${count} קבצים נבחרו ומוכנים לעיבוד</span>`;
    } else if (count === 1) {
        const fileName = input.files[0].name;
        const fileSize = (input.files[0].size / (1024 * 1024)).toFixed(2);
        target.innerHTML = `<span class="file-selected-badge">📄 ${fileName} (${fileSize} MB)</span>`;
    } else {
        target.innerHTML = "";
    }
}

// Live Search & Category Filter for Dashboard
function filterTools() {
    const searchInput = document.getElementById('toolSearchInput');
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const activeCategory = window.currentToolCategory || 'all';
    
    const cards = document.querySelectorAll('.tool-card');
    let visibleCount = 0;
    
    cards.forEach(card => {
        const title = card.getAttribute('data-title') ? card.getAttribute('data-title').toLowerCase() : '';
        const desc = card.getAttribute('data-desc') ? card.getAttribute('data-desc').toLowerCase() : '';
        const cat = card.getAttribute('data-category') || '';
        
        const matchesQuery = !query || title.includes(query) || desc.includes(query);
        const matchesCategory = activeCategory === 'all' || cat === activeCategory;
        
        if (matchesQuery && matchesCategory) {
            card.style.display = 'flex';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
    
    const noResults = document.getElementById('noResultsMsg');
    if (noResults) {
        noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    }
}

function setCategoryFilter(category, btn) {
    window.currentToolCategory = category;
    document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    filterTools();
}

// Initialize on DOM Load
document.addEventListener('DOMContentLoaded', function() {
    // 1. Mobile Sidebar Setup
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
                if (window.innerWidth <= 860) closeSidebar();
            });
        });
    }

    // 2. Drag and drop highlights for file dropzones
    document.querySelectorAll('.file-dropzone').forEach(dropzone => {
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            }, false);
        });

        dropzone.addEventListener('drop', (e) => {
            const input = dropzone.querySelector('input[type="file"]');
            if (input && e.dataTransfer.files.length > 0) {
                input.files = e.dataTransfer.files;
                const changeEvent = new Event('change', { bubbles: true });
                input.dispatchEvent(changeEvent);
            }
        });
    });

    // 3. Search Shortcut (Ctrl+K or /)
    window.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            const search = document.getElementById('toolSearchInput');
            if (search) {
                e.preventDefault();
                search.focus();
                search.select();
            }
        }
    });
});
