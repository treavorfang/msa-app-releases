import { state, ui } from './state.js?v=5.8';
import { Auth } from './components/auth.js?v=5.8';
import { Dashboard } from './components/dashboard.js?v=5.8';
import { TicketDetail } from './components/ticket-detail.js?v=5.8';
import { Financial } from './components/financial.js?v=5.8';
import { Inventory } from './components/inventory.js?v=5.8';
import { Customers } from './components/customers.js?v=5.8';
import { Scanner } from './components/scanner.js?v=5.8';
import { TicketForm } from './components/ticket-form.js?v=5.8';
import { Invoice } from './components/invoice.js?v=5.8';
import { Performance } from './components/performance.js?v=5.8';
import { API } from './api.js?v=5.8';
import { t, translations } from './i18n.js?v=5.8';

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 MSA Mobile v5.1 Loaded");
    
    // Apply Settings
    const savedTheme = localStorage.getItem('msa_theme') || 'auto';
    applyTheme(savedTheme);
    const savedLang = localStorage.getItem('msa_lang') || 'en';
    applyLanguage(savedLang);

    initApp();
});

function initApp() {
    // Check pairing first
    if (!checkPairing()) {
        showScreen('pairing');
        setupEventListeners();
        return;
    }

    // Check for saved user
    const savedUser = sessionStorage.getItem('msa_user');
    if (savedUser) {
        state.user = JSON.parse(savedUser);
        showScreen('main');
        Dashboard.load();
    } else {
        // Paired but not logged in
        showScreen('login');
    }

    setupEventListeners();
}

function checkPairing() {
    const pairedDate = localStorage.getItem('msa_paired_date');
    const now = new Date();
    // Use local date string (YYYY-MM-DD) to match server's daily PIN expiration
    const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    return pairedDate === today;
}

function setupEventListeners() {
    // Pairing Form
    if (ui.pairingForm) {
        ui.pairingForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = ui.pairingForm.querySelector('button');
            btn.disabled = true;
            const pin = ui.pairingPinInput.value;
            try {
                const data = await API.verifyPairing(pin);
                localStorage.setItem('msa_paired_date', data.paired_date);
                showScreen('login');
            } catch (error) {
                ui.pairingError.textContent = error.message;
            } finally {
                btn.disabled = false;
            }
        });
    }

    // Login Form
    ui.loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = ui.loginForm.querySelector('button');
        btn.disabled = true;
        const username = ui.usernameInput.value;
        const password = ui.passwordInput.value;

        try {
            await Auth.login(username, password);
            showScreen('main');
            Dashboard.load();
        } catch (error) {
            // Error handled in Auth component
        } finally {
            btn.disabled = false;
        }
    });

    // Navigation using delegation for robustness
    document.addEventListener('click', (e) => {
        const navItem = e.target.closest('.nav-item');
        if (navItem) {
            e.preventDefault();
            e.stopPropagation();
            const screen = navItem.dataset.screen;
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            navItem.classList.add('active');
            switchNav(screen);
        }
    });

    // Header Global Search (New)
    const searchBtn = document.getElementById('header-search-btn');
    const closeBtn = document.getElementById('close-search-btn');
    const searchBar = document.getElementById('header-search-bar');
    const normalHeader = document.getElementById('header-normal');
    const searchInput = document.getElementById('global-search-input');

    if (searchBtn && searchBar) {
        searchBtn.addEventListener('click', () => {
            normalHeader.style.display = 'none';
            searchBar.style.display = 'flex';
            searchInput.focus();
        });

        const closeSearch = () => {
             searchBar.style.display = 'none';
             normalHeader.style.display = 'flex';
             searchInput.value = '';
        };

        closeBtn.addEventListener('click', closeSearch);

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const query = searchInput.value.trim();
                if (query) {
                    Scanner.handleScanResult(query);
                    closeSearch();
                }
            }
        });
    }

    // Custom Events for internal navigation
    document.addEventListener('viewTicket', (e) => {
        updateGlobalFabVisibility('ticket_detail');
        TicketDetail.load(e.detail.id);
    });

    document.addEventListener('loadDashboard', () => {
        updateGlobalFabVisibility('dashboard');
        Dashboard.load();
    });

    // Global FAB Click
    const globalFab = document.getElementById('global-fab');
    if (globalFab) {
        globalFab.addEventListener('click', () => {
            const activeNav = document.querySelector('.nav-item.active');
            const screen = activeNav ? activeNav.dataset.screen : 'dashboard';

            if (screen === 'customers') {
                Customers.showCreateCustomerModal();
            } else {
                TicketForm.load();
            }
        });
    }
}

