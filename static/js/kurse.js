const verlauf = new PollingValue(
    window.location.origin, () => "/api/kurse/verlauf/?eintraege=20", {},
);

async function getStockName(stockId) {
    return await fetch(window.location.origin + `/api/aktien/${stockId}`)
        .then(res => res.json())
        .then(stock => stock["name"]);
}

async function getStockColor(stockId) {
    return await fetch(window.location.origin + `/api/aktien/${stockId}`)
        .then(res => res.json())
        .then(stock => stock["color"]);
}

async function setSeries(stocks) {
    if (!stocks) {
        return;
    }
    let names = await Promise.all(Object.keys(stocks).map(getStockName));
    let colors = await Promise.all(Object.keys(stocks).map(getStockColor));
    window.kursGraph.chart.updateSeries(
        Object.values(stocks)
            .map((hist, index) => {
                return {
                    name: names[index],
                    data: hist.toReversed().map(({price, valid_after}) => ({
                        x: Date.parse(valid_after),
                        y: price,
                    })),
                    color: colors[index],
                };
            })
    );
}

async function appendSeries(changes) {
    let values = new Array(verlauf.value.length);
    changes.forEach(async (change) => {
        if (change.type !== "updated") {
            throw new Error(`Can only work with updated stocks (not ${change.type}).`);
        }
        if (change.diff.type !== "appended") {
            throw new Error(`Can only work with appended stock values (not ${change.type}).`);
        }
        let appended = change.diff.val;
        let chartIndex = Object.keys(verlauf.value).indexOf(change.key);
        values[chartIndex] = {
            data: [{
                x: Date.parse(appended.valid_after),
                y: appended.price,
            }],
        };
    })
    console.log(`would append data: ${JSON.stringify(values)}`);
    window.kursGraph.chart.appendData(values);
}

document.addEventListener('DOMContentLoaded', () => {

    const toggleBtn = document.getElementById('toggleHeader');
    toggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('header-hidden');
    });

    verlauf.addEventListener('valuechange', ({detail: d}) => {
        switch (d.diff.type) {
        case 'set':
            setSeries(d.diff.val);
            break;
        case 'changed':
            if (d.diff.changes.every(c => c.type === "updated" && c.diff.type === "appended")) {
                appendSeries(d.diff.changes);
                break;
            } else {
                console.log("check failed");
            }
        default:
            setSeries(d.diff.val);
            console.log(d.diff);
        }
    });

    verlauf.start();
});
