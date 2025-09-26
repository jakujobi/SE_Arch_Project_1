document.getElementById('advisor-search').addEventListener('input', function () {
    const query = this.value;
    fetch(`/api/advisors?query=${query}`)
        .then(response => response.json())
        .then(data => {
            const advisorList = document.getElementById('advisor-list');
            advisorList.innerHTML = '';
            data.advisors.forEach(advisor => {
                const advisorItem = document.createElement('div');
                advisorItem.textContent = advisor.name;
                advisorItem.dataset.id = advisor.id;
                advisorItem.addEventListener('click', () => {
                    fetch(`/api/availability/${advisor.id}`)
                        .then(response => response.json())
                        .then(data => {
                            const availabilitySelect = document.getElementById('availability');
                            availabilitySelect.innerHTML = '';
                            data.availability.forEach(slot => {
                                const option = document.createElement('option');
                                option.value = slot.start_time;
                                option.textContent = `${slot.start_time} - ${slot.end_time}`;
                                availabilitySelect.appendChild(option);
                            });
                        });
                });
                advisorList.appendChild(advisorItem);
            });
        });
});
