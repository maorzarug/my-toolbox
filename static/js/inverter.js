let currentMode = 'full';
const engToHebMap = {
    'q': '/', 'w': "'", 'e': 'ק', 'r': 'ר', 't': 'א', 'y': 'ט', 'u': 'ו', 'i': 'ן', 'o': 'ם', 'p': 'פ',
    'a': 'ש', 's': 'ד', 'd': 'ג', 'f': 'כ', 'g': 'ע', 'h': 'י', 'j': 'ח', 'k': 'ל', 'l': 'ך', ';': 'ף',
    "'": ',', 'z': 'ז', 'x': 'ס', 'c': 'ב', 'v': 'ה', 'b': 'נ', 'n': 'מ', 'm': 'צ', ',': 'ת', '.': 'ץ', '/': '.'
};
const hebToEngMap = {};
for (let k in engToHebMap) {
    hebToEngMap[engToHebMap[k]] = k;
}

function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.btn-action').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById('btn-' + mode);
    if (activeBtn) activeBtn.classList.add('active');
    processText();
}

function processText() {
    const srcInput = document.getElementById('srcText');
    if (!srcInput) return;
    const src = srcInput.value;
    let result = "";

    if (currentMode === 'full') {
        result = src.split('').reverse().join('');
    } else if (currentMode === 'lines') {
        result = src.split('\n').map(line => line.split('').reverse().join('')).join('\n');
    } else if (currentMode === 'no_num') {
        result = src.split('').reverse().join('').replace(/\d+/g, m => m.split('').reverse().join(''));
    } else if (currentMode === 'no_eng') {
        result = src.split('').reverse().join('').replace(/[a-zA-Z]+/g, m => m.split('').reverse().join(''));
    } else if (currentMode === 'eng2heb' || currentMode === 'heb2eng') {
        const map = (currentMode === 'eng2heb') ? engToHebMap : hebToEngMap;
        for (let i = 0; i < src.length; i++) {
            let char = src[i].toLowerCase();
            result += map[char] ? map[char] : src[i];
        }
    }
    
    const dst = document.getElementById('dstText');
    if (dst) dst.value = result;
}
