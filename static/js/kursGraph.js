class KursGraph {
    constructor() {
        this.ctx = document.getElementById('kursChart').getContext('2d');
        this.chart = this.initChart();
    }

    initChart() {
        return new Chart(this.ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                animation: false, // Schnellere Updates
                plugins: {
                    legend: { 
                        position: 'top',
                        labels: { color: '#fff' }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        },
                        ticks: { color: '#fff' }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        },
                        ticks: { color: '#fff' }
                    }
                }
            }
        });
    }

    updateData(firmen) {
        const zeit = new Date().toLocaleTimeString();
        
        // Aktualisiere Labels (Zeitachse)
        this.chart.data.labels = Array(20).fill('');
        this.chart.data.labels[19] = zeit;

        // Aktualisiere Datensätze
        this.chart.data.datasets = Object.values(firmen).map(firma => ({
            label: firma.name,
            data: firma.verlauf,
            borderColor: firma.color,
            backgroundColor: firma.color + '33',
            tension: 0.3
        }));

        this.chart.update('none'); // Update ohne Animation
    }
}

// Erstelle globale Instanz
window.kursGraph = new KursGraph();