// --- Navigation ---
function showScreen(screen) {
    // Helper to clear all screens
    const screens = [ui.pairingScreen, ui.loginScreen, ui.mainScreen];
    screens.forEach(s => s.classList.remove('active'));

    if (screen === 'pairing') {
        ui.pairingScreen.classList.add('active');
        // Update Static Texts
        document.querySelector('#pairing-screen h1').textContent = t('pair_title');
        document.querySelector('#pairing-screen p').textContent = t('pair_subtitle');
        document.querySelector('label[for="pairing-pin"]').textContent = t('pair_pin_label');
        document.getElementById('pairing-pin').placeholder = t('pair_placeholder');
        document.querySelector('#pairing-form button').textContent = t('pair_btn');
        
    } else if (screen === 'login') {
        ui.loginScreen.classList.add('active');
        document.querySelector('#login-screen h1').textContent = t('app_title');
        document.querySelector('#login-screen button').textContent = t('login_title');
        document.querySelector('label[for="username"]').textContent = t('label_username');
        document.querySelector('label[for="password"]').textContent = t('label_password');
        document.getElementById('username').placeholder = t('login_user_ph');
        document.getElementById('password').placeholder = t('login_pass_ph');

    } else {
        ui.mainScreen.classList.add('active');
        // Update UI based on role
        if (state.user) {
            ui.userBadge.textContent = state.user.role.toUpperCase();
            updateNavigationForRole(state.user.role);
            updateGlobalFabVisibility(screen);
        }
    }
}

function updateGlobalFabVisibility(screen) {
    const fab = document.getElementById('global-fab');
    if (!fab) return;
    
    // Only show for staff
    const isStaff = state.user && state.user.role === 'staff';
    
    // Show on Dashboard OR Customers screen
    // screen might be undefined (init) -> dashboard
    const currentScreen = screen || 'dashboard';
    const isAllowedScreen = currentScreen === 'main' || currentScreen === 'dashboard' || currentScreen === 'customers';
    
    fab.style.display = (isStaff && isAllowedScreen) ? 'flex' : 'none';
}

function updateNavigationForRole(role) {
    const nav = document.querySelector('.bottom-nav');
    // Treat 'admin' as staff for now, or just strictly 'staff'
    if (role === 'staff' || role === 'admin') {
        nav.innerHTML = `
            <a href="#" class="nav-item active" data-screen="dashboard">
                <span class="icon">🏠</span>
                <span>${t('nav_dashboard')}</span>
            </a>
            <a href="#" class="nav-item" data-screen="inventory">
                <span class="icon">📦</span>
                <span>${t('nav_stock')}</span>
            </a>
            <a href="#" class="nav-item" data-screen="customers">
                <span class="icon">👥</span>
                <span>${t('nav_clients')}</span>
            </a>
            <a href="#" class="nav-item" data-screen="scanner">
                <span class="icon">🔍</span>
                <span>${t('nav_scan')}</span>
            </a>
            <a href="#" class="nav-item" data-screen="invoices">
                <span class="icon">🧾</span>
                <span>${t('nav_invoices')}</span>
            </a>
            <a href="#" class="nav-item" data-screen="financial">
                <span class="icon">💵</span>
                <span>${t('nav_finance')}</span>
            </a>
        `;
    } else {
        nav.innerHTML = `
            <a href="#" class="nav-item active" data-screen="dashboard">
                <span class="icon">📋</span>
                <span>${t('nav_jobs')}</span>
            </a>
            <a href="#" class="nav-item" data-screen="inventory">
                <span class="icon">📦</span>
                <span>${t('nav_stock')}</span>
            </a>
            <a href="#" class="nav-item" data-screen="performance">
                <span class="icon">📊</span>
                <span>${t('nav_performance')}</span>
            </a>
        `;
    }
}

