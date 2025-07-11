document.addEventListener('DOMContentLoaded', async () => {
    const container = document.getElementById('shop-list');

    try {
        // API-Aufruf, um die verfügbaren Firmen zu laden
        const response = await fetch('/api/aktien/');
        if (!response.ok) {
            throw new Error(`HTTP-Fehler! Status: ${response.status}`);
        }
        const stocks = await response.json();

        // Überprüfen, ob Firmen vorhanden sind
        if (!stocks.length) {
            container.innerHTML = "<div style='color:#fff'>Keine Firmen gefunden.</div>";
            return;
        }

        // Bestehende Shop-Header beibehalten
        const shopHeader = container.querySelector('.shop-list-header');
        container.innerHTML = '';
        container.appendChild(shopHeader);

        // Dynamisch Zeilen für jede Firma hinzufügen
        for (const stock of stocks) {
            const row = createStockRow(stock);
            container.appendChild(row);

            // Lade den aktuellen Kurs
            loadStockPrice(stock.id, row);

            // Lade die gekauften Aktien
            loadStockSummary(stock.id, row);

            // Event-Listener für Plus-, Minus- und Kauf-Buttons hinzufügen
            setupRowEventListeners(stock.id, row);
        }
    } catch (error) {
        console.error('Fehler beim Laden der Firmen:', error);
        container.innerHTML = "<div style='color:#fff'>Fehler beim Laden der Firmen.</div>";
    }
});

// Erstellt eine Zeile für eine Firma
function createStockRow(stock) {
    const row = document.createElement('div');
    row.classList.add('shop-row');
    row.innerHTML = `
        <span class="firma-name">${stock.name}</span>
        <span class="akt-wert">Lade Kurs...</span>
        <span class="aktien-umlauf">${stock.stocks_available}</span>
        <button class="minus-btn">-</button>
        <input type="number" class="anzahl-input" value="1" min="1" max="${stock.stocks_available}">
        <button class="plus-btn">+</button>
        <span class="betrag-info">0 MA</span> <!-- Betrag-Anzeige -->
        <button class="kauf-btn" data-firma-id="${stock.id}">Kaufen</button>
        <button class="verkauf-btn" data-firma-id="${stock.id}">Verkaufen</button>
    `;
    return row;
}

// Lädt den aktuellen Kurs für eine Firma
async function loadStockPrice(stockId, row) {
    try {
        const kursResp = await fetch(`/api/kurse/verlauf/${stockId}?eintraege=1`);
        if (kursResp.ok) {
            const kursData = await kursResp.json();
            const aktuellerKurs = kursData.length > 0 ? kursData[0].price : 'Kein Kurs';
            row.querySelector('.akt-wert').textContent = `${aktuellerKurs} MA`;
        } else {
            row.querySelector('.akt-wert').textContent = 'Fehler';
        }
    } catch (error) {
        console.error(`Fehler beim Laden des Kurses für Firma ${stockId}:`, error);
        row.querySelector('.akt-wert').textContent = 'Fehler';
    }
}

// Lädt die gekauften Aktien für eine Firma
async function loadStockSummary(stockId, row) {
    try {
        const summaryResp = await fetch(`/api/aktien/${stockId}/summary`);
        if (summaryResp.ok) {
            const summaryData = await summaryResp.json();
            const totalAmount = summaryData.total_amount;

            // Überprüfen, ob totalAmount eine Zahl ist
            if (typeof totalAmount === 'number') {
                row.querySelector('.aktien-umlauf').textContent = totalAmount;
            } else {
                row.querySelector('.aktien-umlauf').textContent = 'Fehler: Ungültige Daten';
            }
        } else {
            row.querySelector('.aktien-umlauf').textContent = 'Fehler: API nicht erreichbar';
        }
    } catch (error) {
        console.error(`Fehler beim Abrufen der Daten für stock_id ${stockId}:`, error);
        row.querySelector('.aktien-umlauf').textContent = 'Fehler';
    }
}

