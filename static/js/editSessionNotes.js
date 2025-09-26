document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.edit-session-notes-btn').forEach(button => {
        button.addEventListener('click', function () {
            const consultationId = this.dataset.consultationId;

            // Fetch the current session notes
            fetch(`/schedule/getSessionNotes/${consultationId}/`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const currentNotes = data.session_notes || "";
                    const newNotes = prompt("Edit session notes:", currentNotes);
                    if (newNotes !== null) {
                        fetch(`/schedule/updateSessionNotes/${consultationId}/`, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ session_notes: newNotes }),
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                location.reload();
                            } else {
                                alert(data.message || "An error occurred while updating session notes.");
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                        });
                    }
                } else {
                    alert(data.message || "An error occurred while fetching session notes.");
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
});
