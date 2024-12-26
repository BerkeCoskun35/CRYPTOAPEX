function toggleNotificationPanel() {
    const panel = document.getElementById('notificationPanel');

    
    if (panel.style.display === 'block') {
        panel.style.display = 'none'; 
    } else {
        panel.style.display = 'block'; 
    }

    
    console.log("Panel durumu: ", panel.style.display);
}


window.onclick = function(event) {
    const panel = document.getElementById('notificationPanel');
    const button = document.querySelector('.notification-button');

    
    if (!button.contains(event.target) && panel.style.display === 'block') {
        panel.style.display = 'none'; 
    }
}

function clearInputs() {
    
    const inputs = document.querySelectorAll('input[type="text"], input[type="password"]');
    inputs.forEach(input => {
        input.value = ''; 
    });
}


window.onload = function() {
    const panel = document.getElementById('notificationPanel');
    panel.style.display = 'none'; 
    clearInputs();
}

function toggleFavorite(button) {
    // Kullanıcı giriş yapmış mı kontrol et
    fetch('/api/check-login')
        .then(response => response.json())
        .then(data => {
            if (data.isLoggedIn) {
                // Kullanıcı giriş yapmışsa favoriyi ekle/kaldır
                button.classList.toggle('favorited');
            } else {
                // Giriş yapılmamışsa login sayfasına yönlendir
                window.location.href = '/login';
            }
        })
        .catch(error => {
            console.error('Login durumu kontrol edilirken bir hata oluştu:', error);
        });
}
