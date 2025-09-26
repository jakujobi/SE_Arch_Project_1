document.addEventListener('DOMContentLoaded', function () {
    document.querySelector('body').addEventListener('click', function (event) {
        if (event.target.classList.contains('unregister-btn')) {
            event.preventDefault();
            const button = event.target;

            // Prevent duplicate requests by checking if the button is already disabled
            if (button.disabled) return;

            const eventId = button.getAttribute('data-event-id');
            if (eventId) {
                unregisterEvent(eventId, button);
            }
        }
    });
});

function unregisterEvent(eventId, button) {
    // Disable the button to prevent duplicate calls
    button.disabled = true;

    fetch(`/schedule/unregister/${eventId}/`, { // Fixed the URL to include the correct path
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        },
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Successfully unregistered from the event.');
                location.reload();
            } else {
                alert(data.message || 'Failed to unregister from the event.');
                button.disabled = false; // Re-enable the button if the operation failed
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An unexpected error occurred while trying to unregister from the event.');
            button.disabled = false; // Re-enable the button in case of an error
        });
}

function getCSRFToken() {
    return document.querySelector('input[name="csrfmiddlewaretoken"]').value;
}
