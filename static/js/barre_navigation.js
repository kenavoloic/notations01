/**
 * Navbar JavaScript - Fonctionnalités pour la navigation
 * Fichier: static/js/navbar.js
 */

// Variables globales
let mobileMenuOpen = false;

/**
 * Toggle du menu mobile
 */
function toggleMobileMenu() {
    const navbarCollapse = document.getElementById('navbarNav');
    const toggler = document.querySelector('.navbar-toggler');
    
    mobileMenuOpen = !mobileMenuOpen;
    
    if (mobileMenuOpen) {
        navbarCollapse.classList.add('show');
        toggler.classList.add('active');
    } else {
        navbarCollapse.classList.remove('show');
        toggler.classList.remove('active');
    }
}

/**
 * Toggle des dropdowns
 */
function toggleDropdown(element) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    // Fermer tous les autres dropdowns
    document.querySelectorAll('.dropdown.show').forEach(dropdown => {
        if (!dropdown.contains(element)) {
            dropdown.classList.remove('show');
        }
    });
    
    // Toggle le dropdown actuel
    const dropdown = element.closest('.dropdown');
    if (dropdown) {
        dropdown.classList.toggle('show');
    }
}

/**
 * Fermer les dropdowns en cliquant ailleurs
 */
function closeDropdownsOnOutsideClick(event) {
    if (!event.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown.show').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
}

/**
 * Fermer le menu mobile en cliquant sur un lien
 */
function closeMobileMenuOnLinkClick(event) {
    if (window.innerWidth <= 768 && event.target.matches('.nav-link, .dropdown-item')) {
        const navbarCollapse = document.getElementById('navbarNav');
        const toggler = document.querySelector('.navbar-toggler');
        
        navbarCollapse.classList.remove('show');
        toggler.classList.remove('active');
        mobileMenuOpen = false;
    }
}

/**
 * Toggle du thème clair/sombre
 */
function toggleTheme() {
    const body = document.body;
    const themeIcon = document.getElementById('theme-icon');
    
    if (!themeIcon) {
        console.warn('Élément theme-icon non trouvé');
        return;
    }
    
    const isDark = body.classList.toggle('dark-theme');
    
    // Mettre à jour l'icône
    themeIcon.textContent = isDark ? '☀️' : '🌙';
    
    // Sauvegarder la préférence
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    
    // Dispatch un événement personnalisé pour les autres composants
    window.dispatchEvent(new CustomEvent('themeChanged', { 
        detail: { isDark } 
    }));
}

/**
 * Charger le thème sauvegardé
 */
function loadSavedTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const themeIcon = document.getElementById('theme-icon');
    
    if (!themeIcon) {
        console.warn('Élément theme-icon non trouvé lors du chargement du thème');
        return;
    }
    
    const shouldUseDarkTheme = savedTheme === 'dark' || (!savedTheme && prefersDark);
    
    if (shouldUseDarkTheme) {
        document.body.classList.add('dark-theme');
        themeIcon.textContent = '☀️';
    } else {
        document.body.classList.remove('dark-theme');
        themeIcon.textContent = '🌙';
    }
}

/**
 * Gestion du redimensionnement de la fenêtre
 */
function handleWindowResize() {
    const navbarCollapse = document.getElementById('navbarNav');
    const toggler = document.querySelector('.navbar-toggler');
    
    // Fermer le menu mobile si on passe en desktop
    if (window.innerWidth > 768) {
        navbarCollapse.classList.remove('show');
        toggler.classList.remove('active');
        mobileMenuOpen = false;
        
        // Fermer aussi tous les dropdowns
        document.querySelectorAll('.dropdown.show').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
}

/**
 * Gestion des touches clavier
 */
function handleKeyboardNavigation(event) {
    // Échapper pour fermer les dropdowns et le menu mobile
    if (event.key === 'Escape') {
        // Fermer les dropdowns
        document.querySelectorAll('.dropdown.show').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
        
        // Fermer le menu mobile
        if (mobileMenuOpen) {
            toggleMobileMenu();
        }
    }
    
    // Enter sur les éléments avec dropdown-toggle
    if (event.key === 'Enter' && event.target.classList.contains('dropdown-toggle')) {
        event.preventDefault();
        toggleDropdown(event.target);
    }
}

/**
 * Initialisation de la navbar
 */
function initNavbar() {
    // Charger le thème sauvegardé
    loadSavedTheme();
    
    // Event listeners
    document.addEventListener('click', closeDropdownsOnOutsideClick);
    document.addEventListener('click', closeMobileMenuOnLinkClick);
    document.addEventListener('keydown', handleKeyboardNavigation);
    window.addEventListener('resize', handleWindowResize);
    
    // Listener pour les changements de préférence système
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addEventListener('change', function(e) {
        // Ne pas changer automatiquement si l'utilisateur a une préférence sauvegardée
        if (!localStorage.getItem('theme')) {
            if (e.matches) {
                document.body.classList.add('dark-theme');
                document.getElementById('theme-icon').textContent = '☀️';
            } else {
                document.body.classList.remove('dark-theme');
                document.getElementById('theme-icon').textContent = '🌙';
            }
        }
    });
    
    // Améliorer l'accessibilité - ajouter des attributs ARIA
    document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
        toggle.setAttribute('aria-haspopup', 'true');
        toggle.setAttribute('aria-expanded', 'false');
    });
    
    // Observer les changements de classe pour les dropdowns
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const dropdown = mutation.target;
                const toggle = dropdown.querySelector('.dropdown-toggle');
                
                if (toggle) {
                    const isOpen = dropdown.classList.contains('show');
                    toggle.setAttribute('aria-expanded', isOpen.toString());
                }
            }
        });
    });
    
    // Observer tous les dropdowns
    document.querySelectorAll('.dropdown').forEach(dropdown => {
        observer.observe(dropdown, { attributes: true });
    });
    
    console.log('Navbar initialisée avec succès');
}

/**
 * Utilitaires publics
 */
window.NavbarUtils = {
    closeAllDropdowns: function() {
        document.querySelectorAll('.dropdown.show').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    },
    
    closeMobileMenu: function() {
        if (mobileMenuOpen) {
            toggleMobileMenu();
        }
    },
    
    getCurrentTheme: function() {
        return document.body.classList.contains('dark-theme') ? 'dark' : 'light';
    },
    
    setTheme: function(theme) {
        const body = document.body;
        const themeIcon = document.getElementById('theme-icon');
        
        if (theme === 'dark') {
            body.classList.add('dark-theme');
            if (themeIcon) themeIcon.textContent = '☀️';
        } else {
            body.classList.remove('dark-theme');
            if (themeIcon) themeIcon.textContent = '🌙';
        }
        
        localStorage.setItem('theme', theme);
    }
};

// Initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', initNavbar);

// Support pour les anciens navigateurs
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNavbar);
} else {
    initNavbar();
}
