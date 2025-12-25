import { state, ui } from '../state.js?v=5.8';
import { API } from '../api.js?v=5.8';
import { TicketForm } from './ticket-form.js?v=5.8';
import { t } from '../i18n.js?v=5.8';

const DashboardState = {
    activeTab: 'active', // 'active', 'history', or 'returned'
    tickets: [],
    stats: null,
    weeklyStats: null,
    
    // Pagination
    page: 0,
    limit: 20,
    hasMore: true,
    isLoadingMore: false,
    
    // Tech Stats
    techStats: null
};

export const Dashboard = {
    async load(mode = 'active') {
        const isStaff = state.user.role === 'staff' || state.user.role === 'admin';
        
        DashboardState.activeTab = mode;
        
        if (mode === 'history') {
            ui.screenTitle.textContent = t('nav_history') || 'Job History';
        } else {
            ui.screenTitle.textContent = isStaff ? t('header_shop_hub') : t('header_assigned_jobs');
        }
        
        ui.content.innerHTML = `<div class="loading">${t('loading_refining')}</div>`;
        
        // Reset local state
        DashboardState.tickets = [];
        DashboardState.stats = null;
        DashboardState.page = 0;
        DashboardState.hasMore = true;

        try {
            // Initial Load
            const promises = [this.loadTickets(true)];
            
            if (isStaff) {
                promises.push(API.getStats());
                promises.push(API.getWeeklyStats());
            }

            const results = await Promise.all(promises);
            // results[0] is handled in loadTickets
            
            if (isStaff) {
                const stats = results[1];
                const weekly = results[2];
                
                if (stats.error) throw new Error("Stats: " + stats.error);
                if (weekly.error) throw new Error("Weekly: " + weekly.error);

                DashboardState.stats = stats;
                DashboardState.weeklyStats = weekly;
            } else {
                DashboardState.stats = null;
                DashboardState.weeklyStats = null;
                
                // Fetch Tech Stats
                try {
                    const techId = state.user.tech_id;
                    if (techId) {
                        const tStats = await API.getTechStats(techId);
                        DashboardState.techStats = tStats;
                    }
                } catch(e) { console.warn("Tech stats fail", e); }
            }
            
            // Set Header Labels
            const roleBadge = document.getElementById('user-role-badge');
            if (roleBadge) roleBadge.textContent = isStaff ? t('dash_role_staff') : t('dash_role_tech');
            
            if (mode === 'history') {
                ui.screenTitle.textContent = t('nav_history') || 'Job History';
            } else {
                ui.screenTitle.textContent = isStaff ? t('header_shop_hub') : t('header_workbench');
            }

            this.render();
        } catch (error) {
            console.error(error);
            ui.content.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        }
    },

    async loadTickets(initial = false) {
        if (DashboardState.isLoadingMore && !initial) return;
        DashboardState.isLoadingMore = true;

        if (initial) {
            DashboardState.page = 0;
            DashboardState.hasMore = true;
        }

        const isStaff = state.user.role === 'staff' || state.user.role === 'admin';
        const techId = isStaff ? null : state.user.tech_id;
        const skip = DashboardState.page * DashboardState.limit;
        
        // Render loading state for button if not initial
        if (!initial) {
            const btn = document.getElementById('btn-load-more');
            if (btn) btn.textContent = t('loading_wait');
        }

        try {
            const newTickets = await API.getTickets(techId, DashboardState.activeTab, DashboardState.limit, skip);
            
            if (initial) {
                DashboardState.tickets = newTickets;
            } else {
                DashboardState.tickets = [...DashboardState.tickets, ...newTickets];
            }
            
            DashboardState.hasMore = newTickets.length === DashboardState.limit;
            DashboardState.page++;
            
        } catch (e) {
            console.error("Load tickets failed", e);
            alert(t('err_general'));
        } finally {
            DashboardState.isLoadingMore = false;
            this.renderTicketList();
        }
    },

    render() {
        const isStaff = state.user.role === 'staff' || state.user.role === 'admin';
        // Note: Count is now based on *loaded* tickets.
        const activeJobsCount = DashboardState.tickets.filter(t => !['completed', 'cancelled'].includes(t.status.toLowerCase()) && t.device_status !== 'returned').length;
        
        let html = '';
        
        if (isStaff && DashboardState.stats) {
            const s = DashboardState.stats;
            html += `
                <div style="text-align: center; margin-top: 10px; margin-bottom: 20px;">
                    <span style="font-size: 13px; font-weight: 500; color: var(--text-sub); opacity: 0.8;">${t('dash_today')} </span>
                    <span style="font-size: 14px; font-weight: 800; color: var(--accent-color);">${s.revenue_today.toLocaleString()} Ks</span>
                </div>

                <!-- Financial Pulse (Mini Chart) -->
                <div class="card" style="margin: 0 20px 24px; padding: 20px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <div>
                            <h4 style="margin: 0; font-size: 11px; text-transform: uppercase; opacity: 0.5;">${t('dash_pulse')}</h4>
                            <div style="font-size: 18px; font-weight: 800; margin-top: 2px;">${t('dash_weekly')}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 16px; font-weight: 800; color: var(--accent-color);">${DashboardState.weeklyStats.total_revenue.toLocaleString()} Ks</div>
                            <div style="font-size: 10px; opacity: 0.7; color: #10b981;">${t('dash_profit')} ${(DashboardState.weeklyStats.total_revenue - DashboardState.weeklyStats.total_expense).toLocaleString()} Ks</div>
                        </div>
                    </div>
                    
                    <div style="display: flex; align-items: flex-end; justify-content: space-between; height: 70px; gap: 6px;">
                        ${DashboardState.weeklyStats.days.map(d => {
                            const maxVal = Math.max(...DashboardState.weeklyStats.days.flatMap(day => [day.revenue, day.expense]), 1);
                            const revH = (d.revenue / maxVal) * 100;
                            const expH = (d.expense / maxVal) * 100;
                            return `
                                <div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px;">
                                    <div style="width: 100%; height: 70px; display: flex; align-items: flex-end; gap: 2px;">
                                        <div style="flex: 1; height: ${revH}%; background: var(--accent-color); border-radius: 2px 2px 0 0; opacity: 0.8; box-shadow: 0 0 5px var(--accent-glow);"></div>
                                        <div style="flex: 1; height: ${expH}%; background: #ef4444; border-radius: 2px 2px 0 0; opacity: 0.6;"></div>
                                    </div>
                                    <span style="font-size: 9px; opacity: 0.4; font-weight: 600;">${d.day}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                    <div style="display: flex; gap: 12px; margin-top: 12px; justify-content: center;">
                        <div style="display: flex; align-items: center; gap: 4px; font-size: 9px; opacity: 0.6;">
                            <div style="width: 8px; height: 8px; background: var(--accent-color); border-radius: 2px;"></div> ${t('dash_rev')}
                        </div>
                        <div style="display: flex; align-items: center; gap: 4px; font-size: 9px; opacity: 0.6;">
                            <div style="width: 8px; height: 8px; background: #ef4444; border-radius: 2px;"></div> ${t('dash_exp')}
                        </div>
                    </div>
                </div>
            `;
        } else if (!isStaff) {
             const ts = DashboardState.techStats || {};
             html += `
                <div class="card" style="margin: 20px; background: linear-gradient(135deg, rgba(245,158,11,0.1), transparent);">
                    <div style="font-size: 10px; font-weight: 800; color: var(--text-sub); text-transform: uppercase;">${t('dash_workbench')}</div>
                    
                    <div style="display: flex; gap: 16px; margin-top: 16px;">
                        <!-- Active -->
                        <div style="flex: 1; text-align: center;">
                            <span style="display: block; font-size: 24px; font-weight: 900; color: var(--accent-color);">${activeJobsCount}</span>
                            <span style="font-size: 10px; font-weight: 700; color: var(--text-sub); text-transform: uppercase;">${t('dash_active_tasks') || 'Active'}</span>
                        </div>
                        
                        <!-- Completed Today -->
                        <div style="flex: 1; text-align: center; border-left: 1px solid rgba(255,255,255,0.1);">
                            <span style="display: block; font-size: 24px; font-weight: 900; color: #10b981;">${ts.completed_today || 0}</span>
                            <span style="font-size: 10px; font-weight: 700; color: var(--text-sub); text-transform: uppercase;">${t('dash_done_today') || 'Today'}</span>
                        </div>

                        <!-- Avg Time -->
                        <div style="flex: 1; text-align: center; border-left: 1px solid rgba(255,255,255,0.1);">
                            <span style="display: block; font-size: 16px; line-height: 29px; font-weight: 800; color: #3b82f6;">${ts.avg_repair_time || t('not_applicable') || 'N/A'}</span>
                            <span style="font-size: 10px; font-weight: 700; color: var(--text-sub); text-transform: uppercase;">${t('dash_avg_time')}</span>
                        </div>
                    </div>
                </div>
            `;
        }

        // 2. Recent Activity Section
        html += `
            <div style="padding: 0 24px; margin-bottom: 12px;">
                 <h3 style="margin: 0; font-size: 12px; font-weight: 800; color: var(--text-sub); text-transform: uppercase; letter-spacing: 0.5px;">${t('dash_recent')}</h3>
            </div>
            <div class="tab-container">
                <div class="sub-tab ${DashboardState.activeTab === 'active' ? 'active' : ''}" data-tab="active">${t('tab_active')}</div>
                <div class="sub-tab ${DashboardState.activeTab === 'history' ? 'active' : ''}" data-tab="history">${t('tab_finished')}</div>
                <div class="sub-tab ${DashboardState.activeTab === 'returned' ? 'active' : ''}" data-tab="returned">${t('tab_returned')}</div>
            </div>
            <div id="ticket-list"></div>
        `;

        ui.content.innerHTML = html;
        this.renderTicketList();

        // Bind new ticket button
        const newTicketBtn = ui.content.querySelector('#btn-new-ticket');
        if (newTicketBtn) {
            newTicketBtn.addEventListener('click', () => {
                TicketForm.load();
            });
        }

        // Bind tab clicks
        ui.content.querySelectorAll('.sub-tab').forEach(tab => {
            tab.addEventListener('click', async () => {
                const mode = tab.dataset.tab;
                if (mode !== DashboardState.activeTab) {
                    DashboardState.activeTab = mode;
                    
                    // Update tab classes visually first
                    ui.content.querySelectorAll('.sub-tab').forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    
                    // Specific load for the list only
                    await this.loadTickets(true);
                }
            });
        });
    },

    renderTicketList() {
        const listContainer = ui.content.querySelector('#ticket-list');
        if (!listContainer) return;
        
        let filterStatus;
        let emptyMsgKey;
        if (DashboardState.activeTab === 'active') {
            filterStatus = t => !['completed', 'cancelled'].includes(t.status.toLowerCase()) && t.device_status !== 'returned';
            emptyMsgKey = 'empty_active';
        } else if (DashboardState.activeTab === 'history') {
            filterStatus = t => ['completed', 'cancelled'].includes(t.status.toLowerCase()) && t.device_status !== 'returned';
            emptyMsgKey = 'empty_history';
        } else {
            filterStatus = t => t.device_status === 'returned';
            emptyMsgKey = 'empty_returned';
        }
        
        const filtered = DashboardState.tickets.filter(filterStatus);

        if (filtered.length === 0 && !DashboardState.hasMore) {
            listContainer.innerHTML = `<div class="empty-state">${t(emptyMsgKey)}</div>`;
            return;
        }

        let html = filtered.map(tk => {
            const statusClass = `status-${tk.status.toLowerCase().replace(' ', '_')}`;
            const priorityClass = `status-${tk.priority.toLowerCase().replace(' ', '_')}`;
            
            const statusLabel = t('status_' + tk.status.toLowerCase().replace(' ', '_')) || tk.status;
            const prioKey = 'form_prio_' + tk.priority.toLowerCase();
            const priorityLabel = t(prioKey) === prioKey ? tk.priority : t(prioKey);

            return `
                <div class="card active-ticket" onclick="document.dispatchEvent(new CustomEvent('viewTicket', { detail: { id: ${tk.id} } }))">
                    <div class="card-header">
                        <div style="display: flex; flex-direction: column; gap: 4px;">
                            <h2 class="card-title" style="margin: 0;">${tk.device}</h2>
                            <div style="display: flex; gap: 6px; align-items: center;">
                                <span class="status-badge ${statusClass}">${statusLabel}</span>
                                <span class="status-badge ${priorityClass}">${priorityLabel}</span>
                            </div>
                        </div>
                    </div>
                    <div class="card-description" style="font-size: 14px; color: var(--text-sub); margin-bottom: 12px; margin-top: 8px;">
                        ${tk.error || t('no_desc')}
                    </div>
                    <div class="card-footer">
                        <span class="card-id" style="color: var(--accent-color); font-family: monospace; font-size: 13px;">${tk.number}</span>
                        <span class="card-date" style="font-size: 11px; opacity: 0.5;">${tk.created_at}</span>
                    </div>
                </div>
            `;
        }).join('');
        
        // Add Load More Button
        if (DashboardState.hasMore) {
            html += `
                <div style="padding: 20px; text-align: center;">
                    <button id="btn-load-more" class="btn-secondary" style="width: 100%; padding: 12px;">${t('btn_load_more') || 'Load More'}</button>
                </div>
            `;
        }
        
        listContainer.innerHTML = html;
        
        // Bind Load More
        if (DashboardState.hasMore) {
            const btn = listContainer.querySelector('#btn-load-more');
            if (btn) {
                btn.addEventListener('click', () => {
                    this.loadTickets(false);
                });
            }
        }
    }
};
