(() => {
    const themeStorageKey = 'blogdelgoat-theme';
    const savedTheme = localStorage.getItem(themeStorageKey);

    if (savedTheme === 'light') {
        document.documentElement.dataset.theme = 'light';
    }

    document.addEventListener('DOMContentLoaded', () => {
        const themeToggle = document.getElementById('theme-toggle');
        if (!themeToggle) {
            return;
        }

        themeToggle.checked = document.documentElement.dataset.theme === 'light';
        themeToggle.addEventListener('change', () => {
            const theme = themeToggle.checked ? 'light' : 'dark';
            document.documentElement.dataset.theme = theme;
            localStorage.setItem(themeStorageKey, theme);
        });
    });
})();
