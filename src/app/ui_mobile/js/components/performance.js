import { state, ui } from '../state.js?v=5.8';
import { API } from '../api.js?v=5.8';
import { t } from '../i18n.js?v=5.8';

export const Performance = {
    async load() {
        ui.screenTitle.textContent = t('nav_performance') || 'Performance';
        ui.content.innerHTML = `<div class="loading">${t('loading_wait') || 'Loading...'}</div>`;

        try {
            const techId = state.user.tech_id;
            if (!techId) throw new Error("Technician ID missing");
            const data = await API.getTechnicianPerformance(techId);
            this.render(data);
        } catch (error) {
            console.error("Performance load failed", error);
            ui.content.innerHTML = `<div class="error">${error.message}</div>`;
        }
    },

    render(data) {
        const { summary, current_month, history } = data;
        const currency = t('currency_ks') || 'Ks';

        // simple helper for percentages
        const getPercent = (val, max) => Math.min(100, (val / (max || 1)) * 100);

        ui.content.innerHTML = `
            <div style="padding: 20px;">
                <!-- Efficiency Score (Radial Style) -->
                <div class="card" style="text-align: center; padding: 30px 20px; background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), transparent); margin-bottom: 24px;">
                    <div style="font-size: 11px; text-transform: uppercase; color: var(--text-sub); font-weight: 700; letter-spacing: 1px; margin-bottom: 8px;">${t('perf_efficiency') || 'Current Efficiency'}</div>
                    <div style="position: relative; width: 120px; height: 120px; margin: 0 auto 16px;">
                        <svg viewBox="0 0 36 36" style="width: 100%; height: 100%; transform: rotate(-90deg);">
                            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="3" />
                            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#10b981" stroke-width="3" stroke-dasharray="${getPercent(current_month?.efficiency_score || 0, 5)}, 100" />
                        </svg>
                        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 32px; font-weight: 900; color: #10b981;">${(current_month?.efficiency_score || 0).toFixed(1)}</div>
                    </div>
                </div>

                <!-- Metrics Grid -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
                    <div class="card" style="padding: 16px; border-left: 4px solid #3b82f6;">
                         <div style="font-size: 10px; color: var(--text-sub); text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">${t('perf_completed') || 'Completed'}</div>
                         <div style="font-size: 20px; font-weight: 800;">${current_month?.tickets_completed || 0} <span style="font-size: 12px; color: var(--text-sub); font-weight: 400;">/ ${summary?.total_tickets || 0}</span></div>
                    </div>
                    <div class="card" style="padding: 16px; border-left: 4px solid #8b5cf6;">
                         <div style="font-size: 10px; color: var(--text-sub); text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">${t('perf_revenue') || 'Revenue'}</div>
                         <div style="font-size: 16px; font-weight: 800;">${(current_month?.revenue_generated || 0).toLocaleString()}</div>
                    </div>
                </div>

                <!-- Recent Trend (Simple CSS Bars) -->
                ${history && history.length > 0 ? `
                <div style="margin-top: 32px; margin-bottom: 24px;">
                    <h3 style="font-size: 12px; text-transform: uppercase; color: var(--text-sub); margin-bottom: 16px; padding-left: 4px;">${t('perf_trend') || 'Ticket Trend'}</h3>
                    <div class="card" style="padding: 20px; display: flex; align-items: flex-end; justify-content: space-between; height: 154px; gap: 8px;">
                        ${history.slice().reverse().map(m => {
                            const h = (m.tickets_completed / (Math.max(...history.map(x => x.tickets_completed)) || 1)) * 100;
                            return `
                            <div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8px;">
                                <div style="font-size: 9px; font-weight: 700; color: #3b82f6;">${m.tickets_completed}</div>
                                <div style="width: 100%; background: linear-gradient(to top, rgba(59, 130, 246, 0.4), #3b82f6); height: ${h}px; border-radius: 4px;"></div>
                                <div style="font-size: 8px; color: var(--text-sub); text-transform: uppercase;">${new Date(m.month).toLocaleDateString(undefined, {month: 'short'})}</div>
                            </div>
                            `;
                        }).join('')}
                    </div>
                </div>
                ` : ''}

                <!-- Compensation Card -->
                <div class="card" style="padding: 20px; margin-bottom: 30px; background: linear-gradient(to bottom right, rgba(245, 158, 11, 0.05), transparent);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 16px;">
                        <span style="font-weight: 700;">${t('perf_compensation') || 'Compensation'}</span>
                        <span style="color: #f59e0b; font-weight: 800;">${((current_month?.commission_earned || 0) + (current_month?.bonuses_earned || 0)).toLocaleString()} ${currency}</span>
                    </div>
                    
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 13px;">
                            <span style="color: var(--text-sub);">${t('perf_commission') || 'Commission'}</span>
                            <span>${(current_month?.commission_earned || 0).toLocaleString()} ${currency}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 13px;">
                            <span style="color: var(--text-sub);">${t('perf_bonuses') || 'Bonuses'}</span>
                            <span>${(current_month?.bonuses_earned || 0).toLocaleString()} ${currency}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
};
