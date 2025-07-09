class KursGraph {
    constructor(initSeries) {
        this.container = document.getElementById("chart-container");
        this.chart = this.initChart(initSeries);
    }

    initChart(initSeries) {
        let chart = new ApexCharts(this.container, {
            chart: {
                type: 'line',
                height: '100%',
                animations: {
                    enabled: true,
                    easing: 'linear',
                    speed: 1000,
                    animateGradually: {
                        enabled: true,
                    },
                    dynamicAnimation: {
                        speed: 5000
                    },
                },
            },
            datalabels: { enabled: false },
            markers: { size: 0 },
            title: {
                text: "D(AU)-Jones",
                style: { color: "#e0d9cf" },
            },
            series: initSeries ? initSeries : [],
            xaxis: {
                type: 'datetime',
                labels: {
                    style: { colors: ["#fff"] },
                },
                // 10 Einträge * Intervallänge (in ms)
                range: 10 * 5000,
            },
            yaxis: {
                title: {
                    text: "Kurs",
                    style: { color: "#e0d9cf" },
                },
                labels: {
                    style: { colors: ["#fff"] },
                },
            },
            legend: {
                position: 'top',
                labels: {
                    colors: ['#fff'],
                },
            },
            tooltip: {
                x: { format: "H:mm:ss" },
            },
            noData: {
                text: "Keine Daten...",
            },
        });

        chart.render();
        return chart;
    }

    updateData(updates) {
        const zeit = new Date().toLocaleTimeString();

        console.log("updating with:");
        console.log(updates);

        this.chart.appendData(updates);
    }
}

// Erstelle globale Instanz
window.kursGraph = new KursGraph();
