const firmen = {
    baekerei:{
        name: "Bäckerei",
        color: "#ffd966",
        kurs: 100,
        volatility: 0.05,
        verlauf: [] // Array für Kursverlauf
    },
    saftbar:{
        name: "Saftbar",
        color: "#f44336",
        kurs: 150,
        volatility: 0.07,
        verlauf: []
    },
    kueche:{
        name: "Küche",
        color: "#4caf50",
        kurs: 200,
        volatility: 0.3,
        verlauf: []
    },
    bank:{
        name: "Bank",
        color: "#2196f3",
        kurs: 360,
        volatility: 0.1,
        verlauf: []
    },
};

function getKursAenderung(aktuellerKurs, volatility) {
    const zufallsFaktor = Math.random() * 2 - 1;
    const aenderung = aktuellerKurs * volatility * zufallsFaktor;
    return Math.round((aktuellerKurs + aenderung)*100) / 100;
}

function aktualisiereKurse() {
    console.log("=== Neue Kurse ===");

    for (let firma in firmen) {
        firmen[firma].kurs = getKursAenderung(firmen[firma].kurs, firmen[firma].volatility);
        firmen[firma].verlauf.push(firmen[firma].kurs);
        
        if (firmen[firma].verlauf.length > 20) {
            firmen[firma].verlauf.shift();
        }
        
        console.log(`${firmen[firma].name}: ${firmen[firma].kurs} MA`);
    }

    // Prüfe ob Graph verfügbar ist
    if (window.kursGraph) {
        window.kursGraph.updateData(firmen);
    }
}

// Warte bis DOM geladen ist
document.addEventListener('DOMContentLoaded', () => {
    console.log("Kurssimulation startet...");
    aktualisiereKurse();
    setInterval(aktualisiereKurse, 5000);
});