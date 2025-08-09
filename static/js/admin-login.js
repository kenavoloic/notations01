// ===== admin-login.js - Configuration admin =====
document.addEventListener('DOMContentLoaded', function () {
	new LoginManager({
		usernameId: 'id_username',
		passwordId: 'id_password',
		storageKey: 'admin-theme',
		preventSubmit: false, // Laisser Django gérer la soumission
		simulateDelay: 0,
		handleErrorClass: true, // Gestion de la classe .error
		autoFocus: true // Focus automatique sur le premier champ
	});
});
