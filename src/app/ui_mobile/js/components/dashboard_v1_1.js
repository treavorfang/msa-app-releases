import { state, ui } from '../state.js';
import { API } from '../api.js';
import { TicketForm } from './ticket-form.js';

const DashboardState = {
    activeTab: 'active', // 'active' or 'history'
    tickets: [],
    stats: null
};

export const Dashboard = {
    async load() {
        const isStaff = state.user.role === 'staff';
        ui.screenTitle.innerHTML = ''; // Clean slate
        ui.screenTitle.textContent = isStaff ? 'Shop Hub' : 'Assigned Jobs';
        ui.content.innerHTML = '<div class="loading">Refining your workspace...</div>';

        try {
            if (isStaff) {
                // Parallel fetch for speed
                const [tickets, stats] = await Promise.all([
                    API.getTickets(),
                    API.getStats()
                ]);
                DashboardState.tickets = tickets;
                DashboardState.stats = stats;
            } else {
                DashboardState.tickets = await API.getTickets(state.user.user.id);
                DashboardState.stats = null;
            }
            this.render();
        } catch (error) {
            ui.content.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        }
    },

    render() {
        const isStaff = state.user.role === 'staff';
        const activeJobs = DashboardState.tickets.filter(t => !['completed', 'cancelled'].includes(t.status.toLowerCase()));
        
        let html = '';
        
        if (isStaff && DashboardState.stats) {
            const s = DashboardState.stats;
            
            // Modern Header with Compact Revenue badge
            ui.screenTitle.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
                    <span>Shop Hub</span>
                    <div class="revenue-badge">
                        <span>💰</span>
                        <span>${s.revenue_today.toLocaleString()}</span>
                    </div>
                </div>
            `;

            html += `
                <div class="stats-strip">
                    <div class="stat-chip active">
                        <div class="stat-chip-val">${s.active_tickets}</div>
                        <div class="stat-chip-label">Active</div>
                    </div>
                    <div class="stat-chip" style="${s.urgent_tickets > 0 ? 'border-color: #ef4444; background: rgba(239, 68, 68, 0.05);' : ''}">
                        <div class="stat-chip-val" style="${s.urgent_tickets > 0 ? 'color: #ef4444;' : ''}">${s.urgent_tickets}</div>
                        <div class="stat-chip-label">Urgent</div>
                    </div>
                    <div class="stat-chip">
                        <div class="stat-chip-val">${s.pending_parts}</div>
                        <div class="stat-chip-label">Parts</div>
                    </div>
                    <div class="stat-chip">
                        <div class="stat-chip-val" style="color: #10b981;">${s.ready_pickup}</div>
                        <div class="stat-chip-label">Ready</div>
                    </div>
                    <div class="stat-chip">
                        <div class="stat-chip-val" style="color: #3b82f6;">${s.returned_today || 0}</div>
                        <div class="stat-chip-label">Returned</div>
                    </div>
                </div>
            `;
        } else if (!isStaff) {
             html += `
                <div class="card" style="padding: 20px 24px; background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(0,0,0,0.2)); margin-bottom: 20px;">
                    <div style="font-size: 10px; font-weight: 800; color: var(--text-sub); text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 12px; opacity: 0.6;">Workbench</div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: baseline; gap: 12px;">
                            <span style="font-size: 36px; font-weight: 900; color: var(--accent-color); line-height: 1;">${activeJobs.length}</span>
                            <span style="font-size: 11px; font-weight: 700; color: var(--text-sub); text-transform: uppercase; letter-spacing: 0.5px;">Active Tasks</span>
                        </div>
                        <div style="font-size: 20px; color: var(--text-sub); opacity: 0.5;">📋</div>
                    </div>
                </div>
            `;
        }

        // 2. Sub-Tabs Toggle
        html += `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                 <h3 style="margin: 0; font-size: 12px; opacity: 0.7;">Recent Activity</h3>
            </div>
            <div class="tab-container">
                <div class="sub-tab ${DashboardState.activeTab === 'active' ? 'active' : ''}" data-tab="active">In Progress</div>
                <div class="sub-tab ${DashboardState.activeTab === 'history' ? 'active' : ''}" data-tab="history">Finished</div>
            </div>
            <div id="ticket-list"></div>
            <div style="font-size: 8px; color: var(--text-sub); opacity: 0.2; text-align: center; margin-top: 16px;">v1.1-compact</div>
        `;

        // 3. FAB (Staff Only)
        if (isStaff) {
            html += `<button class="fab" id="fab-new-ticket"></button>`;
        }

        ui.content.innerHTML = html;
        this.renderTicketList();

        // Bind FAB / New Ticket button
        const newTicketBtn = ui.content.querySelector('#btn-new-ticket, #fab-new-ticket');
        if (newTicketBtn) {
            newTicketBtn.addEventListener('click', () => {
                TicketForm.load();
            });
        }

        // Bind tab clicks
        ui.content.querySelectorAll('.sub-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                DashboardState.activeTab = tab.dataset.tab;
                this.render();
            });
        });
    },

    renderTicketList() {
        const listContainer = ui.content.querySelector('#ticket-list');
        const filterStatus = DashboardState.activeTab === 'active' 
            ? t => !['completed', 'cancelled'].includes(t.status.toLowerCase())
            : t => ['completed', 'cancelled'].includes(t.status.toLowerCase());
        
        const filtered = DashboardState.tickets.filter(filterStatus);

        if (filtered.length === 0) {
            listContainer.innerHTML = `<div class="empty-state">No ${DashboardState.activeTab} jobs items.</div>`;
            return;
        }

        listContainer.innerHTML = filtered.map(t => {
            const isActive = !['completed', 'cancelled', 'unrepairable'].includes(t.status.toLowerCase());
            return `
                <div class="ticket-row ${isActive ? 'active-ticket' : ''}" data-ticket-id="${t.id}">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                            <span style="font-weight: 800; color: var(--accent-color); font-size: 11px;">#${t.number.split('-').pop()}</span>
                            <div style="font-size: 14px; font-weight: 700; color: var(--text-main);">${t.device}</div>
                        </div>
                        <div style="font-size: 11px; color: var(--text-sub); display: flex; justify-content: space-between; padding-right: 12px;">
                            <span>${t.error || 'General Service'}</span>
                            <span style="opacity: 0.5;">${t.created_at}</span>
                        </div>
                    </div>
                    <span class="status-badge status-${t.status.toLowerCase()}" style="font-size: 8px; padding: 2px 6px;">${t.status.split('_')[0]}</span>
                </div>
            `;
        }).join('');

        // Re-bind listeners
        let loadingTicket = false;
        listContainer.querySelectorAll('.ticket-row').forEach(card => {
            card.addEventListener('click', () => {
                if (loadingTicket) return;
                loadingTicket = true;
                const event = new CustomEvent('viewTicket', { detail: { id: card.dataset.ticketId } });
                document.dispatchEvent(event);
                // Reset after a short delay
                setTimeout(() => { loadingTicket = false; }, 1000);
            });
        });
    }
};
