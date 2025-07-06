document.addEventListener('DOMContentLoaded', () => {
    const addBtn = document.getElementById('add-company');
    if (!addBtn) return;

    addBtn.addEventListener('click', async () => {
        // Default-Werte
        const defaultName = "Firmen Name";
        // API-Request zum Anlegen
        const response = await fetch(`/api/aktien/?name=${encodeURIComponent(defaultName)}`, {
            method: 'POST'
        });
        if (response.ok) {
            // Nach dem Anlegen: Seite neu laden oder Liste neu holen
            location.reload();
        } else {
            alert('Fehler beim Anlegen!');
        }
    });
});