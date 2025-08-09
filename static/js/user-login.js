// ===== user-login.js - Configuration utilisateur =====
document.addEventListener('DOMContentLoaded', function () {
	new LoginManager({
		usernameId: 'username',
		passwordId: 'password',
		storageKey: 'theme',
		preventSubmit: true,
		simulateDelay: 2000,
		handleErrorClass: false,
		autoFocus: false
	});
});
