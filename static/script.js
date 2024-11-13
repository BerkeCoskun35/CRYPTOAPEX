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
    button.classList.toggle('favorited');
}