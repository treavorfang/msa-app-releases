import { state, ui } from '../state.js?v=5.8';
import { API } from '../api.js?v=5.8';
import { TicketForm } from './ticket-form.js?v=5.8';
import { Invoice } from './invoice.js?v=5.8';
import { t } from '../i18n.js?v=5.8';

export const TicketDetail = {
    async load(id) {
        const isStaff = state.user.role === 'staff';
        ui.screenTitle.textContent = isStaff ? t('detail_manage') : t('detail_job');
        ui.content.innerHTML = `<div class="loading">${t('loading_detail')}</div>`;

        try {
            console.log('Loading ticket detail for ID:', id);
            const [ticket, technicians, parts, history] = await Promise.all([
                API.getTicketDetail(id),
                isStaff ? API.getTechnicians() : Promise.resolve([]),
                API.getTicketParts(id),
                API.getTicketHistory(id)
            ]);
            console.log('Ticket data loaded:', ticket);
            console.log('History loaded:', history);
            
            state.activeTicket = ticket;
            state.activeParts = parts;
            state.activeHistory = history;
            const techList = technicians;
            const isReadOnly = ticket.device_status === 'returned';

            ui.content.innerHTML = `
                <div class="ticket-detail">
                    <div class="card">
                        <div class="card-header">
                            <span class="card-id">${ticket.number || ticket.id}</span>
                            <span class="status-badge status-${(ticket.status || 'unknown').toLowerCase().replace(/\s/g, '_')}">${t('status_' + (ticket.status || 'unknown')) || ticket.status}</span>
                        </div>
                        <div class="card-title">${ticket.device.brand} ${ticket.device.model}</div>
                        <p class="error-text" style="font-size: 14px; color: var(--text-main); font-weight: 500;">${ticket.error}</p>
                        <div class="divider"></div>
                        <div class="detail-row">
                            <span>${t('detail_customer')}</span>
                            <span>${ticket.customer}</span>
                        </div>
                        <div class="detail-row">
                            <span>${t('detail_assigned')}</span>
                            <span style="color: var(--accent-color); font-weight: 700;">${ticket.assigned_technician_name || t('detail_unassigned')}</span>
                        </div>
                        <div class="detail-row" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border-color);">
                            <span>${t('detail_parts_total')}</span>
                            <span style="font-weight: 800; color: var(--accent-color);">${(ticket.total_parts_cost || 0).toLocaleString()} Ks</span>
                        </div>
                        <div class="detail-row">
                            <span>${t('detail_custody')}</span>
                            <span class="status-badge status-${ticket.device_status}" id="badge-custody">
                                ${ticket.device_status === 'returned' ? t('status_returned') : ticket.device_status.toUpperCase()}
                            </span>
                        </div>
                        ${ticket.device_status === 'returned' ? `
                            <div style="margin-top: 12px; padding: 10px; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 8px; font-size: 11px; color: #3b82f6;">
                                ℹ️ ${t('detail_returned_msg')}
                            </div>
                        ` : ''}
                    </div>
                    
                    <!-- Technician Tools -->
                    ${!isReadOnly ? `
                        <div class="card">
                            <h3 style="margin-bottom: 12px; font-size: 12px; color: var(--text-sub); text-transform: uppercase;">${t('tool_title') || 'Technician Tools'}</h3>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                                <!-- Diagnostics -->
                                <button class="btn-secondary" id="btn-diag-open" style="padding: 16px; display: flex; flex-direction: column; align-items: center; gap: 8px;">
                                    <span style="font-size: 24px;">🩺</span>
                                    <span style="font-size: 12px;">${t('tool_diag') || 'Diagnostics'}</span>
                                </button>
                                
                                <!-- Device Lock -->
                                <button class="btn-secondary" id="btn-patt-open" style="padding: 16px; display: flex; flex-direction: column; align-items: center; gap: 8px;">
                                    <span style="font-size: 24px;">🔐</span>
                                    <span style="font-size: 12px;">${t('tool_lock') || 'Device Lock'}</span>
                                </button>
                            </div>
                        </div>
                    ` : ''}

                    <div class="card">
                        <div class="card-header">
                            <h3>${t('detail_parts_title')}</h3>
                            ${!isReadOnly ? `<button class="btn-add-part" id="btn-add-part-trigger">${t('detail_add')}</button>` : ''}
                        </div>
                        <div id="parts-list-container" style="margin-top: 8px;">
                            ${this.renderPartsHtml(parts, isReadOnly)}
                        </div>
                    </div>

                    <div class="actions">
                        ${isStaff ? `
                            <div class="input-group" style="margin-bottom: 24px;">
                                <label style="font-size: 10px; font-weight: 800; color: var(--text-sub); text-transform: uppercase;">${t('detail_assign_label')}</label>
                                <select id="assign-tech" ${isReadOnly ? 'disabled' : ''} style="width: 100%; background: ${isReadOnly ? 'rgba(255,255,255,0.01)' : 'rgba(255,255,255,0.03)'}; border: 1px solid var(--border-color); border-radius: 12px; padding: 14px; color: ${isReadOnly ? 'rgba(255,255,255,0.3)' : 'white'};">
                                    <option value="">${t('detail_select_tech')}</option>
                                    ${techList.map(t => `
                                        <option value="${t.id}" ${ticket.assigned_technician_id === t.id ? 'selected' : ''}>${t.name}</option>
                                    `).join('')}
                                </select>
                            </div>

                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 24px;">
                                <div class="input-group">
                                    <label>${t('detail_est_cost')}</label>
                                    <input type="number" id="edit-est-cost" value="${ticket.estimated_cost || 0}" ${isReadOnly ? 'readonly' : ''}>
                                </div>
                                <div class="input-group">
                                    <label>${t('detail_act_cost')}</label>
                                    <input type="number" id="edit-act-cost" value="${ticket.actual_cost || 0}" ${isReadOnly ? 'readonly' : ''}>
                                </div>
                            </div>
                        ` : ''}

                        ${ticket.invoice_id ? `
                            <div style="margin-bottom: 20px;">
                                <button class="btn-secondary" id="btn-view-invoice" data-id="${ticket.invoice_id}" style="width: 100%; border: 1px dashed var(--border-color); padding: 12px; display: flex; align-items: center; justify-content: center; gap: 8px;">
                                    <span>📄</span> ${t('detail_view_inv')}
                                </button>
                            </div>
                        ` : (ticket.status === 'completed' || ticket.status === 'unrepairable' ? `
                            <div style="margin-bottom: 20px;">
                                <button class="btn-primary" id="btn-create-invoice" style="width: 100%; background: #10b981; color: white; padding: 12px; display: flex; align-items: center; justify-content: center; gap: 8px;">
                                    <span>💰</span> ${t('detail_create_inv')}
                                </button>
                            </div>
                        ` : '')}

                        <h3 style="font-size: 12px; margin-bottom: 12px; opacity: 0.7;">${t('detail_update')}</h3>
                        <div class="status-grid">
                            ${['in_progress', 'awaiting_parts', 'completed', 'unrepairable'].map(s => `
                                <button class="btn-status ${ticket.status === s ? 'active' : ''}" data-status="${s}" ${isReadOnly ? 'disabled' : ''} style="${isReadOnly ? 'opacity: 0.4; cursor: not-allowed;' : ''}">
                                    ${t('status_' + s) || s.replace(/_/g, ' ')}
                                </button>
                            `).join('')}
                        </div>
                        
                        <textarea id="work-notes" placeholder="${isReadOnly ? t('detail_readonly_notes') : t('detail_notes_ph')}" ${isReadOnly ? 'readonly' : ''}></textarea>
                        
                        <div class="photo-section">
                            <h3 style="font-size: 12px; margin-bottom: 12px; opacity: 0.7;">${t('detail_gallery')}</h3>
                            <div class="photo-gallery">
                                ${this.renderPhotosHtml(ticket.photos)}
                            </div>
                            
                            ${!isReadOnly ? `
                                <div class="photo-upload-box" id="photo-trigger">
                                    <span>📷 ${t('detail_photo_append')}</span>
                                    <input type="file" id="photo-input" accept="image/*" capture="environment" hidden>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <div style="display: flex; gap: 12px; margin-top: 24px;">
                        <button class="btn-primary back-btn" style="flex: 1; background: #374151; color: white;">${t('btn_close')}</button>
                    </div>

                    <div class="card" style="margin-top: 24px;">
                        <div class="card-header">
                            <h3>${t('detail_timeline')}</h3>
                        </div>
                        <div class="timeline">
                            ${this.renderTimelineHtml(history)}
                        </div>
                    </div>

                    <!-- Part Search Modal -->
                    <div id="part-search-modal" class="modal-overlay" style="display: none;">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h3>${t('modal_lookup_title')}</h3>
                                <button class="btn-close-modal">✕</button>
                            </div>
                            <div class="modal-body">
                                <div class="search-container">
                                    <input type="text" id="part-search-q" placeholder="${t('ph_search_part')}">
                                </div>
                                <div id="part-search-results" class="search-results-list"></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            this.setupEventListeners();

        } catch (error) {
            ui.content.innerHTML = `<div class="error">Failed to load: ${error.message}</div>`;
        }
    },

    setupEventListeners() {
        // Status buttons
        // Status buttons
        ui.content.querySelectorAll('.btn-status').forEach(btn => {
            btn.addEventListener('click', () => {
                const newStatus = btn.dataset.status;
                if (newStatus === state.activeTicket.status) return;
                
                // If completing, maybe ask for notes? For now, direct update.
                // Actually, let's ask for confirmation/notes for all major changes to be safe.
                this.promptStatusChange(newStatus);
            });
        });

        // View Invoice
        const viewInvoiceBtn = ui.content.querySelector('#btn-view-invoice');
        if (viewInvoiceBtn) {
            viewInvoiceBtn.addEventListener('click', () => {
                Invoice.fromTicket = state.activeTicket.id; // Store return path
                Invoice.load(viewInvoiceBtn.dataset.id);
            });
        }

        // Create Invoice
        const createInvoiceBtn = ui.content.querySelector('#btn-create-invoice');
        if (createInvoiceBtn) {
            createInvoiceBtn.addEventListener('click', () => {
                this.openCheckoutModal();
            });
        }

        // Photo upload
        const photoTrigger = ui.content.querySelector('#photo-trigger');
        const photoInput = ui.content.querySelector('#photo-input');
        
        if (photoTrigger && photoInput) {
            photoTrigger.addEventListener('click', () => photoInput.click());
            photoInput.addEventListener('change', (e) => this.handlePhotoUpload(e.target));
        }

        // Back button
        ui.content.querySelector('.back-btn').addEventListener('click', () => {
            document.dispatchEvent(new CustomEvent('loadDashboard'));
        });

        // Save button - REMOVED (Auto-save)
        // const saveBtn = ui.content.querySelector('#btn-save-all');
        // if (saveBtn) {
        //     saveBtn.addEventListener('click', () => this.handleSave());
        // }

        // Part Management Listeners
        const addPartTrigger = ui.content.querySelector('#btn-add-part-trigger');
        if (addPartTrigger) {
            addPartTrigger.addEventListener('click', () => this.openPartSearch());
        }

        const closeModalBtn = ui.content.querySelector('.btn-close-modal');
        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', () => this.closePartSearch());
        }

        const partSearchInput = ui.content.querySelector('#part-search-q');
        if (partSearchInput) {
            partSearchInput.addEventListener('input', this.debounce((e) => this.handlePartSearch(e.target.value), 300));
        }

        ui.content.querySelectorAll('.btn-remove-part').forEach(btn => {
            btn.addEventListener('click', () => this.handleRemovePart(btn.dataset.id));
        });
        
        const diagBtn = ui.content.querySelector('#btn-diag-open');
        if (diagBtn) {
            diagBtn.addEventListener('click', () => this.openDiagnosticsModal());
        }
        
         const pattBtn = ui.content.querySelector('#btn-patt-open');
        if (pattBtn) {
            pattBtn.addEventListener('click', () => this.openPatternModal());
        }
    },

    renderPartsHtml(parts, isReadOnly) {
        if (!parts || parts.length === 0) {
            return `<div class="empty-state" style="padding: 20px 0; font-size: 11px;">${t('empty_parts')}</div>`;
        }

        return parts.map(p => `
            <div class="part-item">
                <div class="part-item-info">
                    <div class="part-item-name">${p.name}</div>
                    <div class="part-item-meta">SKU: ${p.sku} | Qty: ${p.quantity}</div>
                    <div class="part-item-price">${p.total.toLocaleString()} Ks</div>
                </div>
                ${!isReadOnly ? `<button class="btn-remove-part" data-id="${p.id}">${t('btn_remove')}</button>` : ''}
            </div>
        `).join('');
    },

    renderPhotosHtml(photos) {
        if (!photos || photos.length === 0) {
            return `<span style="font-size: 11px; opacity: 0.5; padding: 10px;">${t('empty_photos')}</span>`;
        }
        return photos.map(p => `
            <div class="photo-item" onclick="window.open('${p.url}', '_blank')">
                <img src="${p.url}" loading="lazy">
                <div class="photo-type-badge">${p.type}</div>
            </div>
        `).join('');
    },

    openPartSearch() {
        ui.content.querySelector('#part-search-modal').style.display = 'flex';
        ui.content.querySelector('#part-search-q').focus();
    },

    closePartSearch() {
        ui.content.querySelector('#part-search-modal').style.display = 'none';
        ui.content.querySelector('#part-search-q').value = '';
        ui.content.querySelector('#part-search-results').innerHTML = '';
    },

    async handlePartSearch(query) {
        const resultsDiv = ui.content.querySelector('#part-search-results');
        if (!query) {
            resultsDiv.innerHTML = '';
            return;
        }

        try {
            const parts = await API.searchInventory(query);
            resultsDiv.innerHTML = parts.map(p => `
                <div class="part-item">
                    <div class="part-item-info">
                        <div class="part-item-name">${p.name}</div>
                        <div class="part-item-meta">SKU: ${p.sku} | Stock: ${p.stock}</div>
                        <div class="part-item-price">${p.price.toLocaleString()} Ks</div>
                    </div>
                    <button class="btn-add-part-inline" data-id="${p.id}">${t('btn_add')}</button>
                </div>
            `).join('');

            resultsDiv.querySelectorAll('.btn-add-part-inline').forEach(btn => {
                btn.addEventListener('click', () => this.handleAddPart(btn.dataset.id));
            });
        } catch (err) {
            resultsDiv.innerHTML = `<div class="error">${t('err_lookup_fail')}</div>`;
        }
    },

    async handleAddPart(partId) {
        try {
            await API.addTicketPart(state.activeTicket.id, { part_id: parseInt(partId), quantity: 1 });
            this.closePartSearch();
            this.load(state.activeTicket.id);
        } catch (err) {
            alert(t('alert_add_fail') + err.message);
        }
    },

    async handleRemovePart(itemId) {
        if (!confirm(t('confirm_remove_part'))) return;
        
        try {
            await API.removeTicketPart(state.activeTicket.id, itemId);
            this.load(state.activeTicket.id);
        } catch (err) {
            alert(t('alert_remove_fail') + err.message);
        }
    },

    debounce(func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), wait);
        };
    },

    renderTimelineHtml(history) {
        if (!history || !Array.isArray(history) || history.length === 0) {
            return `<div class="empty-state" style="padding: 20px 0; font-size: 11px;">${t('empty_history')}</div>`;
        }

        return history.map(ev => {
            if (!ev || !ev.timestamp) return '';
            
            const date = new Date(ev.timestamp);
            if (isNaN(date.getTime())) {
                 console.error('Invalid timestamp in history:', ev.timestamp);
                 return '';
            }
            const timeStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            let icon = '📝';
            let title = '';
            let typeClass = '';
            let content = '';
            let meta = '';

            const safeStatus = (s) => (s || 'unknown').replace(/_/g, ' ');
            const localStatus = (s) => t('status_' + (s || 'unknown').toLowerCase()) || safeStatus(s);
            
            if (ev.type === 'status_change') {
                icon = '🔄';
                title = t('timeline_status');
                typeClass = 'type-status';
                content = `${t('timeline_changed')} <b>${localStatus(ev.old)}</b> ${t('timeline_to')} <b>${localStatus(ev.new)}</b>`;
                if (ev.reason) content += `<br/><i style="font-size: 11px; opacity: 0.8;">${t('timeline_reason')}: ${ev.reason}</i>`;
                meta = `${t('timeline_updated_by')} ${ev.by || 'System'}`;
            } else if (ev.type === 'work_log') {
                icon = '👨‍🔧';
                title = t('timeline_work_log');
                typeClass = 'type-work';
                content = ev.work || t('timeline_tech_updates');
                meta = `${t('timeline_tech')}: ${ev.by || 'Unknown'}`;
                if (ev.end_time) {
                    const start = new Date(ev.timestamp);
                    const end = new Date(ev.end_time);
                    if (!isNaN(start.getTime()) && !isNaN(end.getTime())) {
                        const diffMs = end - start;
                        const diffMins = Math.round(diffMs / 60000);
                        meta += ` | ${t('timeline_duration')}: ${diffMins} ${t('timeline_mins')}`;
                    }
                }
            }

            return `
                <div class="timeline-event">
                    <span class="timeline-time">${timeStr}</span>
                    <div class="timeline-content">
                        <div class="timeline-type ${typeClass}">${icon} ${title}</div>
                        <div class="timeline-desc">${content}</div>
                        <div class="timeline-meta">${meta}</div>
                    </div>
                </div>
            `;
        }).join('');
    },

    async promptStatusChange(newStatus) {
        const currentStatus = state.activeTicket.status;
        const note = prompt(`${t('detail_update')} ${t('status_' + newStatus) || newStatus}\n\n${t('detail_notes_ph')}`);
        
        if (note === null) return; // Cancelled

        try {
            await API.updateStatus(state.activeTicket.id, {
                status: newStatus,
                notes: note || undefined
            });
            // alert(t('alert_update_success')); // Optional: Toast would be better
            this.load(state.activeTicket.id);
        } catch (error) {
            alert(t('alert_update_fail') + error.message);
        }
    },

    async handlePhotoUpload(input) {
        if (!input.files || !input.files[0]) return;
        
        const file = input.files[0];
        const statusText = ui.content.querySelector('#photo-trigger span');
        statusText.textContent = t('upload_uploading');
        
        try {
            await API.uploadPhoto(state.activeTicket.id, file);
            statusText.textContent = t('upload_saved');
            setTimeout(() => {
                this.load(state.activeTicket.id); // Reload to show new photo
            }, 1000);
        } catch (error) {
            alert(t('alert_upload_fail') + error.message);
            statusText.textContent = `📷 ${t('detail_photo_append')}`;
        }
    },

    openCheckoutModal() {
        const ticket = state.activeTicket;
        
        // Prevent duplicate invoices
        if (ticket.invoice_id) {
            alert(t('alert_dup_invoice'));
            return;
        }

        const deposit = ticket.deposit || 0;
        
        const partsTotal = ticket.total_parts_cost || 0;
        const ticketTotal = ticket.actual_cost || ticket.estimated_cost || 0;
        let laborCost = Math.max(0, ticketTotal - partsTotal);
        
        // Modal HTML
        const modalHtml = `
        <div id="checkout-modal" class="modal-overlay" style="display: flex; align-items: flex-end;">
            <div class="modal-content" style="border-radius: 20px 20px 0 0; padding: 24px; max-height: 90vh; display: flex; flex-direction: column; background: #1a1a1a;">
                <div class="modal-header" style="margin-bottom: 20px;">
                    <h3 style="font-size: 18px; color: white;">${t('co_title')}</h3>
                    <button class="btn-close-modal" style="background: none; border: none; font-size: 20px; color: #666;">✕</button>
                </div>
                
                <div class="modal-body" style="overflow-y: auto;">
                    <!-- Totals Section -->
                    <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; margin-bottom: 20px;">
                        <div class="detail-row" style="margin-bottom: 8px;">
                            <span style="color: #999;">${t('co_parts_total')}</span>
                            <span style="color: white;">${(partsTotal * 1.5).toLocaleString()} Ks</span>
                        </div>
                        <div class="input-group" style="margin-bottom: 8px;">
                            <label style="color: #999; font-size: 12px;">${t('co_labor')}</label>
                            <input type="number" id="checkout-labor" value="${laborCost}" style="background: rgba(0,0,0,0.3); border: 1px solid #333; color: white; padding: 8px; border-radius: 8px; width: 100%; font-size: 16px;">
                        </div>
                        <div class="divider" style="margin: 12px 0; border-color: #333;"></div>
                        <div class="detail-row" style="font-size: 18px; font-weight: bold;">
                            <span style="color: white;">${t('co_subtotal')}</span>
                            <span id="checkout-subtotal" style="color: #10b981;">0 Ks</span>
                        </div>
                    </div>

                    <!-- Payment Section -->
                    <h4 style="color: #666; font-size: 12px; text-transform: uppercase; margin-bottom: 12px; font-weight: 800;">${t('co_pay_det')}</h4>
                    
                    <div class="detail-row" style="margin-bottom: 12px;">
                        <span style="color: #999;">${t('co_deposit')}</span>
                        <span style="color: #ef4444;">- ${deposit.toLocaleString()} Ks</span>
                    </div>

                    <div class="detail-row" style="margin-bottom: 16px; font-size: 16px;">
                        <span style="color: white;">${t('co_bal_due')}</span>
                        <span id="checkout-due" style="color: #ef4444; font-weight: bold;">0 Ks</span>
                    </div>

                    <div class="input-group" style="margin-bottom: 12px;">
                        <label>${t('co_pay_method')}</label>
                        <select id="checkout-method" style="background: rgba(255,255,255,0.05); border: 1px solid #333; color: white; padding: 12px; border-radius: 8px; width: 100%;">
                            <option value="cash">${t('inv_cash')}</option>
                            <option value="bank_transfer">${t('inv_bank')}</option>
                            <option value="card">${t('inv_card')}</option>
                        </select>
                    </div>

                    <div class="input-group" style="margin-bottom: 20px;">
                        <label>${t('co_tendered')}</label>
                        <input type="number" id="checkout-tendered" placeholder="${t('co_ph_amount')}" style="background: rgba(255,255,255,0.05); border: 1px solid #333; color: white; padding: 12px; border-radius: 8px; width: 100%; font-size: 18px;">
                    </div>

                    <div style="background: #111; padding: 16px; border-radius: 12px; text-align: center;">
                        <div style="color: #666; font-size: 12px; margin-bottom: 4px;">${t('co_change_due')}</div>
                        <div id="checkout-change" style="color: #10b981; font-size: 24px; font-weight: 800;">0 Ks</div>
                    </div>
                </div>

                <div class="modal-footer" style="margin-top: 24px;">
                    <button id="btn-confirm-checkout" class="btn-primary" style="width: 100%; background: #10b981; padding: 16px; font-size: 16px; font-weight: bold;">
                        ${t('co_confirm_btn')}
                    </button>
                </div>
            </div>
        </div>
        `;

        // Inject
        const existingModal = document.getElementById('checkout-modal');
        if(existingModal) existingModal.remove();
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Elements
        const laborInput = document.getElementById('checkout-labor');
        const subtotalEl = document.getElementById('checkout-subtotal');
        const dueEl = document.getElementById('checkout-due');
        const tenderedInput = document.getElementById('checkout-tendered');
        const changeEl = document.getElementById('checkout-change');
        const confirmBtn = document.getElementById('btn-confirm-checkout');
        const closeBtn = document.querySelector('#checkout-modal .btn-close-modal');

        // Logic
        const partsMarkup = partsTotal * 1.5;
        
        const updateTotals = () => {
            const labor = parseFloat(laborInput.value) || 0;
            const subtotal = partsMarkup + labor;
            const due = Math.max(0, subtotal - deposit);
            const tendered = parseFloat(tenderedInput.value) || 0;
            const change = Math.max(0, tendered - due);

            subtotalEl.textContent = subtotal.toLocaleString() + ' Ks';
            dueEl.textContent = due.toLocaleString() + ' Ks';
            
            if (tendered > 0) {
                 changeEl.textContent = change.toLocaleString() + ' Ks';
            } else {
                 changeEl.textContent = '0 Ks';
            }
        };

        // Listeners
        laborInput.addEventListener('input', updateTotals);
        tenderedInput.addEventListener('input', updateTotals);
        
        closeBtn.addEventListener('click', () => {
            document.getElementById('checkout-modal').remove();
        });

        confirmBtn.addEventListener('click', async () => {
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = t('co_processing');
            
            const labor = parseFloat(laborInput.value) || 0;
            const tendered = parseFloat(tenderedInput.value) || 0;
            const method = document.getElementById('checkout-method').value;
            
            const reqData = {
                labor_override: labor,
                payment: tendered > 0 ? {
                    method: method,
                    amount: Math.min(tendered, parseFloat(dueEl.textContent.replace(/[^0-9.]/g, '')))
                } : null
            };
            
            try {
                const result = await API.createInvoiceFromTicket(ticket.id, reqData);
                
                document.getElementById('checkout-modal').remove();
                Invoice.fromTicket = ticket.id;
                Invoice.load(result.id);
            } catch (err) {
                alert('Error: ' + err.message);
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = t('co_confirm_btn');
            }
        });

        // Init
        updateTotals();
    },


    openDiagnosticsModal() {
        const modalHtml = `
        <div id="diag-modal" class="modal-overlay" style="display: flex;">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${t('tool_diag') || 'Diagnostics'}</h3>
                    <button class="btn-close-modal">✕</button>
                </div>
                <div class="modal-body">
                    <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px;">
                        ${['Screen', 'Battery', 'Charging', 'Camera (Rear)', 'Camera (Front)', 'Audio', 'FaceID/TouchID', 'WiFi/BT'].map(item => `
                            <div class="diag-item" style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 8px;">
                                <span>${item}</span>
                                <div style="display: flex; gap: 8px;">
                                    <button class="btn-diag-state" data-item="${item}" data-state="pass" style="padding: 6px 12px; border-radius: 4px; border: 1px solid #10b981; color: #10b981; background: transparent;">PASS</button>
                                    <button class="btn-diag-state" data-item="${item}" data-state="fail" style="padding: 6px 12px; border-radius: 4px; border: 1px solid #ef4444; color: #ef4444; background: transparent;">FAIL</button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <textarea id="diag-notes" placeholder="Additional notes..." style="width: 100%; height: 80px;"></textarea>
                </div>
                <div class="modal-footer">
                    <button id="btn-save-diag" class="btn-primary" style="width: 100%;">Save Log</button>
                </div>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modal = document.getElementById('diag-modal');
        
        // Listeners for state toggles
        const results = {};
        modal.querySelectorAll('.btn-diag-state').forEach(btn => {
            btn.addEventListener('click', () => {
                const item = btn.dataset.item;
                const state = btn.dataset.state;
                
                // Toggle active class visually
                btn.parentElement.querySelectorAll('button').forEach(b => {
                    b.style.background = 'transparent';
                    b.style.color = b.dataset.state === 'pass' ? '#10b981' : '#ef4444';
                });
                
                btn.style.background = state === 'pass' ? '#10b981' : '#ef4444';
                btn.style.color = 'white';
                
                results[item] = state;
            });
        });
        
        modal.querySelector('.btn-close-modal').addEventListener('click', () => modal.remove());
        
        modal.querySelector('#btn-save-diag').addEventListener('click', async () => {
            if (Object.keys(results).length === 0) {
                alert(t('alert_check_item'));
                return;
            }
            try {
                const notes = document.getElementById('diag-notes').value;
                await API.saveDiagnostics(state.activeTicket.id, results, notes);
                alert(t('alert_diag_saved'));
                modal.remove();
                this.load(state.activeTicket.id);
            } catch (e) {
                alert(e.message);
            }
        });
    },

    openPatternModal() {
        const ticket = state.activeTicket;
        const device = ticket.device || {};
        const lockType = device.lock_type || 'None';
        const passcode = device.passcode || '';
        
        let visualHtml = '';
        
        if (lockType === 'Pattern') {
            // Convert "1234" or "1 2 3 4" or "1-2-3-4" to array of digits
            const sequence = passcode.replace(/\D/g, '').split('');
            
            visualHtml = `
                <div style="display: flex; flex-direction: column; align-items: center; gap: 20px;">
                    <div style="font-size: 14px; opacity: 0.8; font-weight: 700;">Pattern Sequence: ${sequence.join(' → ')}</div>
                    
                    <div id="pattern-grid" style="display: grid; grid-template-columns: repeat(3, 60px); grid-gap: 24px; position: relative;">
                         ${[1,2,3,4,5,6,7,8,9].map(i => {
                            const isActive = sequence.includes(i.toString());
                            const order = sequence.indexOf(i.toString()) + 1;
                            const style = isActive ? 
                                `background: var(--accent-color); box-shadow: 0 0 15px var(--accent-glow); color: black;` : 
                                `background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.1);`;
                            
                            return `
                                <div class="patt-dot" style="width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 14px; ${style}">
                                    ${isActive ? order : ''}
                                </div>
                            `;
                         }).join('')}
                    </div>
                </div>
            `;
        } else {
            visualHtml = `
                <div style="padding: 40px 20px; text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 20px;">${lockType === 'None' ? '🔓' : '🔑'}</div>
                    <div style="font-size: 12px; color: var(--text-sub); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">${lockType}</div>
                    <div style="font-size: 24px; font-weight: 800; color: var(--accent-color); font-family: monospace;">${passcode || 'NO LOCK'}</div>
                </div>
            `;
        }

        const modalHtml = `
        <div id="pattern-modal" class="modal-overlay" style="display: flex;">
            <div class="modal-content" style="max-width: 320px;">
                <div class="modal-header">
                    <h3>${t('tool_lock') || 'Device Lock'}</h3>
                    <button class="btn-close-modal">✕</button>
                </div>
                <div class="modal-body">
                    ${visualHtml}
                </div>
                <div class="modal-footer" style="padding-top: 0;">
                    <button class="btn-primary btn-close-modal" style="width: 100%;">Done</button>
                </div>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modal = document.getElementById('pattern-modal');
        modal.querySelectorAll('.btn-close-modal').forEach(btn => {
            btn.addEventListener('click', () => modal.remove());
        });
    }
};
