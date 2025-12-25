import { state, ui } from '../state.js?v=5.8';
import { API } from '../api.js?v=5.8';
import { t } from '../i18n.js?v=5.8';

const CustomerState = {
    query: '',
    customers: [],
    selectedCustomer: null,
    // Pagination
    page: 0,
    limit: 20,
    hasMore: true,
    isLoadingMore: false
};

export const Customers = {
    async load() {
        ui.screenTitle.textContent = t('cust_directory');
        ui.content.innerHTML = `
            <div class="search-container" style="position: relative; margin-bottom: 20px;">
                <input type="text" id="customer-search" placeholder="${t('cust_search_ph')}" 
                       style="padding-left: 48px; background: rgba(255,255,255,0.05); border-radius: 18px;">
                <span style="position: absolute; left: 16px; top: 14px; opacity: 0.5; font-size: 18px;">🔎</span>
            </div>
            <div id="customer-list-container">
                <div class="loading">${t('cust_fetching')}</div>
            </div>
        `;
        
        // Reset state
        CustomerState.query = '';
        CustomerState.page = 0;
        CustomerState.customers = [];
        CustomerState.hasMore = true;

        this.handleSearch(true);

        const searchInput = ui.content.querySelector('#customer-search');
        searchInput.addEventListener('input', this.debounce((e) => {
            CustomerState.query = e.target.value;
            this.resetAndSearch();
        }, 300));
    },
    
    resetAndSearch() {
        CustomerState.page = 0;
        CustomerState.hasMore = true;
        CustomerState.customers = [];
        this.handleSearch(true);
    },

    async handleSearch(initial = false) {
        const listDiv = ui.content.querySelector('#customer-list-container');
        const query = CustomerState.query;
        
        if (CustomerState.isLoadingMore && !initial) return;
        CustomerState.isLoadingMore = true;
        
        const skip = CustomerState.page * CustomerState.limit;
        
        try {
            if (initial) {
                listDiv.innerHTML = `<div class="loading">${t('cust_fetching')}</div>`;
            } else {
                const btn = document.getElementById('btn-load-more-cust');
                if (btn) btn.textContent = t('loading_wait');
            }

            let newCustomers;
            if (query.length > 1) {
                // Search might not support pagination well yet in API, assuming it returns all matches for now or we update API later
                // For now, search API returns all. So if query is present, we just replace all.
                // TODO: Paginate search if needed. Currently route `search_customers` does NOT take limit/skip.
                newCustomers = await API.searchCustomers(query);
                CustomerState.hasMore = false; // Disable load more for search results for now
            } else {
                newCustomers = await API.getCustomers(CustomerState.limit, skip);
                CustomerState.hasMore = newCustomers.length === CustomerState.limit;
            }

            if (initial || query.length > 1) {
                CustomerState.customers = newCustomers;
            } else {
                CustomerState.customers = [...CustomerState.customers, ...newCustomers];
            }
            
            if (!query.length || query.length <= 1) {
                CustomerState.page++;
            }

            this.renderList();

        } catch (err) {
            listDiv.innerHTML = `<div class="error">Search failed: ${err.message}</div>`;
        } finally {
            CustomerState.isLoadingMore = false;
        }
    },
    
    renderList() {
        const listDiv = ui.content.querySelector('#customer-list-container');
        if (!listDiv) return;
        
        if (CustomerState.customers.length === 0) {
            listDiv.innerHTML = `<div class="empty-state">${t('cust_none')}</div>`;
            return;
        }

        let html = CustomerState.customers.map(c => `
            <div class="client-list-item" data-id="${c.id}">
                <div class="client-avatar">
                    ${c.name.charAt(0).toUpperCase()}
                </div>
                <div class="client-info">
                    <div class="client-name">${c.name}</div>
                    <div class="client-details">
                        <span style="opacity: 0.7;">📞</span> ${c.phone || 'N/A'}
                    </div>
                </div>
                <div class="client-arrow">❯</div>
            </div>
        `).join('');
        
        // Add Load More
        if (CustomerState.hasMore && CustomerState.query.length <= 1) {
             html += `
                <div style="padding: 20px; text-align: center;">
                    <button id="btn-load-more-cust" class="btn-secondary" style="width: 100%; padding: 12px;">${t('btn_load_more')}</button>
                </div>
            `;
        }

        listDiv.innerHTML = html;

        listDiv.querySelectorAll('.client-list-item').forEach(card => {
            card.addEventListener('click', () => {
                this.loadProfile(card.dataset.id);
            });
        });
        
        if (CustomerState.hasMore && CustomerState.query.length <= 1) {
            const btn = listDiv.querySelector('#btn-load-more-cust');
            if (btn) {
                btn.addEventListener('click', () => {
                    this.handleSearch(false);
                });
            }
        }
    },

    async loadProfile(id) {
        ui.screenTitle.textContent = t('cust_profile');
        ui.content.innerHTML = `<div class="loading">${t('cust_loading')}</div>`;

        try {
            const customer = await API.getCustomerDetail(id);
            CustomerState.selectedCustomer = customer;

            ui.content.innerHTML = `
                <div style="animation: slideUp 0.4s ease-out;">
                    <div class="card" style="padding: 24px; text-align: center; background: linear-gradient(135deg, rgba(245,158,11,0.1), transparent); margin-bottom: 24px;">
                        <div style="width: 80px; height: 80px; border-radius: 50%; background: var(--accent-color); color: black; display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: 900; margin: 0 auto 16px;">
                            ${customer.name.charAt(0).toUpperCase()}
                        </div>
                        <h2 style="font-size: 24px; margin-bottom: 4px;">${customer.name}</h2>
                        <p style="color: var(--text-sub); margin-bottom: 20px;">${customer.phone || 'No phone'} • ${customer.email || 'No email'}</p>
                        <button class="btn-primary" id="btn-edit-cust" style="margin-top: 0; width: auto; padding: 10px 24px; font-size: 14px; background: rgba(255,255,255,0.05); color: white; border: 1px solid var(--border-color);">
                            ${t('cust_edit_contact')}
                        </button>
                    </div>

                    <h3 style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-sub); margin-bottom: 12px; padding-left: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <span>${t('cust_units')}</span>
                    </h3>
                    <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px;">
                        ${customer.devices.length ? customer.devices.map(d => `
                            <div class="card" style="padding: 16px; background: rgba(255,255,255,0.02); display: flex; align-items: center; gap: 12px;">
                                <div style="font-size: 24px;">📱</div>
                                <div>
                                    <div style="font-weight: 700; font-size: 14px;">${d.brand} ${d.model}</div>
                                    <div style="font-size: 11px; opacity: 0.5;">S/N: ${d.serial || 'N/A'}</div>
                                </div>
                            </div>
                        `).join('') : `<div class="empty-state" style="padding: 20px;">${t('cust_no_devices')}</div>`}
                    </div>

                    <h3 style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-sub); margin-bottom: 12px; padding-left: 8px;">${t('cust_recent_tickets')}</h3>
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        ${customer.recent_tickets.length ? customer.recent_tickets.map(t_item => {
                            const statusClass = `status-${t_item.status.toLowerCase().replace(' ', '_')}`;
                            return `
                                <div class="card" onclick="document.dispatchEvent(new CustomEvent('viewTicket', { detail: { id: ${t_item.id} } }))" style="padding: 16px; cursor: pointer;">
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                                        <div style="font-weight: 700; font-size: 14px;">${t_item.device}</div>
                                        <span class="status-badge ${statusClass}">${t('status_' + t_item.status.toLowerCase()) || t_item.status}</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="font-size: 12px; color: var(--accent-color); font-family: monospace;">${t_item.number}</span>
                                        <span style="font-size: 11px; opacity: 0.5;">${t_item.created_at}</span>
                                    </div>
                                </div>
                            `;
                        }).join('') : `<div class="empty-state" style="padding: 20px;">${t('cust_no_history')}</div>`}
                    </div>

                    <button class="btn-primary" id="btn-back-list" style="margin-top: 40px; background: transparent; color: var(--text-sub); border: 1px solid var(--border-color);">
                        ${t('cust_back_list')}
                    </button>
                </div>
            `;

            ui.content.querySelector('#btn-back-list').addEventListener('click', () => {
                this.load();
            });

            ui.content.querySelector('#btn-edit-cust').addEventListener('click', () => {
                this.showEditModal(customer);
            });



        } catch (err) {
            ui.content.innerHTML = `<div class="error">Profile load failed: ${err.message}</div>`;
        }
    },

    showEditModal(customer) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="animation: slideUp 0.3s ease-out;">
                <div class="modal-header">
                    <h3>${t('cust_edit_title')}</h3>
                    <button class="btn-close-modal">✕</button>
                </div>
                <div class="modal-body">
                    <form id="edit-cust-form">
                        <div class="input-group">
                            <label>${t('form_fullname')}</label>
                            <input type="text" id="edit-name" value="${customer.name}" required>
                        </div>
                        <div class="input-group">
                            <label>${t('form_phone')}</label>
                            <input type="tel" id="edit-phone" value="${customer.phone || ''}" inputmode="tel" pattern="[0-9]*">
                        </div>
                        <div class="input-group">
                            <label>${t('form_email')}</label>
                            <input type="email" id="edit-email" value="${customer.email || ''}">
                        </div>
                        <button type="submit" class="btn-primary" style="margin-top: 20px; height: 56px;">${t('btn_apply')}</button>
                    </form>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Numeric strip for phone
        const phoneInp = modal.querySelector('#edit-phone');
        phoneInp.addEventListener('input', () => {
            phoneInp.value = phoneInp.value.replace(/\D/g, '');
        });

        modal.querySelector('.btn-close-modal').addEventListener('click', () => modal.remove());
        modal.querySelector('#edit-cust-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = e.target.querySelector('button');
            btn.disabled = true;
            btn.textContent = 'Saving...';

            const data = {
                name: modal.querySelector('#edit-name').value.trim(),
                phone: modal.querySelector('#edit-phone').value.trim(),
                email: modal.querySelector('#edit-email').value.trim()
            };

            try {
                await API.updateCustomer(customer.id, data);
                modal.remove();
                this.loadProfile(customer.id);
            } catch (err) {
                alert('Update failed: ' + err.message);
                btn.disabled = false;
                btn.textContent = t('btn_apply');
            }
        });
    },

    showCreateCustomerModal() {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="animation: slideUp 0.3s ease-out;">
                <div class="modal-header">
                    <h3>${t('cust_new_title')}</h3>
                    <button class="btn-close-modal">✕</button>
                </div>
                <div class="modal-body">
                    <form id="create-cust-form">
                        <div class="input-group">
                            <label>${t('form_fullname')} <span style="color: var(--accent-color);">*</span></label>
                            <input type="text" id="new-name" required placeholder="Display Name">
                        </div>
                        <div class="input-group">
                            <label>${t('form_phone')}</label>
                            <input type="tel" id="new-phone" placeholder="09xxxxxxxxx" inputmode="tel" pattern="[0-9]*">
                        </div>
                        <div class="input-group">
                            <label>${t('form_email')}</label>
                            <input type="email" id="new-email" placeholder="client@example.com">
                        </div>
                        <button type="submit" class="btn-primary" style="margin-top: 20px; height: 56px;">${t('cust_create_btn')}</button>
                    </form>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('.btn-close-modal').addEventListener('click', () => modal.remove());
        modal.querySelector('#create-cust-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = e.target.querySelector('button');
            
            const name = modal.querySelector('#new-name').value.trim();
            const phone = modal.querySelector('#new-phone').value.trim();
            const email = modal.querySelector('#new-email').value.trim();

            if (phone && !this.validatePhone(phone)) {
                alert("Invalid phone number format (min 7 digits)");
                return;
            }
            if (email && !this.validateEmail(email)) {
                alert("Invalid email format");
                return;
            }

            btn.disabled = true;
            btn.textContent = 'Creating...';

            try {
                const data = { name, phone, email };
                const result = await API.createCustomer(data);
                modal.remove();
                this.loadProfile(result.id);
            } catch (err) {
                alert('Creation failed: ' + err.message);
                btn.disabled = false;
                btn.textContent = t('cust_create_btn');
            }
        });
    },

    async showAddDeviceModal(customer) {
        let brands = [];
        try {
            brands = await API.getBrands(); // Returns dict { "Brand": ["Model1", ...], ... }
        } catch (e) {
            console.error(e);
        }
        const brandNames = Object.keys(brands);

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content" style="animation: slideUp 0.3s ease-out;">
                <div class="modal-header">
                    <h3>${t('cust_add_device')}</h3>
                    <button class="btn-close-modal">✕</button>
                </div>
                <div class="modal-body">
                    <form id="add-device-form">
                        <div class="input-group">
                            <label>${t('cust_brand')} <span style="color: var(--accent-color);">*</span></label>
                            <input type="text" id="dev-brand" list="brand-list" required placeholder="${t('cust_brand')}">
                            <datalist id="brand-list">
                                ${brandNames.map(b => `<option value="${b}">`).join('')}
                            </datalist>
                        </div>
                        <div class="input-group">
                            <label>${t('cust_model')} <span style="color: var(--accent-color);">*</span></label>
                            <input type="text" id="dev-model" list="model-list" required placeholder="${t('cust_model')}">
                            <datalist id="model-list"></datalist>
                        </div>
                        <div class="input-group">
                            <label>${t('cust_serial')}</label>
                            <input type="text" id="dev-sn" placeholder="${t('cust_optional')}" inputmode="numeric" pattern="[0-9]*">
                        </div>
                        <div class="input-group">
                            <label>${t('cust_color')}</label>
                            <input type="text" id="dev-color" placeholder="${t('cust_optional')}">
                        </div>
                        <button type="submit" class="btn-primary" style="margin-top: 20px; height: 56px;">${t('cust_reg_device')}</button>
                    </form>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const brandInput = modal.querySelector('#dev-brand');
        const modelList = modal.querySelector('#model-list');
        
        brandInput.addEventListener('input', () => {
            const val = brandInput.value;
            const models = brands[val] || [];
            modelList.innerHTML = models.map(m => `<option value="${m}">`).join('');
        });

        // Numeric strip/format for IMEI
        const snInp = modal.querySelector('#dev-sn');
        snInp.addEventListener('input', () => {
            const digits = snInp.value.replace(/\D/g, '');
            if (digits.length >= 8) {
                snInp.value = digits.replace(/(\d{4})/g, '$1 ').trim().substring(0, 19);
            } else {
                snInp.value = digits.toUpperCase();
            }
        });

        modal.querySelector('.btn-close-modal').addEventListener('click', () => modal.remove());
        modal.querySelector('#add-device-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = e.target.querySelector('button');

            const brand = modal.querySelector('#dev-brand').value.trim();
            const model = modal.querySelector('#dev-model').value.trim();
            const serial = modal.querySelector('#dev-sn').value.trim();
            const color = modal.querySelector('#dev-color').value.trim();

            // Simple IMEI check if digits > 14
            const digits = serial.replace(/\D/g, '');
            if (digits.length >= 15) {
                if (!this.validateIMEI(digits)) {
                    alert("Invalid IMEI Checksum");
                    return;
                }
            }

            btn.disabled = true;
            btn.textContent = 'Registering...';

            try {
                const data = { brand, model, serial, color };
                await API.createDevice(customer.id, data);
                modal.remove();
                this.loadProfile(customer.id);
            } catch (err) {
                alert('Device registration failed: ' + err.message);
                btn.disabled = false;
                btn.textContent = 'Register Device';
            }
        });
    },

    validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    },

    validatePhone(phone) {
        return /^[\d\s\-\(\)]{7,}$/.test(phone);
    },

    validateIMEI(imei) {
        // Simple luhn check, can copy from ticket-form or just use regex for length now
        // Copying concise version
        if (imei.length !== 15 && imei.length !== 16) return false;
        let sum = 0;
        for (let i = 0; i < 14; i++) {
            let n = parseInt(imei[i]);
            if (i % 2 === 1) {
                n *= 2;
                if (n > 9) n = (n % 10) + 1;
            }
            sum += n;
        }
        const check = (10 - (sum % 10)) % 10;
        return check === parseInt(imei[14]);
    },

    debounce(func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), wait);
        };
    }
};
