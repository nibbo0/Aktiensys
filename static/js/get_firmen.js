document.addEventListener('DOMContentLoaded', async () => {
    const container = document.getElementById('firmen-list');
    const response = await fetch('/api/aktien/');
    const firmen = await response.json();

    if (!firmen.length) {
        container.innerHTML = "<div style='color:#fff'>Keine Firmen gefunden.</div>";
        return;
    }

    // Für jede Firma: Kurs asynchron laden und Zeile bauen
    for (const firma of firmen) {
    let aktuellerKurs = '';
    let kursziel = '';
    try {
        // Aktueller Kurs (letzter Preis mit valid_after <= jetzt)
        const kursResp = await fetch(`/api/kurse/verlauf/${firma.id}?eintraege=1`);
        const kursData = await kursResp.json();
        aktuellerKurs = (kursData[firma.id] && kursData[firma.id][0] && kursData[firma.id][0].price) || '';

        // Kursziel (nächster Preis mit valid_after > jetzt)
        const zielResp = await fetch(`/api/kurse/vorschau/${firma.id}?eintraege=1`);
        const zielData = await zielResp.json();
        kursziel = (zielData[firma.id] && zielData[firma.id][0] && zielData[firma.id][0].price) || '';
    } catch (e) {
        aktuellerKurs = 'Fehler';
        kursziel = 'Fehler';
    }

    const row = document.createElement('div');
    row.dataset.firmaId = firma.id;
    row.className = 'firmen-list-row';
    row.innerHTML = `
        <input type="checkbox">
        <input type="text" value="${(firma.stock_name && firma.stock_name.trim()) ? firma.stock_name : 'Unnamed'}" placeholder="Firmenname">
        <input type="color" value="${firma.color ? firma.color : '#ffffff'}" placeholder="Farbe">
        <input type="text" class="kursfeld" value="${aktuellerKurs}" placeholder="Aktueller Kurs" readonly>
        <input type="text" class="kurszielfeld" value="${kursziel}" placeholder="Aktuelles Kursziel" readonly>
        <input type="number" class="kurszieleditfield" value="${kursziel}" step="1.00">
        <span class="countdown"></span>
        <button class="save-btn">Save</button>
    `;
    container.appendChild(row);
}

    // Aktualisiere alle 10 Sekunden die Kurse
    setInterval(async () => {
        const rows = container.querySelectorAll('.firmen-list-row');
        for (const row of rows) {
            const firmaId = row.dataset.firmaId;
            try {
                // Aktuellen Kurs laden und setzen
                const kursfeld = row.querySelector('.kursfeld');
                const alterKurs = kursfeld ? kursfeld.value : '';
                const kursResp = await fetch(`/api/kurse/verlauf/${firmaId}?eintraege=1`);
                const kursData = await kursResp.json();
                const aktuellerKurs = (kursData[firmaId] && kursData[firmaId][0] && kursData[firmaId][0].price) || '';
                if (kursfeld) kursfeld.value = aktuellerKurs;
    
                // Kursziel laden und setzen
                const zielResp = await fetch(`/api/kurse/vorschau/${firmaId}?eintraege=1`);
                const zielData = await zielResp.json();
                const kursziel = (zielData[firmaId] && zielData[firmaId].price) || '';
                const validAfter = zielData[firmaId] && zielData[firmaId].valid_after;
                const kurszielfeld = row.querySelector('.kurszielfeld');
                const kurszieleditfeld = row.querySelector('.kurszieleditfield');
                const countdownField = row.querySelector('.countdown');
    
                if (kurszielfeld) kurszielfeld.value = kursziel;
    
                // Nur wenn sich der aktuelle Kurs geändert hat, Kursziel in Editfeld übernehmen
                if (kurszieleditfeld && alterKurs !== aktuellerKurs) {
                    kurszieleditfeld.value = kursziel;
                }
    
                // Countdown berechnen und anzeigen
                if (countdownField && validAfter) {
                    const targetTime = new Date(validAfter).getTime();
                    const now = Date.now();
                    let diff = Math.floor((targetTime - now) / 1000);
                    if (diff < 0) diff = 0;
                    const min = Math.floor(diff / 60);
                    const sec = diff % 60;
                    countdownField.textContent = `${min}:${sec.toString().padStart(2, '0')} min`;
                }
            } catch (e) {
                // Fehler ignorieren oder anzeigen
            }
        }
    }, 500);
});