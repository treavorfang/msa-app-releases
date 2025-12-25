import { state, ui } from '../state.js?v=5.8';
import { API } from '../api.js?v=5.8';
import { t } from '../i18n.js?v=5.8';

export const Financial = {
    // State
    state: {
        transactions: [],
        summary: null,
        page: 0,
        limit: 20,
        hasMore: true,
        isLoadingMore: false,
        filterType: null // null (All), 'income', 'expense'
    },

    async load() {
        ui.screenTitle.textContent = t('fin_title');
        ui.content.innerHTML = `<div class="loading">${t('fin_loading')}</div>`;
        
        try {
            // Load Summary (independent of list filter)
            const summaryData = await API.getFinancialSummary(30);
            this.state.summary = summaryData.summary;
            
            // Initial List Load
            this.resetListState();
            await this.loadTransactions(true);
            
        } catch (error) {
            ui.content.innerHTML = `<div class="error">Failed to load: ${error.message}</div>`;
        }
    },
    
    resetListState() {
        this.state.page = 0;
        this.state.transactions = [];
        this.state.hasMore = true;
        this.state.isLoadingMore = false;
    },
    
    setFilter(type) {
        if (this.state.filterType === type) return;
        this.state.filterType = type;
        this.resetListState();
        
        // Update UI Tabs
        const tabs = ui.content.querySelectorAll('.filter-tab');
        tabs.forEach(t => {
            t.classList.toggle('active', t.dataset.type === (type || 'all'));
        });
        
        // Show loading in list area only
        const listContainer = ui.content.querySelector('.transaction-list');
        if(listContainer) listContainer.innerHTML = `<div class="loading" style="padding: 20px;">${t('fin_loading')}</div>`;
        
        this.loadTransactions(false, true); // initial=false but force render list
    },

    async loadTransactions(initialFullLoad = false, forceRender = false) {
        if (this.state.isLoadingMore && !initialFullLoad && !forceRender) return;
        this.state.isLoadingMore = true;
        
        const skip = this.state.page * this.state.limit;
        
        try {
            if (!initialFullLoad && !forceRender) {
                const btn = document.getElementById('btn-load-more-fin');
                if (btn) btn.textContent = t('loading_wait');
            }

            const newTransactions = await API.getTransactions(this.state.limit, skip, this.state.filterType);
            
            if (initialFullLoad || forceRender) {
                this.state.transactions = newTransactions;
            } else {
                this.state.transactions = [...this.state.transactions, ...newTransactions];
            }
            
            this.state.hasMore = newTransactions.length === this.state.limit;
            this.state.page++;
            
            if (initialFullLoad) {
                this.renderFull();
            } else {
                this.renderListOnly();
            }

        } catch (error) {
            console.error(error);
            if(initialFullLoad) ui.content.innerHTML = `<div class="error">Failed: ${error.message}</div>`;
        } finally {
            this.state.isLoadingMore = false;
        }
    },

    renderFull() {
        const summary = this.state.summary;
        
        ui.content.innerHTML = `
            <div class="financial-dashboard">
                <!-- Stats Cards -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                    <div class="card" style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2);">
                        <div style="font-size: 11px; opacity: 0.7; color: #10b981;">${t('fin_inc_30')}</div>
                        <div style="font-size: 18px; font-weight: 800; color: #10b981;">${summary.total_income.toLocaleString()}</div>
                    </div>
                    <div class="card" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2);">
                        <div style="font-size: 11px; opacity: 0.7; color: #ef4444;">${t('fin_exp_30')}</div>
                        <div style="font-size: 18px; font-weight: 800; color: #ef4444;">${summary.total_expense.toLocaleString()}</div>
                    </div>
                </div>
                
                <div class="card" style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); margin-bottom: 24px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 11px; opacity: 0.7; color: #3b82f6;">${t('fin_net_30')}</div>
                            <div style="font-size: 24px; font-weight: 800; color: #3b82f6;">${summary.net_profit.toLocaleString()}</div>
                        </div>
                        <div style="text-align: right;">
                             <button id="btn-add-transaction" class="btn-primary" style="background: #3b82f6; width: auto; padding: 8px 16px; font-size: 13px;">
                                ${t('fin_new')}
                             </button>
                        </div>
                    </div>
                </div>

                <!-- Recent Transactions Header & Filters -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h3 style="font-size: 14px; opacity: 0.7; margin: 0;">${t('fin_recent')}</h3>
                    
                    <div class="filter-pills" style="display: flex; gap: 8px;">
                        <button class="filter-tab active" data-type="all" style="padding: 4px 12px; border-radius: 12px; font-size: 12px; border: 1px solid rgba(255,255,255,0.1); background: transparent; color: #888;">All</button>
                        <button class="filter-tab" data-type="income" style="padding: 4px 12px; border-radius: 12px; font-size: 12px; border: 1px solid rgba(16, 185, 129, 0.2); background: transparent; color: #10b981;">Inc</button>
                        <button class="filter-tab" data-type="expense" style="padding: 4px 12px; border-radius: 12px; font-size: 12px; border: 1px solid rgba(239, 68, 68, 0.2); background: transparent; color: #ef4444;">Exp</button>
                    </div>
                </div>

                <div class="transaction-list">
                    <!-- List Content -->
                </div>
                
                <div id="fin-load-more-container" style="padding: 20px; text-align: center; display: none;">
                    <button id="btn-load-more-fin" class="btn-secondary" style="width: 100%; padding: 12px;">${t('btn_load_more')}</button>
                </div>
            </div>
        `;

        this.renderListOnly();
        this.bindEvents();
    },
    
    renderListOnly() {
        const listDiv = ui.content.querySelector('.transaction-list');
        const loadMoreDiv = ui.content.querySelector('#fin-load-more-container');
        
        if (!listDiv) return;
        
        if (this.state.transactions.length === 0) {
            listDiv.innerHTML = `<div class="empty-state">${t('fin_none')}</div>`;
            if(loadMoreDiv) loadMoreDiv.style.display = 'none';
            return;
        }
        
        listDiv.innerHTML = this.state.transactions.map(t_item => this.renderTransactionItem(t_item)).join('');
        
        if (loadMoreDiv) {
            loadMoreDiv.style.display = this.state.hasMore ? 'block' : 'none';
        }
        
        // Re-bind delete buttons
        listDiv.querySelectorAll('.btn-delete-trans').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                if(confirm(t('fin_del_confirm'))) {
                    this.deleteTransaction(btn.dataset.id);
                }
            });
        });
    },
    
    bindEvents() {
        ui.content.querySelector('#btn-add-transaction').addEventListener('click', () => {
            this.openAddModal();
        });
        
        // Filter Tabs
        ui.content.querySelectorAll('.filter-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                const type = btn.dataset.type === 'all' ? null : btn.dataset.type;
                this.setFilter(type);
            });
        });
        
        // Load More
        const loadMoreBtn = ui.content.querySelector('#btn-load-more-fin');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => {
                this.loadTransactions(false);
            });
        }
    },

    renderTransactionItem(t_item) {
        const isIncome = t_item.type === 'income';
        const color = isIncome ? '#10b981' : '#ef4444';
        const sign = isIncome ? '+' : '-';
        const bg = isIncome ? 'rgba(16, 185, 129, 0.05)' : 'rgba(239, 68, 68, 0.05)';
        const border = isIncome ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
        
        return `
            <div class="card" style="margin-bottom: 8px; position: relative; background: ${bg}; border: 1px solid ${border};">
                <div class="card-header" style="flex-direction: column; align-items: stretch; gap: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <h2 class="card-title" style="margin: 0; font-size: 15px; display: flex; align-items: center; gap: 8px;">
                            <span style="width: 6px; height: 6px; background: ${t_item.category_color || color}; border-radius: 50%;"></span>
                            ${t_item.category_name}
                        </h2>
                        <button class="btn-delete-trans" data-id="${t_item.id}" style="
                            background: none; border: none; color: #666; font-size: 14px; padding: 0 4px; line-height: 1;">✕</button>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 2px;">
                        <span style="font-size: 12px; color: var(--text-sub); opacity: 0.8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 70%;">
                            ${t_item.description || t('fin_desc')}
                        </span>
                        <span style="font-size: 11px; opacity: 0.5;">${t_item.date}</span>
                    </div>
                </div>
                
                <div class="card-footer" style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.05); justify-content: space-between; align-items: center; display: flex;">
                    <span class="status-badge" style="background: rgba(255,255,255,0.05); color: #aaa; border: 1px solid rgba(255,255,255,0.1); font-size: 10px; padding: 2px 6px;">
                         ${t('inv_' + t_item.payment_method) || t_item.payment_method.replace('_', ' ').toUpperCase()}
                    </span>
                    <span style="font-size: 15px; font-weight: 700; color: ${color};">
                        ${sign}${t_item.amount.toLocaleString()}
                    </span>
                </div>
            </div>
        `;
    },

    async openAddModal() {
        // Base Modal HTML
        const modalHtml = `
        <div id="financial-modal" class="modal-overlay" style="display: flex; align-items: flex-end;">
            <div class="modal-content" style="border-radius: 20px 20px 0 0; padding: 24px; display: flex; flex-direction: column; background: #1a1a1a; width: 100%; max-height: 90vh; overflow-y: auto;">
                <div class="modal-header" style="margin-bottom: 20px;">
                    <h3 style="font-size: 18px; color: white;">${t('fin_add_trans')}</h3>
                    <button class="btn-close-modal" style="background: none; border: none; font-size: 20px; color: #666;">✕</button>
                </div>
                
                <div class="modal-body">
                    <!-- Type Toggle -->
                    <div style="display: flex; background: rgba(255,255,255,0.05); padding: 4px; border-radius: 8px; margin-bottom: 16px;">
                        <button class="type-btn active" data-type="expense" style="flex: 1; padding: 8px; border: none; background: #ef4444; color: white; border-radius: 6px;">${t('fin_expense')}</button>
                        <button class="type-btn" data-type="income" style="flex: 1; padding: 8px; border: none; background: transparent; color: #888; border-radius: 6px;">${t('fin_income')}</button>
                    </div>

                    <div class="input-group" style="margin-bottom: 12px;">
                        <label>${t('inv_amount')}</label>
                        <input type="number" id="fin-amount" placeholder="0.00" style="background: rgba(255,255,255,0.05); border: 1px solid #333; color: white; padding: 12px; border-radius: 8px; width: 100%; font-size: 20px; font-weight: bold;">
                    </div>

                    <div class="input-group" style="margin-bottom: 12px;">
                        <label>${t('fin_cat')}</label>
                        <select id="fin-category" style="background: rgba(255,255,255,0.05); border: 1px solid #333; color: white; padding: 12px; border-radius: 8px; width: 100%;">
                            <option value="">${t('fin_sel_cat')}</option>
                        </select>
                    </div>

                    <div class="input-group" style="margin-bottom: 12px;">
                        <label>${t('fin_desc')}</label>
                        <input type="text" id="fin-desc" placeholder="${t('fin_det_ph')}" style="background: rgba(255,255,255,0.05); border: 1px solid #333; color: white; padding: 12px; border-radius: 8px; width: 100%;">
                    </div>
                    
                    <div class="input-group" style="margin-bottom: 12px;">
                        <label>${t('fin_date')}</label>
                        <input type="date" id="fin-date" value="${new Date().toISOString().split('T')[0]}" style="background: rgba(255,255,255,0.05); border: 1px solid #333; color: white; padding: 12px; border-radius: 8px; width: 100%;">
                    </div>

                    <div class="input-group" style="margin-bottom: 20px;">
                        <label>${t('inv_pay_method')}</label>
                        <select id="fin-method" style="background: rgba(255,255,255,0.05); border: 1px solid #333; color: white; padding: 12px; border-radius: 8px; width: 100%;">
                            <option value="cash">${t('inv_cash')}</option>
                            <option value="bank_transfer">${t('inv_bank')}</option>
                            <option value="card">${t('inv_card')}</option>
                        </select>
                    </div>
                </div>

                <button id="btn-save-trans" class="btn-primary" style="width: 100%; background: #ef4444; padding: 16px; font-size: 16px; font-weight: bold;">
                    ${t('fin_save_exp')}
                </button>
            </div>
        </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // State for Modal
        let activeType = 'expense';
        
        // Load Categories
        const loadCats = async (type) => {
            const select = document.getElementById('fin-category');
            select.innerHTML = '<option>Loading...</option>';
            try {
                const cats = await API.getExpenseCategories(type);
                select.innerHTML = cats.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
            } catch (e) {
                select.innerHTML = '<option>Error loading categories</option>';
            }
        };
        loadCats('expense');

        // Bind Modal Events
        const modal = document.getElementById('financial-modal');
        const closeBtn = modal.querySelector('.btn-close-modal');
        const saveBtn = document.getElementById('btn-save-trans');
        const typeBtns = modal.querySelectorAll('.type-btn');

        closeBtn.addEventListener('click', () => modal.remove());

        // Type Toggle Logic
        typeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const type = e.target.dataset.type;
                activeType = type;
                
                // Update UI
                typeBtns.forEach(b => {
                    b.classList.remove('active');
                    b.style.background = 'transparent';
                    b.style.color = '#888';
                });
                e.target.classList.add('active');
                
                if (type === 'expense') {
                    e.target.style.background = '#ef4444';
                    e.target.style.color = 'white';
                    saveBtn.style.background = '#ef4444';
                    saveBtn.textContent = t('fin_save_exp');
                } else {
                    e.target.style.background = '#10b981';
                    e.target.style.color = 'white';
                    saveBtn.style.background = '#10b981';
                    saveBtn.textContent = t('fin_save_inc');
                }
                
                loadCats(type);
            });
        });

        // Save Logic
        saveBtn.addEventListener('click', async () => {
             const amount = parseFloat(document.getElementById('fin-amount').value);
             const categoryId = document.getElementById('fin-category').value;
             const desc = document.getElementById('fin-desc').value;
             const date = document.getElementById('fin-date').value;
             const method = document.getElementById('fin-method').value;

             if (!amount || !categoryId) {
                 alert('Please enter amount and category');
                 return;
             }
             
             try {
                 saveBtn.disabled = true;
                 saveBtn.textContent = 'Saving...';
                 
                 await API.addTransaction({
                     amount: amount,
                     type: activeType,
                     category_id: categoryId,
                     description: desc,
                     date: date,
                     payment_method: method
                 });
                 
                 modal.remove();
                 this.load(); // Refresh dashboard
             } catch (err) {
                 alert('Error: ' + err.message);
                 saveBtn.disabled = false;
                 saveBtn.textContent = 'Retry';
             }
        });
    },

    async deleteTransaction(id) {
        try {
            await API.deleteTransaction(id);
            this.load(); // Reloads both summary and list, resetting state. Safest to ensure summary math is right.
        } catch (err) {
            alert("Failed to delete: " + err.message);
        }
    }
};
