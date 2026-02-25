// Theme helper: apply saved theme early and provide toggle if missing
(function(){
    try {
        function applySavedTheme() {
            var theme = localStorage.getItem("theme");
            if (theme === "dark") {
                if (document.body) document.body.classList.add("dark");
                else document.addEventListener('DOMContentLoaded', function(){ document.body.classList.add('dark'); });
            }
        }

        applySavedTheme();

        if (typeof window.toggleDarkMode !== 'function') {
            window.toggleDarkMode = function() {
                if (!document.body) return;
                document.body.classList.toggle('dark');
                if (document.body.classList.contains('dark')) {
                    localStorage.setItem('theme', 'dark');
                } else {
                    localStorage.setItem('theme', 'light');
                }
            };
        }
    } catch (e) {
        // ignore errors on older browsers or restricted origins
    }
})();
