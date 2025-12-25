import { state, ui } from '../state.js?v=5.8';
import { API } from '../api.js?v=5.8';
import { t } from '../i18n.js?v=5.8';

export const Invoice = {
    // State
    state: {
        invoices: [],
        page: 0,
        limit: 20,
        hasMore: true,
        isLoadingMore: false
    },

    async load(detailId = null) {
        if (detailId) {
            await this.loadDetail(detailId);
        } else {
            // Reset state on initial full load
            this.state.page = 0;
            this.state.invoices = [];
            this.state.hasMore = true;
            await this.loadList(true);
        }
    },

    async loadList(initial = false) {
        ui.screenTitle.textContent = t('inv_title');
        
        if (initial) {
             ui.content.innerHTML = `<div class="loading">${t('inv_loading')}</div>`;
        } else {
             const btn = document.getElementById('btn-load-more-inv');
             if (btn) btn.textContent = t('loading_wait');
        }
        
        if (this.state.isLoadingMore && !initial) return;
        this.state.isLoadingMore = true;
        
        const skip = this.state.page * this.state.limit;
        
        try {
            const newInvoices = await API.getInvoices(this.state.limit, skip);
            
            if (initial) {
                this.state.invoices = newInvoices;
            } else {
                this.state.invoices = [...this.state.invoices, ...newInvoices];
            }
            
            this.state.hasMore = newInvoices.length === this.state.limit;
            this.state.page++;
            
            this.renderList();
        } catch (error) {
            ui.content.innerHTML = `<div class="error">Failed: ${error.message}</div>`;
        } finally {
            this.state.isLoadingMore = false;
        }
    },

    renderList() {
        const invoices = this.state.invoices;
        
        if (!invoices || invoices.length === 0) {
            ui.content.innerHTML = `<div class="empty-state">${t('inv_none')}</div>`;
            return;
        }

        let html = invoices.map(inv => {
            const statusClass = inv.status === 'paid' ? 'status-completed' : 
                               (inv.status === 'partially_paid' ? 'status-pending' : 'status-cancelled');
            
            // Adjust status badge color for unpaid if needed
            let statusStyle = '';
            if (inv.status === 'unpaid') statusStyle = 'background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid rgba(239,68,68,0.3);';
            else if (inv.status === 'partially_paid') statusStyle = 'background: rgba(245,158,11,0.2); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3);';

            return `
            <div class="card invoice-item" data-id="${inv.id}">
                <div class="card-header" style="flex-direction: column; align-items: stretch; gap: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h2 class="card-title" style="margin: 0; font-size: 16px;">${inv.customer}</h2>
                        <span class="status-badge" style="${statusStyle || ''}">${inv.status.toUpperCase().replace('_', ' ')}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 2px;">
                        <span class="card-id" style="font-size: 13px; color: var(--text-sub); opacity: 0.8;">${inv.number}</span>
                        <span style="font-size: 11px; opacity: 0.5;">${inv.date}</span>
                    </div>
                </div>
                
                <div class="card-footer" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); justify-content: space-between; align-items: center;">
                    <span style="font-size: 12px; font-weight: 700; color: ${inv.balance > 0 ? '#ef4444' : '#10b981'};">
                         ${inv.balance > 0 ? `${t('inv_due')}: ${inv.balance.toLocaleString()}` : t('inv_paid')}
                    </span>
                    <span style="font-size: 16px; font-weight: 800; color: var(--accent-color);">
                        ${inv.total.toLocaleString()} <span style="font-size: 11px; font-weight: 400; opacity: 0.7;">Ks</span>
                    </span>
                </div>
            </div>
            `;
        }).join('');
        
        // Add Load More
        if (this.state.hasMore) {
             html += `
                <div style="padding: 20px; text-align: center;">
                    <button id="btn-load-more-inv" class="btn-secondary" style="width: 100%; padding: 12px;">${t('btn_load_more')}</button>
                </div>
            `;
        }
        
        ui.content.innerHTML = html;
        
        ui.content.querySelectorAll('.invoice-item').forEach(card => {
            card.addEventListener('click', () => {
                this.loadDetail(card.dataset.id);
            });
        });
        
        if (this.state.hasMore) {
            const btn = ui.content.querySelector('#btn-load-more-inv');
            if (btn) {
                btn.addEventListener('click', () => {
                    this.loadList(false);
                });
            }
        }
    },

    async loadDetail(id) {
        ui.screenTitle.textContent = t('inv_detail');
        ui.content.innerHTML = '<div class="loading">Loading details...</div>';
        
        try {
            const inv = await API.getInvoiceDetail(id);
            this.renderDetail(inv);
        } catch (error) {
            ui.content.innerHTML = `<div class="error">Failed: ${error.message}</div>`;
        }
    },

    renderDetail(inv) {
        ui.content.innerHTML = `
            <div class="ticket-detail">
                <div class="card">
                    <div class="card-header">
                        <span class="card-id"># ${inv.number}</span>
                        <span class="status-badge ${inv.status === 'paid' ? 'status-completed' : 'status-pending'}">
                            ${inv.status.toUpperCase()}
                        </span>
                    </div>
                    <div class="card-title" style="margin-top: 8px;">${inv.customer.name}</div>
                    
                    <div class="divider"></div>
                    
                    <div class="detail-row">
                        <span>${t('inv_date')}</span>
                        <span>${new Date(inv.created_at).toLocaleDateString()}</span>
                    </div>
                    ${inv.device ? `
                    <div class="detail-row">
                        <span>${t('inv_device')}</span>
                        <span>${inv.device}</span>
                    </div>
                    ` : ''}

                    <div style="margin-top: 24px; margin-bottom: 8px; font-size: 12px; font-weight: 700; opacity: 0.7; text-transform: uppercase;">
                        ${t('inv_items')}
                    </div>
                    
                    <div style="background: rgba(255,255,255,0.03); border-radius: 8px; padding: 4px;">
                        ${inv.items.map(item => `
                            <div style="display: flex; justify-content: space-between; padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.05);">
                                <div>
                                    <div style="font-weight: 600;">${item.description}</div>
                                    <div style="font-size: 11px; opacity: 0.5;">x${item.quantity} ${item.sku ? `(${item.sku})` : ''}</div>
                                </div>
                                <div style="font-weight: 600;">${item.total.toLocaleString()}</div>
                            </div>
                        `).join('')}
                    </div>

                    <div style="margin-top: 16px; padding-top: 16px; border-top: 1px dashed var(--border-color);">
                        <div class="detail-row">
                            <span style="opacity: 0.7;">${t('inv_subtotal')}</span>
                            <span>${inv.subtotal.toLocaleString()}</span>
                        </div>
                        <div class="detail-row">
                            <span style="opacity: 0.7;">${t('inv_tax')}</span>
                            <span>${inv.tax.toLocaleString()}</span>
                        </div>
                        ${inv.discount > 0 ? `
                        <div class="detail-row" style="color: #10b981;">
                            <span>${t('inv_discount')}</span>
                            <span>-${inv.discount.toLocaleString()}</span>
                        </div>
                        ` : ''}
                        <div class="detail-row" style="margin-top: 12px; font-size: 18px; font-weight: 800; color: var(--accent-color);">
                            <span>${t('inv_total')}</span>
                            <span>${inv.total.toLocaleString()} Ks</span>
                        </div>

                        <!-- Payments Section -->
                        <div style="margin-top: 24px; margin-bottom: 8px; font-size: 12px; font-weight: 700; opacity: 0.7; text-transform: uppercase;">
                            ${t('inv_pay_hist')}
                        </div>
                        <div style="background: rgba(255,255,255,0.03); border-radius: 8px; padding: 4px;">
                            ${inv.payments && inv.payments.length > 0 ? inv.payments.map(p => `
                                <div style="display: flex; justify-content: space-between; padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.05);">
                                    <div>
                                        <div style="font-weight: 600; text-transform: capitalize;">${t('inv_' + p.method) || p.method.replace('_', ' ')}</div>
                                        <div style="font-size: 11px; opacity: 0.5;">${p.date}</div>
                                    </div>
                                    <div style="font-weight: 600; color: #10b981;">-${p.amount.toLocaleString()}</div>
                                </div>
                            `).join('') : `<div style="padding: 12px; opacity: 0.5; font-size: 13px;">${t('inv_no_pay')}</div>`}
                        </div>

                        <!-- Balance Due -->
                        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px dashed var(--border-color);">
                             <div class="detail-row">
                                <span>${t('inv_paid')}</span>
                                <span style="color: #10b981;">${inv.payments.reduce((acc, p) => acc + p.amount, 0).toLocaleString()} Ks</span>
                            </div>
                            <div class="detail-row" style="font-size: 18px; font-weight: 800; color: ${(inv.total - inv.payments.reduce((acc, p) => acc + p.amount, 0)) > 0 ? '#ef4444' : '#10b981'}; margin-top: 8px;">
                                <span>${t('inv_due')}</span>
                                <span>${Math.max(0, inv.total - inv.payments.reduce((acc, p) => acc + p.amount, 0)).toLocaleString()} Ks</span>
                            </div>
                        </div>

                        ${(inv.total - inv.payments.reduce((acc, p) => acc + p.amount, 0)) > 0 ? `
                        <button id="btn-add-payment" class="btn-primary" data-balance="${Math.max(0, inv.total - inv.payments.reduce((acc, p) => acc + p.amount, 0))}" style="background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; margin-top: 16px; width: 100%;">
                            ${t('inv_add_pay')}
                        </button>
                        ` : ''}

                    </div>
                </div>


                <div style="display: flex; gap: 12px; margin-top: 24px;">
                    <button class="btn-primary back-btn" style="flex: 1; background: #374151;">${t('btn_close')}</button>
                    <button id="btn-print-invoice" class="btn-primary" style="flex: 1; background: #2563EB; display: flex; align-items: center; justify-content: center; gap: 8px;">
                        <span>🖨️</span> ${t('inv_print')}
                    </button>
                </div>
            </div>
        `;

        // Bind Events
        const printBtn = ui.content.querySelector('#btn-print-invoice');
        if (printBtn) {
            printBtn.addEventListener('click', async () => {
                if (confirm('Print this invoice to the shop printer?')) {
                    try {
                        printBtn.disabled = true;
                        printBtn.innerHTML = 'Printing...';
                        await API.printInvoice(inv.id);
                        alert('Print job sent successfully!');
                        printBtn.innerHTML = `<span>🖨️</span> ${t('inv_print')}`;
                        printBtn.disabled = false;
                    } catch (error) {
                        alert('Print failed: ' + error.message);
                        printBtn.innerHTML = '<span>⚠️</span> Retry';
                        printBtn.disabled = false;
                    }
                }
            });
        }



        // Bind Events
        ui.content.querySelector('.back-btn').addEventListener('click', () => {
            if (this.fromTicket) {
                document.dispatchEvent(new CustomEvent('viewTicket', { detail: { id: this.fromTicket } }));
                this.fromTicket = null;
            } else {
                // If returning to list, we just re-render what we have, or maybe do nothing as content is replaced?
                // Actually loadDetail replaces content, so we need to restore list.
                // We can just call renderList() to show existing state without refetching!
               ui.screenTitle.textContent = t('inv_title');
               this.renderList();
            }
        });

        const payBtn = ui.content.querySelector('#btn-add-payment');
        if (payBtn) {
            payBtn.addEventListener('click', () => {
                const balanceDue = parseFloat(payBtn.dataset.balance);
                this.openPaymentModal(inv.id, balanceDue);
            });
        }
    },

    openPaymentModal(invoiceId, balanceDue) {
        const modalHtml = `
        <div id="payment-modal" class="modal-overlay" style="display: flex; align-items: flex-end;">
            <div class="modal-content" style="border-radius: 20px 20px 0 0; padding: 24px; display: flex; flex-direction: column; background: #1a1a1a; width: 100%;">
                <div class="modal-header" style="margin-bottom: 20px;">
                    <h3 style="font-size: 18px; color: white;">${t('inv_add_pay')}</h3>
                    <button class="btn-close-modal" style="background: none; border: none; font-size: 20px; color: #666;">✕</button>
                </div>
                
                <div class="modal-body">
                    <div class="detail-row" style="margin-bottom: 16px;">
                        <span style="color: #999;">${t('inv_due')}</span>
                        <span style="color: #ef4444; font-weight: bold;">${balanceDue.toLocaleString()} Ks</span>
                    </div>

                    <div class="input-group" style="margin-bottom: 12px;">
                        <label>${t('inv_pay_method')}</label>
                        <select id="pay-method" style="background: rgba(255,255,255,0.05); border: 1px solid #333; color: white; padding: 12px; border-radius: 8px; width: 100%;">
                            <option value="cash">${t('inv_cash')}</option>
                            <option value="bank_transfer">${t('inv_bank')}</option>
                            <option value="card">${t('inv_card')}</option>
                        </select>
                    </div>

                    <div class="input-group" style="margin-bottom: 20px;">
                        <label>${t('inv_amount')}</label>
                        <input type="number" id="pay-amount" value="${balanceDue}" style="background: rgba(255,255,255,0.05); border: 1px solid #333; color: white; padding: 12px; border-radius: 8px; width: 100%; font-size: 18px;" inputmode="decimal" step="any">
                    </div>
                </div>

                <button id="btn-submit-payment" class="btn-primary" style="width: 100%; background: #10b981; padding: 16px; font-size: 16px; font-weight: bold;">
                    ${t('inv_receive')}
                </button>
            </div>
        </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        const closeBtn = document.querySelector('#payment-modal .btn-close-modal');
        const submitBtn = document.getElementById('btn-submit-payment');

        closeBtn.addEventListener('click', () => document.getElementById('payment-modal').remove());

        submitBtn.addEventListener('click', async () => {
            const amount = parseFloat(document.getElementById('pay-amount').value);
            const method = document.getElementById('pay-method').value;

            if (!amount || amount <= 0) {
                alert('Please enter a valid amount');
                return;
            }

            try {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Processing...';
                
                await API.addPayment(invoiceId, {
                    amount: amount,
                    method: method,
                    notes: "Mobile Payment Addon"
                });

                document.getElementById('payment-modal').remove();
                this.loadDetail(invoiceId); // Reload to show update
            } catch (err) {
                alert('Error: ' + err.message);
                submitBtn.disabled = false;
                submitBtn.textContent = t('inv_receive');
            }
        });
    }
};
