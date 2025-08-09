// ===== loginManager.js - Module principal =====
class LoginManager {
	constructor(config) {
		this.config = {
			// Configuration par défaut
			formSelector: '.login-form',
			submitButtonSelector: '.submit-button',
			themeToggleSelector: '#theme-toggle',
			themeIconSelector: '.theme-icon',
			storageKey: 'theme',
			loadingText: 'Connexion en cours...',
			submitText: 'Se connecter',
			preventSubmit: false,
			autoFocus: false,
			handleErrorClass: false,
			simulateDelay: 0,
			// Fusionner avec la config fournie
			...config
		};

		this.form = document.querySelector(this.config.formSelector);
		this.submitButton = document.querySelector(this.config.submitButtonSelector);
		this.usernameInput = document.getElementById(this.config.usernameId);
		this.passwordInput = document.getElementById(this.config.passwordId);
		this.themeToggle = document.getElementById('theme-toggle');
		this.themeIcon = document.querySelector(this.config.themeIconSelector);

		this.init();
	}

	init() {
		this.initTheme();
		this.bindThemeEvents();
		this.bindFormEvents();
		this.bindKeyboardEvents();
		
		if (this.config.autoFocus && this.usernameInput && !this.usernameInput.value) {
			this.usernameInput.focus();
		}
	}

	// ===== GESTION DU THÈME =====
	initTheme() {
		const savedTheme = localStorage.getItem(this.config.storageKey);
		const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

		if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
			this.enableDarkTheme();
		} else {
			this.enableLightTheme();
		}
	}

	enableDarkTheme() {
		document.body.classList.add('dark-theme');
		if (this.themeIcon) this.themeIcon.textContent = '☀️';
		if (this.themeToggle) {
			this.themeToggle.setAttribute('aria-label', 'Basculer vers le thème clair');
			this.themeToggle.setAttribute('title', 'Passer au thème clair');
		}
		localStorage.setItem(this.config.storageKey, 'dark');
	}

	enableLightTheme() {
		document.body.classList.remove('dark-theme');
		if (this.themeIcon) this.themeIcon.textContent = '🌙';
		if (this.themeToggle) {
			this.themeToggle.setAttribute('aria-label', 'Basculer vers le thème sombre');
			this.themeToggle.setAttribute('title', 'Passer au thème sombre');
		}
		localStorage.setItem(this.config.storageKey, 'light');
	}

	toggleTheme() {
		const isDark = document.body.classList.contains('dark-theme');
		if (isDark) {
			this.enableLightTheme();
		} else {
			this.enableDarkTheme();
		}

		// Animation de feedback
		if (this.themeToggle) {
			this.themeToggle.style.transform = 'scale(0.9)';
			setTimeout(() => {
				this.themeToggle.style.transform = 'scale(1)';
			}, 150);
		}
	}

	bindThemeEvents() {
		if (!this.themeToggle) return;

		this.themeToggle.addEventListener('click', () => this.toggleTheme());

		this.themeToggle.addEventListener('keydown', (e) => {
			if (e.key === 'Enter' || e.key === ' ') {
				e.preventDefault();
				this.toggleTheme();
			}
		});

		// Écouter les changements de préférence système
		window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
			if (!localStorage.getItem(this.config.storageKey)) {
				if (e.matches) {
					this.enableDarkTheme();
				} else {
					this.enableLightTheme();
				}
			}
		});
	}

	// ===== VALIDATION =====
	validateField(input) {
		if (!input) return true;
		
		const isValid = input.checkValidity();
		input.setAttribute('aria-invalid', !isValid);

		// Gestion optionnelle de la classe d'erreur
		if (this.config.handleErrorClass && isValid) {
			input.classList.remove('error');
		}

		return isValid;
	}

	bindFormEvents() {
		if (!this.form) return;

		// Validation en temps réel
		if (this.usernameInput) {
			this.usernameInput.addEventListener('blur', () => this.validateField(this.usernameInput));
		}
		if (this.passwordInput) {
			this.passwordInput.addEventListener('blur', () => this.validateField(this.passwordInput));
		}

		// Soumission du formulaire
		this.form.addEventListener('submit', (e) => this.handleSubmit(e));
	}

	handleSubmit(e) {
		// Validation complète
		const isUsernameValid = this.validateField(this.usernameInput);
		const isPasswordValid = this.validateField(this.passwordInput);

		if (!isUsernameValid || !isPasswordValid) {
			e.preventDefault();
			// Focus sur le premier champ invalide
			const firstInvalid = this.form.querySelector('[aria-invalid="true"]');
			if (firstInvalid) {
				firstInvalid.focus();
			}
			return;
		}

		// Si on doit empêcher la soumission (mode simulation)
		if (this.config.preventSubmit) {
			e.preventDefault();
		}

		// Animation de chargement
		this.startLoading();

		// Simulation optionnelle ou restauration en cas d'erreur
		if (this.config.simulateDelay > 0) {
			setTimeout(() => {
				console.log('Tentative de connexion...');
				this.stopLoading();
			}, this.config.simulateDelay);
		}
	}

	startLoading() {
		document.body.classList.add('loading');
		if (this.submitButton) {
			this.submitButton.textContent = this.config.loadingText;
			this.submitButton.disabled = true;
		}
	}

	stopLoading() {
		document.body.classList.remove('loading');
		if (this.submitButton) {
			this.submitButton.textContent = this.config.submitText;
			this.submitButton.disabled = false;
		}
	}

	bindKeyboardEvents() {
		document.addEventListener('keydown', (e) => {
			// Effacer les champs avec Échap
			if (e.key === 'Escape') {
				if (this.usernameInput) this.usernameInput.value = '';
				if (this.passwordInput) this.passwordInput.value = '';
				if (this.usernameInput) this.usernameInput.focus();
			}

			// Raccourci clavier pour toggle thème : Ctrl/Cmd + Shift + T
			if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
				e.preventDefault();
				this.toggleTheme();
			}
		});
	}
}
