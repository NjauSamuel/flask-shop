const toggleButton = document.querySelector('[data-collapse-toggle="navbar-sticky"]');
const navbar = document.getElementById('navbar-sticky');
const themeToggleBtn = document.getElementById('theme-toggle');
const darkIcon = document.getElementById('theme-toggle-dark-icon');
const lightIcon = document.getElementById('theme-toggle-light-icon');

toggleButton.addEventListener('click', () => {
    navbar.classList.toggle('hidden');
});


// Check if user has set a theme preference previously
if (localStorage.getItem('color-theme') === 'dark' || (!('color-theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
    lightIcon.classList.remove('hidden');
} else {
    darkIcon.classList.remove('hidden');
}

themeToggleBtn.addEventListener('click', function () {
    // Toggle dark mode icons
    darkIcon.classList.toggle('hidden');
    lightIcon.classList.toggle('hidden');

    // If dark mode is enabled
    if (document.documentElement.classList.contains('dark')) {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('color-theme', 'light');
    } else {
        document.documentElement.classList.add('dark');
        localStorage.setItem('color-theme', 'dark');
    }
});
