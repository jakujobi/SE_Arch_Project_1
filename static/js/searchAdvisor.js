function filterAdvisors() {
    const input = document.getElementById("searchInput").value.toLowerCase();
    const table = document.getElementById("advisorTable");
    const rows = table.getElementsByTagName("tr");

    for (let i = 0; i < rows.length; i++) {
        const nameCell = rows[i].getElementsByTagName("td")[0];
        if (nameCell) {
            const name = nameCell.textContent || nameCell.innerText;
            rows[i].style.display = name.toLowerCase().includes(input) ? "" : "none";
        }
    }
}