// Add header click listener for profile (New)
document.getElementById('user-role-badge').addEventListener('click', () => {
    // Manually trigger profile view
    // Deactivate all nav items since we are in a hidden "Me" view
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    switchNav('profile');
});

function switchNav(screen) {
    updateGlobalFabVisibility(screen);
    // Refresh titles on switch
    switch (screen) {
        case 'dashboard':
            const isStaff = state.user.role === 'staff' || state.user.role === 'admin';
            ui.screenTitle.textContent = isStaff ? t('header_shop_hub') : t('header_assigned_jobs');
            Dashboard.load('active');
            break;
        case 'scanner':
            ui.screenTitle.textContent = t('nav_scan');
            Scanner.load();
            break;
        case 'inventory':
            ui.screenTitle.textContent = t('nav_stock');
            Inventory.load();
            break;
        case 'customers':
            ui.screenTitle.textContent = t('nav_clients');
            Customers.load();
            break;
        case 'new_ticket':
            TicketForm.load();
            break;
        case 'invoices':
            ui.screenTitle.textContent = t('nav_invoices');
            Invoice.load();
            break;
        case 'financial':
            ui.screenTitle.textContent = t('nav_finance');
            Financial.load();
            break;
        case 'performance':
            ui.screenTitle.textContent = t('nav_performance');
            Performance.load();
            break;
        case 'profile':
            loadProfile();
            break;
    }
}