function setupRowEventListeners(stockId, row) {
    const plusButton = row.querySelector('.plus-btn');
    const minusButton = row.querySelector('.minus-btn');
    const inputField = row.querySelector('.anzahl-input');
    const kaufButton = row.querySelector('.kauf-btn');
    const verkaufButton = row.querySelector('.verkauf-btn');
    const betragInfo = row.querySelector('.betrag-info'); // Betrag-Anzeige
    let aktuellerKurs = 0; // Speichert den aktuellen Kurs

    // Funktion zur Aktualisierung des Betrags
    const updateBetrag = () => {
        const amount = parseInt(inputField.value, 10) || 0;
        const betrag = aktuellerKurs * amount;
        betragInfo.textContent = `${betrag.toFixed(2)} MA`;
    };

    // Lade den aktuellen Kurs und aktualisiere den Betrag
    const loadAktuellerKurs = async () => {
        try {
            const kursResp = await fetch(`/api/kurse/verlauf/${stockId}?eintraege=1`);
            if (kursResp.ok) {
                const kursData = await kursResp.json();
                aktuellerKurs = kursData.length > 0 ? kursData[0].price : 0;
                updateBetrag(); // Betrag nach Kursaktualisierung berechnen
            } else {
                aktuellerKurs = 0;
                betragInfo.textContent = 'Fehler';
            }
        } catch (error) {
            console.error(`Fehler beim Laden des Kurses für stock_id ${stockId}:`, error);
            aktuellerKurs = 0;
            betragInfo.textContent = 'Fehler';
        }
    };

    // Lade den aktuellen Kurs beim Initialisieren
    loadAktuellerKurs();

    // Plus-Button: Erhöht den Wert im Eingabefeld
    plusButton.addEventListener('click', () => {
        const currentValue = parseInt(inputField.value, 10) || 0;
        const maxValue = parseInt(inputField.max, 10) || Infinity;
        if (currentValue < maxValue) {
            inputField.value = currentValue + 1;
            updateBetrag(); // Betrag aktualisieren
        }
    });

    // Minus-Button: Verringert den Wert im Eingabefeld
    minusButton.addEventListener('click', () => {
        const currentValue = parseInt(inputField.value, 10) || 0;
        const minValue = parseInt(inputField.min, 10) || 0;
        if (currentValue > minValue) {
            inputField.value = currentValue - 1;
            updateBetrag(); // Betrag aktualisieren
        }
    });

    // Kauf-Button: Sendet die Kaufanfrage an die API
    kaufButton.addEventListener('click', async () => {
        const amount = parseInt(inputField.value, 10);

        try {
            const response = await fetch(`/api/aktien/${stockId}/kaufen`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ amount }),
            });

            if (response.ok) {
                alert(`Aktien erfolgreich gekauft! Sie haben ${betragInfo.textContent} bezahlt.`);
                loadStockSummary(stockId, row); // Aktualisiere die gekauften Aktien
            } else {
                const errorData = await response.json().catch(() => null);
                console.error('Fehlerdetails:', errorData);
                alert(`Fehler beim Kauf der Aktien: ${errorData?.error || 'Unbekannter Fehler'}`);
            }
        } catch (error) {
            console.error('Fehler beim Kauf der Aktien:', error);
            alert('Fehler beim Kauf der Aktien.');
        }
    });

    // Verkaufen-Button: Sendet die Verkaufsanfrage an die API
    verkaufButton.addEventListener('click', async () => {
        const amount = parseInt(inputField.value, 10);

        try {
            const response = await fetch(`/api/aktien/${stockId}/verkaufen`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ amount: -amount }), // Negative Anzahl für Verkauf
            });

            if (response.ok) {
                alert(`Aktien erfolgreich verkauft! Sie erhalten ${betragInfo.textContent}.`);
                loadStockSummary(stockId, row); // Aktualisiere die gekauften Aktien
            } else {
                const errorData = await response.json().catch(() => null);
                console.error('Fehlerdetails:', errorData);
                alert(`Fehler beim Verkauf der Aktien: ${errorData?.error || 'Unbekannter Fehler'}`);
            }
        } catch (error) {
            console.error('Fehler beim Verkauf der Aktien:', error);
            alert('Fehler beim Verkauf der Aktien.');
        }
    });
}