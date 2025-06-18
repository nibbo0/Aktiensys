document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggleHeader');
    toggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('header-hidden');
    });
});