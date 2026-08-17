let currentProcessedBlob = null;

function handleFileSelect(input) {
    const count = input.files.length;
    const target = document.getElementById('fileCountEff');
    if (!target) return;
    
    if (count > 0) {
        target.innerText = " 🖼️ תמונה נבחרה מוכנה לעיבוד!";
        const preview = document.getElementById('previewContainer');
        if (preview) preview.style.display = 'none';
    } else {
        target.innerText = "";
    }
}

function applyEffectAndPreview() {
    const fileInput = document.getElementById('imgEffFile');
    const effectSelect = document.getElementById('effectSelect');
    
    if (!fileInput || fileInput.files.length === 0) {
        alert("אנא בחר תמונה תחילה.");
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('effect', effectSelect.value);
    
    const btn = document.getElementById('applyEffBtn');
    const oldText = btn ? btn.innerText : '⚡ החל אפקט';
    if (btn) {
        btn.innerText = "⏳ מעבד תמונה...";
        btn.disabled = true;
    }

    fetch('/action/img-effects-preview', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error('שגיאה בעיבוד התמונה.');
        return response.blob();
    })
    .then(blob => {
        currentProcessedBlob = blob;
        const url = URL.createObjectURL(blob);
        const previewImg = document.getElementById('imagePreview');
        const previewContainer = document.getElementById('previewContainer');
        
        if (previewImg) previewImg.src = url;
        if (previewContainer) previewContainer.style.display = 'block';
        
        if (btn) {
            btn.innerText = oldText;
            btn.disabled = false;
        }
    })
    .catch(error => {
        console.error(error);
        alert("אירעה שגיאה בעיבוד התמונה.");
        if (btn) {
            btn.innerText = oldText;
            btn.disabled = false;
        }
    });
}

function downloadProcessedImage() {
    if (!currentProcessedBlob) return;
    
    const url = URL.createObjectURL(currentProcessedBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'toolhub_processed_image.jpg';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
