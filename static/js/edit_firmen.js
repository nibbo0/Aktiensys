document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('firmen-list');
    if (!container) return;

    container.addEventListener('click', async (event) => {
        const button = event.target;
        if (button.tagName === 'BUTTON' && button.classList.contains('save-btn')) {
            const row = button.closest('.firmen-list-row');
            if (!row) return;
            const nameInput = row.querySelector('input[type="text"]');
            const colorInput = row.querySelector('input[type="color"]');
            const kurszielInput = row.querySelector('.kurszieleditfield');
            const firmaId = row.dataset.firmaId;
            const neuerName = nameInput.value;
            const neueFarbe = colorInput.value;


             // Name speichern
            await fetch(`/api/aktien/${firmaId}/name?name=${encodeURIComponent(neuerName)}`, {
                method: 'PUT'
            });

            // Farbe speichern
            await fetch(`/api/aktien/${firmaId}/color?color=${encodeURIComponent(neueFarbe)}`, {
                method: 'PUT'
            });

           const neuesKursziel = parseFloat(kurszielInput.value);
            if (!isNaN(neuesKursziel)) {
                await fetch(`/api/kurse/vorschau/${firmaId}?wert=${encodeURIComponent(neuesKursziel)}`, {
                    method: 'PUT'
                });
            }

            alert('Gespeichert!');
        }
    });
});