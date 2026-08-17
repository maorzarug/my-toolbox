function processWhatsapp() {
    const phoneInput = document.getElementById('waPhone');
    const msgInput = document.getElementById('waMsg');
    const linkTxt = document.getElementById('waDst');
    const directBtn = document.getElementById('waDirectLink');
    const placeholder = document.getElementById('waPlaceholder');

    if (!phoneInput) return;
    let phone = phoneInput.value.trim();
    const msg = msgInput ? msgInput.value : '';

    if (!phone) {
        if (linkTxt) linkTxt.value = "";
        if (directBtn) directBtn.style.display = "none";
        if (placeholder) placeholder.style.display = "block";
        return;
    }
    
    if (phone.startsWith('0')) {
        phone = '972' + phone.substring(1);
    }
    phone = phone.replace(/[^0-9]/g, '');
    let url = "https://wa.me/" + phone;
    if (msg.trim()) {
        url += "?text=" + encodeURIComponent(msg);
    }

    if (linkTxt) linkTxt.value = url;
    if (directBtn) {
        directBtn.href = url;
        directBtn.style.display = "block";
    }
    if (placeholder) placeholder.style.display = "none";
}
