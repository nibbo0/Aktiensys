document.addEventListener('DOMContentLoaded', async () => {
    const container = document.getElementById('firmen-list');
    const response = await fetch('/api/aktien/');
    const firmen = await response.json();

    if (!firmen.length) {
        container.innerHTML = "<div style='color:#fff'>Keine Firmen gefunden.</div>";
        return;
    }

    firmen.forEach(firma => {
        const row = document.createElement('div');
        row.dataset.firmaId = firma.id;
        row.className = 'firmen-list-row';
        row.innerHTML = `
            <input type="checkbox">
            <input type="text" value="${firma.name}" placeholder="Firmenname">
            <input type="color" value="#ff0000" placeholder="Farbe">
            <input type="text" value="" placeholder="Aktueller Kurs">
            <input type="text" value="" placeholder="Aktuelles Kursziel">
            <input type="number" value="" step="1.00">
            <button id="save-btn-${firma.id}" data-firma-id="${firma.id}">Save</button>
        `;
        container.appendChild(row);
    });
});