let nikudTimeout = null;
let selectedCharSpan = null;

function processNikud() {
    const textInput = document.getElementById('nikudSrc');
    const container = document.getElementById('nikudDst');
    if (!textInput || !container) return;

    const text = textInput.value;
    if (!text.trim()) {
        container.innerHTML = "";
        return;
    }
    
    clearTimeout(nikudTimeout);
    nikudTimeout = setTimeout(() => {
        fetch('/api/nikud', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        })
        .then(res => res.json())
        .then(data => {
            renderInteractiveNikud(data.result);
        })
        .catch(err => {
            console.error("Error fetching nikud:", err);
        });
    }, 400);
}

function renderInteractiveNikud(processedText) {
    const container = document.getElementById('nikudDst');
    if (!container) return;
    container.innerHTML = "";
    
    const words = processedText.split(" ");
    words.forEach(word => {
        const wordSpan = document.createElement('span');
        wordSpan.className = 'nikud-word';
        
        let i = 0;
        while (i < word.length) {
            let char = word[i];
            let nikud = "";
            i++;
            while (i < word.length && word[i].charCodeAt(0) >= 0x05B0 && word[i].charCodeAt(0) <= 0x05C4) {
                nikud += word[i];
                i++;
            }
            
            const charSpan = document.createElement('span');
            charSpan.className = 'nikud-char';
            charSpan.innerText = char + nikud;
            charSpan.dataset.baseChar = char;
            charSpan.dataset.currentNikud = nikud;
            
            charSpan.onclick = function(e) {
                e.stopPropagation();
                if (selectedCharSpan) selectedCharSpan.classList.remove('selected');
                selectedCharSpan = charSpan;
                charSpan.classList.add('selected');
                showNikudMenu(e.pageX, e.pageY);
            };
            wordSpan.appendChild(charSpan);
        }
        container.appendChild(wordSpan);
    });
}

function showNikudMenu(x, y) {
    const menu = document.getElementById('nikudPopupMenu');
    if (!menu) return;
    menu.style.display = 'grid';
    menu.style.left = x + 'px';
    menu.style.top = y + 'px';
}

function applyNikud(nikudChar) {
    if (selectedCharSpan) {
        const base = selectedCharSpan.dataset.baseChar;
        selectedCharSpan.innerText = base + nikudChar;
        selectedCharSpan.dataset.currentNikud = nikudChar;
        selectedCharSpan.classList.remove('selected');
    }
    const menu = document.getElementById('nikudPopupMenu');
    if (menu) menu.style.display = 'none';
}

function copyInteractiveText() {
    let resultText = "";
    const words = document.querySelectorAll('.nikud-word');
    words.forEach((w, idx) => {
        w.querySelectorAll('.nikud-char').forEach(c => {
            resultText += c.innerText;
        });
        if (idx < words.length - 1) resultText += " ";
    });
    
    if (!resultText.trim()) return;
    
    navigator.clipboard.writeText(resultText).then(() => {
        const btn = document.getElementById('nikudCopyBtn');
        if (!btn) return;
        const old = btn.innerText;
        btn.innerText = "✅ הועתק!";
        btn.style.background = "var(--success)";
        setTimeout(() => {
            btn.innerText = old;
            btn.style.background = "";
        }, 2000);
    });
}

document.addEventListener('click', function() {
    const menu = document.getElementById('nikudPopupMenu');
    if (menu) menu.style.display = 'none';
    if (selectedCharSpan) {
        selectedCharSpan.classList.remove('selected');
        selectedCharSpan = null;
    }
});