// Profile & Settings
function loadProfile() {
    ui.screenTitle.textContent = t('header_profile');
    
    const currentTheme = localStorage.getItem('msa_theme') || 'auto';
    const currentLang = localStorage.getItem('msa_lang') || 'en';

    ui.content.innerHTML = `
        <div style="position: relative; margin-bottom: 50px;">
            <div style="height: 120px; background: linear-gradient(135deg, #1f2937, #000); border-radius: 0 0 24px 24px; position: relative; overflow: hidden;">
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; opacity: 0.2; background-image: radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0); background-size: 20px 20px;"></div>
            </div>
            <div style="position: absolute; bottom: -35px; left: 50%; transform: translateX(-50%);">
                 <div style="width: 90px; height: 90px; background: var(--accent-color); border: 4px solid var(--bg-primary); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: 800; color: #000; box-shadow: 0 10px 20px rgba(0,0,0,0.3);">
                     ${state.user.user.name.charAt(0).toUpperCase()}
                 </div>
            </div>
        </div>

        <div style="text-align: center; margin-bottom: 32px; padding: 0 20px;">
            <h2 style="font-size: 24px; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.5px;">${state.user.user.name}</h2>
            <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.05); padding: 6px 16px; border-radius: 20px; font-size: 11px; font-weight: 700; color: var(--accent-color); letter-spacing: 1px; text-transform: uppercase;">
                <span>🛡️</span> ${state.user.role} ${t('prof_access')}
            </div>
        </div>

        <div class="card" style="margin-bottom: 24px; padding: 0; overflow: hidden; border: 1px solid rgba(255,255,255,0.05);">
             <div style="padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.05); background: rgba(255,255,255,0.02); font-weight: 700; font-size: 13px; letter-spacing: 0.5px; color: var(--text-sub);">
                ${t('profile_settings')}
            </div>
            
            <!-- Theme Setting -->
            <div style="padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 18px;">🎨</span>
                    <span>${t('profile_appearance')}</span>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 4px; border-radius: 8px; display: flex; gap: 4px;">
                    <button class="theme-btn ${currentTheme === 'light' ? 'active' : ''}" data-theme="light" style="padding: 6px 12px; border: none; border-radius: 6px; font-size: 12px; cursor: pointer;">☀️</button>
                    <button class="theme-btn ${currentTheme === 'auto' ? 'active' : ''}" data-theme="auto" style="padding: 6px 12px; border: none; border-radius: 6px; font-size: 12px; cursor: pointer;">Auto</button>
                    <button class="theme-btn ${currentTheme === 'dark' ? 'active' : ''}" data-theme="dark" style="padding: 6px 12px; border: none; border-radius: 6px; font-size: 12px; cursor: pointer;">🌙</button>
                </div>
            </div>

             <!-- Language Setting -->
            <div style="padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 18px;">🌐</span>
                    <span>${t('profile_language')}</span>
                </div>
                <select id="lang-select" style="background: rgba(255,255,255,0.1); border: none; color: white; padding: 6px 10px; border-radius: 6px; outline: none;">
                    <option value="en" ${currentLang === 'en' ? 'selected' : ''}>English</option>
                    <option value="my" ${currentLang === 'my' ? 'selected' : ''}>Burmese</option>
                </select>
            </div>
        </div>

        <div style="display: flex; flex-direction: column; gap: 12px;">
            <button class="btn-primary" id="view-performance" style="background: rgba(16,185,129,0.05); border: 1px solid rgba(16,185,129,0.1); color: #10b981; justify-content: flex-start; padding: 16px;">
                <span style="margin-right: 12px; font-size: 18px;">📊</span> ${t('nav_performance') || 'Performance'}
            </button>
            <button class="btn-primary" id="change-pin" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); color: var(--text-main); justify-content: flex-start; padding: 16px;">
                <span style="margin-right: 12px; font-size: 18px;">🔒</span> ${t('prof_change_pin')}
            </button>
            <button class="btn-primary" id="logout-btn-profile" style="background: rgba(239,68,68,0.05); border: 1px solid rgba(239,68,68,0.2); color: #ef4444; justify-content: flex-start; padding: 16px;">
                 <span style="margin-right: 12px; font-size: 18px;">🚪</span> ${t('profile_signout')}
            </button>
        </div>
        
        <div style="margin-top: 32px; text-align: center; opacity: 0.3; font-size: 11px;">
            MSA Mobile v5.1.0<br>
            Build 2025.12.24
        </div>
    `;

    // Theme Handlers
    ui.content.querySelectorAll('.theme-btn').forEach(btn => {
        btn.addEventListener('click', () => {
             const theme = btn.dataset.theme;
             applyTheme(theme);
             ui.content.querySelectorAll('.theme-btn').forEach(b => {
                 b.classList.remove('active');
                 b.style.background = 'transparent';
                 b.style.color = '#888';
             });
             btn.classList.add('active');
             btn.style.background = 'var(--accent-color)';
             btn.style.color = '#000';
        });
    });

    // Language Handler
    ui.content.querySelector('#lang-select').addEventListener('change', (e) => {
        applyLanguage(e.target.value);
        // Reload profile to reflect language change immediately
        loadProfile();
        // Also update navigation
        if (state.user) updateNavigationForRole(state.user.role);
    });

    ui.content.querySelector('#view-performance').addEventListener('click', () => {
        switchNav('performance');
    });

    ui.content.querySelector('#change-pin').addEventListener('click', () => {
        alert(t('prof_desktop_msg'));
    });

    ui.content.querySelector('#logout-btn-profile').addEventListener('click', () => {
        if (confirm(t('prof_logout_confirm'))) {
            Auth.logout();
            showScreen('login');
        }
    });

    // Init button styles for theme
    const activeThemeBtn = ui.content.querySelector(`.theme-btn[data-theme="${currentTheme}"]`);
    if(activeThemeBtn) {
        activeThemeBtn.style.background = 'var(--accent-color)';
        activeThemeBtn.style.color = '#000';
    }
}

function applyTheme(theme) {
    localStorage.setItem('msa_theme', theme);
    document.body.classList.remove('theme-light', 'theme-dark');
    
    if (theme === 'auto') {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.body.classList.add('theme-dark');
        } else {
             document.body.classList.add('theme-light');
        }
    } else {
        document.body.classList.add(`theme-${theme}`);
    }
}

function applyLanguage(lang) {
    localStorage.setItem('msa_lang', lang);
    document.documentElement.lang = lang;
    
    // Update placeholders if on search screen
    const searchInput = document.getElementById('global-search-input');
    if (searchInput) searchInput.placeholder = t('search_placeholder');
}
