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

    let date = Date.now();

    let updates = [];

    Object.values(firmen).map((firma, index) => {
        updates[index] = {
            x: date,
            y: getKursAenderung(firma.kurs, firma.volatility)
        };
        firma.kurs = updates[index].y;
        firma.verlauf.push(updates[index]);

        console.log(`${firma.name}: ${firma.kurs} MA`);
    });

    if (window.kursGraph) {
        window.kursGraph.updateData(
            updates.map(u => ({ data: [u] }))
        );
    }
}

// Warte bis DOM geladen ist
document.addEventListener('DOMContentLoaded', () => {
    console.log("Kurssimulation startet...");
    // graphen setzen
    window.kursGraph.chart.updateSeries(
        Object.values(firmen).map(firma => ({
            name: firma.name,
            data: firma.verlauf,
            color: firmen.color,
        }))
    );
    aktualisiereKurse();
    console.log("Timer: " + setInterval(aktualisiereKurse, 10000));
});
