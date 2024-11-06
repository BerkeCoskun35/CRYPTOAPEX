function toggleNotificationPanel() {
    const panel = document.getElementById('notificationPanel');

    // Panelin görünürlüğünü kontrol et ve değiştir
    if (panel.style.display === 'block') {
        panel.style.display = 'none'; // Kapat
    } else {
        panel.style.display = 'block'; // Aç
    }

    // Konsolda durumu göster
    console.log("Panel durumu: ", panel.style.display);
}

// Dışarıya tıklanıldığında açılır paneli kapatma
window.onclick = function(event) {
    const panel = document.getElementById('notificationPanel');
    const button = document.querySelector('.notification-button');

    // Eğer butona tıklanmazsa ve panel açık ise kapat
    if (!button.contains(event.target) && panel.style.display === 'block') {
        panel.style.display = 'none'; // Paneli kapat
    }
}

function clearInputs() {
    // Select all input fields and clear their values
    const inputs = document.querySelectorAll('input[type="text"], input[type="password"]');
    inputs.forEach(input => {
        input.value = ''; // Clear each input field
    });
}

// Sayfa yüklendiğinde paneli gizle
window.onload = function() {
    const panel = document.getElementById('notificationPanel');
    panel.style.display = 'none'; // Sayfa yüklendiğinde panel gizli
    clearInputs();
}