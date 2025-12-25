export const state = {
    user: null,
    currentScreen: 'login',
    tickets: [],
    activeTicket: null
};

export const ui = {
    pairingScreen: document.getElementById('pairing-screen'),
    loginScreen: document.getElementById('login-screen'),
    mainScreen: document.getElementById('main-screen'),
    content: document.getElementById('content'),
    pairingForm: document.getElementById('pairing-form'),
    pairingPinInput: document.getElementById('pairing-pin'),
    pairingError: document.getElementById('pairing-error'),
    loginForm: document.getElementById('login-form'),
    usernameInput: document.getElementById('username'),
    passwordInput: document.getElementById('password'),
    loginError: document.getElementById('login-error'),
    screenTitle: document.getElementById('screen-title'),
    userBadge: document.getElementById('user-role-badge'),
    logoutBtn: document.getElementById('logout-btn'),
    navItems: document.querySelectorAll('.nav-item')
};
