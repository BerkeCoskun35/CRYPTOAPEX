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
    clearInputs();

    // Kullanıcının favorilerini yükle
    fetch('/api/favorites')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const favorites = data.favorites;
                favorites.forEach(favorite => {
                    const buttons = document.querySelectorAll(`button[data-name="${favorite.name}"][data-type="${favorite.type}"]`);
                    buttons.forEach(button => {
                        button.classList.add('favorited');
                    });
                });
            }
        })
        .catch(error => console.error('Favoriler alınırken hata:', error));
};


function toggleFavorite(button) {
    const itemName = button.getAttribute('data-name');
    const itemType = button.getAttribute('data-type');

    fetch('/api/check-login')
        .then(response => response.json())
        .then(data => {
            if (data.isLoggedIn) {
                fetch('/api/favorite', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name: itemName, type: itemType })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        if (data.action === 'added') {
                            button.classList.add('favorited');
                        } else if (data.action === 'removed') {
                            button.classList.remove('favorited');
                        }
                    }
                })
                .catch(error => console.error('Favori işlemi sırasında bir hata oluştu:', error));
            } else {
                window.location.href = '/login';
            }
        })
        .catch(error => console.error('Login durumu kontrol edilirken bir hata oluştu:', error));
}

