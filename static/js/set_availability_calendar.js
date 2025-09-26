document.addEventListener("DOMContentLoaded", function () {
    const addTimeSlotButtons = document.querySelectorAll(".add-time-slot");
    const saveTimeSlotButton = document.getElementById("save-time-slot");
    const saveAvailabilityButton = document.getElementById("save-availability");
    const modalDayInput = document.getElementById("modal-day");
    const modalStartTimeInput = document.getElementById("modal-start-time");
    const modalEndTimeInput = document.getElementById("modal-end-time");
    const timeSlots = { add: {}, remove: {} }; // Initialize add and remove properties

    // Helper function to convert 24-hour time to 12-hour format
    function formatTo12Hour(time) {
        const [hour, minute] = time.split(":");
        const period = hour >= 12 ? "PM" : "AM";
        const formattedHour = hour % 12 || 12;
        return `${formattedHour}:${minute} ${period}`;
    }

    // Helper function to convert 12-hour time to 24-hour format
    function formatTo24Hour(time) {
        const [timePart, period] = time.split(" ");
        let [hour, minute] = timePart.split(":").map(Number);
        if (period === "PM" && hour !== 12) hour += 12;
        if (period === "AM" && hour === 12) hour = 0;
        return `${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")}`;
    }

    // Open modal to add a time slot
    addTimeSlotButtons.forEach(button => {
        button.addEventListener("click", function () {
            const day = this.dataset.day;
            modalDayInput.value = day;
            modalStartTimeInput.value = "";
            modalEndTimeInput.value = "";
            const modal = new bootstrap.Modal(document.getElementById("addTimeSlotModal"));
            modal.show();
        });
    });

    // Save time slot to the table
    saveTimeSlotButton.addEventListener("click", function () {
        const day = modalDayInput.value;
        const startTime = modalStartTimeInput.value; // Already in 24-hour format from <input type="time">
        const endTime = modalEndTimeInput.value; // Already in 24-hour format from <input type="time">

        if (!startTime || !endTime) {
            alert("Please specify both start and end times.");
            return;
        }

        if (!timeSlots.add[day]) {
            timeSlots.add[day] = [];
        }
        timeSlots.add[day].push({ start_time: startTime, end_time: endTime });

        const timeSlotsCell = document.getElementById(`time-slots-${day}`);
        const slotElement = document.createElement("div");
        slotElement.textContent = `${formatTo12Hour(startTime)} - ${formatTo12Hour(endTime)}`;
        slotElement.innerHTML += `
            <button class="btn btn-danger btn-sm remove-time-slot" 
                    data-day="${day}" 
                    data-start-time="${startTime}" 
                    data-end-time="${endTime}">
                Remove
            </button>`;
        slotElement.classList.add("highlight"); // Add highlight class
        timeSlotsCell.appendChild(slotElement);

        // Reset the highlight class to allow re-triggering the effect
        setTimeout(() => {
            slotElement.classList.remove("highlight");
            void slotElement.offsetWidth; // Trigger reflow to reset the animation
            slotElement.classList.add("highlight");
        }, 0);

        // Reattach event listener for dynamically added remove buttons
        slotElement.querySelector(".remove-time-slot").addEventListener("click", function () {
            const day = this.dataset.day;
            const startTime = this.dataset.startTime;
            const endTime = this.dataset.endTime;
            const parentElement = this.parentElement;

            // Check if the entry is a new entry
            const isNewEntry = timeSlots.add[day]?.some(
                slot => slot.start_time === startTime && slot.end_time === endTime
            );

            if (isNewEntry) {
                // Remove the new entry immediately
                timeSlots.add[day] = timeSlots.add[day].filter(
                    slot => slot.start_time !== startTime || slot.end_time !== endTime
                );
                parentElement.remove();
            } else {
                if (this.textContent.trim() === "Remove") {
                    // Mark for removal
                    if (!timeSlots.remove[day]) {
                        timeSlots.remove[day] = [];
                    }
                    timeSlots.remove[day].push({ start_time: startTime, end_time: endTime });

                    parentElement.classList.add("highlight-remove");
                    this.textContent = "Keep";
                    this.classList.remove("btn-danger");
                    this.classList.add("btn-secondary"); // Change color to gray
                } else {
                    // Cancel removal
                    timeSlots.remove[day] = timeSlots.remove[day].filter(
                        slot => slot.start_time !== startTime || slot.end_time !== endTime
                    );

                    parentElement.classList.remove("highlight-remove");
                    this.textContent = "Remove";
                    this.classList.remove("btn-secondary");
                    this.classList.add("btn-danger"); // Change color back to red
                }
            }
        });

        const modal = bootstrap.Modal.getInstance(document.getElementById("addTimeSlotModal"));
        modal.hide();
    });

    const removeTimeSlotButtons = document.querySelectorAll(".remove-time-slot");

    // Remove time slot from the table and prepare for server update
    removeTimeSlotButtons.forEach(button => {
        button.addEventListener("click", function () {
            const day = this.dataset.day;
            const startTime = this.dataset.startTime;
            const endTime = this.dataset.endTime;
            const parentElement = this.parentElement;

            // Check if the entry is a new entry
            const isNewEntry = timeSlots.add[day]?.some(
                slot => slot.start_time === startTime && slot.end_time === endTime
            );

            if (isNewEntry) {
                // Remove the new entry immediately
                timeSlots.add[day] = timeSlots.add[day].filter(
                    slot => slot.start_time !== startTime || slot.end_time !== endTime
                );
                parentElement.remove();
            } else {
                if (this.textContent.trim() === "Remove") {
                    // Mark for removal
                    if (!timeSlots.remove[day]) {
                        timeSlots.remove[day] = [];
                    }
                    timeSlots.remove[day].push({ start_time: startTime, end_time: endTime });

                    parentElement.classList.add("highlight-remove");
                    this.textContent = "Keep";
                    this.classList.remove("btn-danger");
                    this.classList.add("btn-secondary"); // Change color to gray
                } else {
                    // Cancel removal
                    timeSlots.remove[day] = timeSlots.remove[day].filter(
                        slot => slot.start_time !== startTime || slot.end_time !== endTime
                    );

                    parentElement.classList.remove("highlight-remove");
                    this.textContent = "Remove";
                    this.classList.remove("btn-secondary");
                    this.classList.add("btn-danger"); // Change color back to red
                }
            }
        });
    });

    // Save all availability to the server
    saveAvailabilityButton.addEventListener("click", function () {
        fetch("/schedule/setAvailability/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
            },
            body: JSON.stringify({ time_slots: timeSlots.add, remove_time_slots: timeSlots.remove })
        })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    return response.json().then(data => {
                        alert(data.error_message || "An error occurred while saving availability.");
                        throw new Error("Failed to save availability.");
                    });
                }
            })
            .then(data => {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url; // Redirect to the URL provided by the backend
                }
            })
            .catch(error => {
                console.error("Error:", error);
                alert("An error occurred while saving availability.");
            });
    });
});
