import { state, ui } from '../state.js?v=5.8';
import { API } from '../api.js?v=5.8';
import { t } from '../i18n.js?v=5.8';

const FormState = {
    step: 1, // 1: Customer, 2: Device, 3: Problem
    isAdding: false,
    selectedCustomer: null,
    selectedDevice: null,
    customers: [],
    devices: [],
    metadata: {
        brands: {},
        errors: {}
    }
};

export const TicketForm = {
    async load() {
        FormState.step = 1;
        FormState.isAdding = false;
        FormState.selectedCustomer = null;
        FormState.selectedDevice = null;
        FormState.selectedDevice = null;
        FormState.tempCustomer = null;
        FormState.tempDevice = null;

        // Hide Global FAB to prevent accidental clicks
        const fab = document.getElementById('global-fab');
        if (fab) fab.style.display = 'none';
        
        // Load metadata once
        if (!Object.keys(FormState.metadata.brands).length) {
            try {
                const [brands, errors] = await Promise.all([
                    API.getBrands(),
                    API.getErrors()
                ]);
                FormState.metadata.brands = brands;
                FormState.metadata.errors = errors;
            } catch (err) {
                console.error('Metadata load failed:', err);
            }
        }
        
        this.render();
    },

    render() {
        ui.screenTitle.textContent = t('form_intake');
        let html = '';

        if (FormState.step === 1) {
            html = FormState.isAdding ? this.renderAddCustomer() : this.renderCustomerStep();
        } else if (FormState.step === 2) {
            html = FormState.isAdding ? this.renderAddDevice() : this.renderDeviceStep();
        } else {
            html = this.renderProblemStep();
        }

        ui.content.innerHTML = `
            <div class="ticket-form-container" style="animation: slideUp 0.3s ease-out;">
                <div class="step-indicator" style="display: flex; gap: 8px; margin-bottom: 24px;">
                    ${[1, 2, 3].map(i => `
                        <div style="flex: 1; height: 4px; border-radius: 2px; transition: all 0.3s; background: ${i <= FormState.step ? 'var(--accent-color)' : 'rgba(255,255,255,0.1)'}"></div>
                    `).join('')}
                </div>
                ${html}
            </div>
        `;

        this.bindEvents();
    },

    renderCustomerStep() {
        return `
            <div style="text-align: center; margin-bottom: 24px;">
                <div style="font-size: 32px; margin-bottom: 8px;">🔍</div>
                <h2 style="font-size: 20px; margin-bottom: 4px;">${t('form_find_cust')}</h2>
                <p style="font-size: 13px; color: var(--text-sub);">${t('form_find_desc')}</p>
            </div>
            
            <div class="search-container" style="position: relative;">
                <input type="text" id="cust-search" placeholder="${t('cust_search_ph')}" autofocus 
                       style="padding-left: 48px; background: rgba(255,255,255,0.05); border-radius: 18px;">
                <span style="position: absolute; left: 16px; top: 14px; opacity: 0.5; font-size: 18px;">🔎</span>
            </div>
            
            <div id="cust-results" style="margin-top: 20px; display: flex; flex-direction: column; gap: 12px;">
                <!-- Search results will appear here -->
            </div>

            <div style="margin-top: 40px; text-align: center;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                    <div style="flex: 1; height: 1px; background: var(--border-color);"></div>
                    <span style="font-size: 11px; color: var(--text-sub); text-transform: uppercase; letter-spacing: 1px;">${t('form_or')}</span>
                    <div style="flex: 1; height: 1px; background: var(--border-color);"></div>
                </div>
                <button class="btn-primary" style="background: var(--accent-glow); color: var(--accent-light); border: 1px solid var(--accent-color); font-weight: 700;" id="btn-show-add-cust">
                    ${t('form_reg_new')}
                </button>
            </div>
        `;
    },

    renderAddCustomer() {
        return `
            <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 32px;">
                <button id="btn-cancel-add" style="background: rgba(255,255,255,0.05); border: none; color: white; width: 32px; height: 32px; border-radius: 50%; font-size: 12px;">✕</button>
                <h2 style="font-size: 20px; margin: 0;">${t('form_new_acc')}</h2>
            </div>
            
            <div class="card" style="padding: 24px; margin-bottom: 24px;">
                <form id="add-cust-form">
                    <div class="input-group">
                        <label>${t('form_fullname')} <span style="color: var(--accent-color);">*</span></label>
                        <input type="text" id="add-cust-name" required placeholder="Display name" autofocus>
                    </div>
                    <div class="input-group">
                        <label>${t('form_phone')}</label>
                        <input type="tel" id="add-cust-phone" placeholder="09xxxxxxxxx" inputmode="tel" pattern="[0-9]*">
                    </div>
                    <div class="input-group">
                        <label>${t('form_email')}</label>
                        <input type="email" id="add-cust-email" placeholder="client@example.com">
                    </div>
                    <button type="submit" class="btn-primary" style="margin-top: 12px; height: 56px;">${t('form_save_cont')}</button>
                </form>
            </div>
        `;
    },

    renderDeviceStep() {
        return `
            <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px;">
                <button id="btn-back" style="background: rgba(255,255,255,0.05); border: none; color: var(--accent-color); width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">←</button>
                <div>
                   <h2 style="font-size: 20px; margin: 0;">${t('form_sel_unit')}</h2>
                   <p style="font-size: 12px; color: var(--text-sub); margin: 0;">${t('form_acc')} <strong style="color: var(--accent-color)">${FormState.selectedCustomer.name}</strong></p>
                </div>
            </div>
            
            <div id="device-results" style="display: flex; flex-direction: column; gap: 12px;">
                ${FormState.devices.length ? FormState.devices.map(d => `
                    <div class="card device-item" data-id="${d.id}" style="padding: 18px; cursor: pointer; transition: all 0.2s; border: 1px solid var(--border-color); background: rgba(255,255,255,0.03); display: flex; flex-direction: row; align-items: center; gap: 15px;">
                        <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(255,255,255,0.05); display: flex; align-items: center; justify-content: center; font-size: 20px;">📱</div>
                        <div style="flex: 1;">
                            <div style="font-weight: 700; font-size: 15px;">${d.brand} ${d.model}</div>
                            <div style="font-size: 11px; opacity: 0.5; margin-top: 2px;">Serial: ${d.serial || 'NOT RECORDED'}</div>
                        </div>
                        <div style="color: var(--accent-color); opacity: 0.5;">❯</div>
                    </div>
                `).join('') : `<div class="empty-state" style="padding: 60px 0;">${t('cust_no_devices')}</div>`}
            </div>

            <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid var(--border-color); text-align: center;">
                <button class="btn-primary" style="background: transparent; color: var(--accent-light); border: 1.5px dashed var(--accent-color); padding: 14px;" id="btn-show-add-device">
                    ${t('form_reg_dev')}
                </button>
            </div>
        `;
    },

    renderAddDevice() {
        const brands = Object.keys(FormState.metadata.brands);
        return `
            <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px;">
                <button id="btn-cancel-add" style="background: rgba(255,255,255,0.05); border: none; color: white; width: 32px; height: 32px; border-radius: 50%; font-size: 12px;">✕</button>
                <h2 style="font-size: 20px; margin: 0;">${t('cust_add_device')}</h2>
            </div>
            
            <div class="card" style="padding: 24px;">
                <form id="add-device-form">
                    <div class="input-group">
                        <label>${t('form_brand_mfr')} <span style="color: var(--accent-color);">*</span></label>
                        <input type="text" id="add-dev-brand" list="brand-list" required placeholder="e.g. Apple, Samsung, Google" autofocus>
                        <datalist id="brand-list">
                            ${brands.map(b => `<option value="${b}">`).join('')}
                        </datalist>
                    </div>
                    <div class="input-group">
                        <label>${t('form_exact_model')} <span style="color: var(--accent-color);">*</span></label>
                        <input type="text" id="add-dev-model" list="model-list" required placeholder="e.g. iPhone 15 Pro Max">
                        <datalist id="model-list"></datalist>
                    </div>
                    <div class="input-group">
                        <label>${t('form_imei')}</label>
                        <input type="text" id="add-dev-sn" placeholder="Digits only for IMEI" inputmode="numeric" pattern="[0-9]*">
                    </div>
                    <div class="input-group">
                        <input type="text" id="add-dev-color" placeholder="e.g. Titanium Blue">
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                        <div class="input-group">
                            <label>${t('form_lock_type')}</label>
                            <select id="add-dev-lock" style="width: 100%; padding: 16px; border-radius: 14px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); color: white; font-size: 16px;">
                                <option value="None">None</option>
                                <option value="Passcode">Passcode</option>
                                <option value="Pattern">Pattern</option>
                                <option value="Password">Password</option>
                            </select>
                        </div>
                        <div class="input-group">
                            <label>${t('form_passcode')}</label>
                            <input type="text" id="add-dev-pass" placeholder="123456">
                        </div>
                    </div>
                    <button type="submit" class="btn-primary" style="margin-top: 12px; height: 56px;">${t('form_save_spec')}</button>
                </form>
            </div>
        `;
    },

    // Updated renderProblemStep with Checkboxes
    renderProblemStep() {
        const allErrors = [];
        Object.entries(FormState.metadata.errors).forEach(([cat, list]) => {
            list.forEach(err => allErrors.push({ category: cat, label: err }));
        });

        // Pre-defined Accessories List (Reduced to essentials)
        const accessoriesList = [
            "SIM", "Case", "Charger", "Box"
        ];
        
        // Determine Device Brand/Model for display
        let devDisplay = "Unknown Device";
        if (FormState.selectedDevice) {
             devDisplay = `${FormState.selectedDevice.brand} ${FormState.selectedDevice.model}`;
        } else if (FormState.tempDevice) {
             devDisplay = `${FormState.tempDevice.brand} ${FormState.tempDevice.model} (New)`;
        }

        return `
            <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px;">
                <button id="btn-back" style="background: rgba(255,255,255,0.05); border: none; color: var(--accent-color); width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">←</button>
                <div>
                   <h2 style="font-size: 20px; margin: 0;">${t('form_job_part')}</h2>
                   <p style="font-size: 12px; color: var(--text-sub); margin: 0;">${devDisplay}</p>
                </div>
            </div>
            
            <div class="card" style="padding: 24px; margin-bottom: 24px;">
                <form id="final-form">
                    <div class="input-group">
                        <label>${t('form_prim_err')} <span style="color: var(--accent-color);">*</span></label>
                        <input type="text" id="job-error" list="error-list" placeholder="${t('form_prob_desc')}" required autofocus>
                        <datalist id="error-list">
                            ${allErrors.map(e => `<option value="${e.label}">${e.category}</option>`).join('')}
                        </datalist>
                    </div>
                    
                    <div class="input-group">
                        <label>${t('form_tech_obs')}</label>
                        <textarea id="job-desc" rows="3" placeholder="${t('form_symp_ph')}"></textarea>
                    </div>

                    <div class="input-group">
                        <label>${t('form_accs')}</label>
                        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px;">
                            ${accessoriesList.map(acc => `
                                <label style="display: flex; align-items: center; gap: 4px; font-weight: 500; font-size: 11px; background: rgba(255,255,255,0.03); padding: 4px 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); cursor: pointer;">
                                    <input type="checkbox" name="accessories" value="${acc}" style="width: 12px; height: 12px; margin: 0;">
                                    ${acc}
                                </label>
                            `).join('')}
                        </div>
                        <input type="text" id="job-accessories-other" placeholder="${t('form_other')}" style="font-size: 12px; padding: 8px; height: 32px;">
                    </div>

                    <div class="input-group">
                        <label>${t('form_prio')}</label>
                        <select id="job-priority" style="width: 100%; padding: 16px; border-radius: 14px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); color: white; font-size: 16px;">
                            <option value="low">${t('form_prio_low')}</option>
                            <option value="medium" selected>${t('form_prio_med')}</option>
                            <option value="high">${t('form_prio_high')}</option>
                            <option value="critical">${t('form_prio_crit')}</option>
                        </select>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 10px;">
                        <div class="input-group">
                            <label>${t('form_quote')}</label>
                            <input type="number" id="job-cost" value="0" inputmode="decimal">
                        </div>
                        <div class="input-group">
                            <label>${t('form_deposit')}</label>
                            <input type="number" id="job-deposit" value="0" inputmode="decimal">
                        </div>
                    </div>

                    <button type="submit" class="btn-primary" style="margin-top: 16px; height: 60px; box-shadow: 0 10px 30px rgba(245, 158, 11, 0.2);">
                        ${t('form_init_ticket')}
                    </button>
                </form>
            </div>
        `;
    },

    bindEvents() {
        const backBtn = ui.content.querySelector('#btn-back');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                FormState.step--;
                FormState.isAdding = false;
                this.render();
            });
        }

        const cancelAddBtn = ui.content.querySelector('#btn-cancel-add');
        if (cancelAddBtn) {
            cancelAddBtn.addEventListener('click', () => {
                FormState.isAdding = false;
                this.render();
            });
        }

        if (FormState.step === 1) {
            if (!FormState.isAdding) {
                const searchInput = ui.content.querySelector('#cust-search');
                searchInput.addEventListener('input', this.debounce((e) => this.handleCustomerSearch(e.target.value), 300));
                ui.content.querySelector('#btn-show-add-cust').addEventListener('click', () => {
                    FormState.isAdding = true;
                    this.render();
                });
            } else {
                ui.content.querySelector('#add-cust-form').addEventListener('submit', (e) => this.handleAddCustomer(e));
            }
        } else if (FormState.step === 2) {
            // Updated Step 2 Logic for Temp Customer
            const devHeader = ui.content.querySelector('h2'); // Select Unit header logic handled in render
            
            if (!FormState.isAdding) {
                // If using existing customer, show list. If Temp Customer, list is empty so show Add button only or auto-trigger add?
                // Logic: If Temp Customer, we have NO devices. So show empty state or auto-switch to Add Device?
                // Better UX: If Temp Customer, renderDeviceStep shows empty list, user clicks "Add Device".
                
                ui.content.querySelectorAll('.device-item').forEach(item => {
                    item.addEventListener('click', () => {
                        FormState.selectedDevice = FormState.devices.find(d => d.id == item.dataset.id);
                        FormState.tempDevice = null;
                        FormState.step = 3;
                        this.render();
                    });
                });
                ui.content.querySelector('#btn-show-add-device').addEventListener('click', () => {
                    FormState.isAdding = true;
                    this.render();
                });
            } else {
                const brandInput = ui.content.querySelector('#add-dev-brand');
                const modelList = ui.content.querySelector('#model-list');
                
                brandInput.addEventListener('input', () => {
                    const brand = brandInput.value;
                    const models = FormState.metadata.brands[brand] || [];
                    modelList.innerHTML = models.map(m => `<option value="${m}">`).join('');
                });

                ui.content.querySelector('#add-device-form').addEventListener('submit', (e) => this.handleAddDevice(e));
            }
        } else if (FormState.step === 3) {
            ui.content.querySelector('#final-form').addEventListener('submit', (e) => this.handleSubmit(e));
        }
        
        this.attachRealtimeValidation();
        const firstInput = ui.content.querySelector('input[autofocus]');
        if (firstInput) firstInput.focus();
    },

    debounce(func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), wait);
        };
    },

    validateEmail(email) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email); },

    validatePhone(phone) {
        const clean = phone.replace(/[\s\-]/g, '');
        return /^(09|\+?959)\d{7,12}$/.test(clean);
    },

    validateIMEI(imei) {
        if (imei.length === 16) return true; 
        if (imei.length !== 15) return false;
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

    formatSN(sn) { return sn.toUpperCase().replace(/[^A-Z0-9-_]/g, ''); },

    formatIMEI(imei) {
        let digits = imei.replace(/\D/g, '').substring(0, 16);
        let formatted = '';
        for (let i = 0; i < digits.length; i++) {
            if (i > 0 && i % 4 === 0) formatted += ' ';
            formatted += digits[i];
        }
        return formatted;
    },

    showFieldError(input, message) {
        input.classList.add('input-error');
        const group = input.closest('.input-group');
        let errorDiv = group.querySelector('.error-msg');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-msg';
            group.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    },
    
    clearFieldError(input) {
        input.classList.remove('input-error');
        const group = input.closest('.input-group');
        const errorDiv = group.querySelector('.error-msg');
        if (errorDiv) errorDiv.style.display = 'none';
    },

    clearFieldErrors() {
        ui.content.querySelectorAll('.input-error').forEach(el => el.classList.remove('input-error'));
        ui.content.querySelectorAll('.error-msg').forEach(el => el.style.display = 'none');
    },

    attachRealtimeValidation() {
          const emailInput = ui.content.querySelector('#add-cust-email');
          if (emailInput) {
              emailInput.addEventListener('input', () => {
                  const val = emailInput.value.trim();
                  if (val && !this.validateEmail(val)) this.showFieldError(emailInput, 'Invalid email format');
                  else this.clearFieldError(emailInput);
              });
          }
          const phoneInput = ui.content.querySelector('#add-cust-phone');
          if (phoneInput) {
              phoneInput.addEventListener('input', (e) => {
                  phoneInput.value = phoneInput.value.replace(/\D/g, ''); // Strip non-numeric
                  const val = phoneInput.value.trim();
                  if (val && !this.validatePhone(val)) this.showFieldError(phoneInput, 'Invalid phone (min 7 digits)');
                  else this.clearFieldError(phoneInput);
              });
          }
          ['#add-cust-name', '#add-dev-brand', '#add-dev-model'].forEach(sel => {
              const inp = ui.content.querySelector(sel);
              if(inp) inp.addEventListener('input', () => { if(inp.value.trim()) this.clearFieldError(inp); });
          });

           const snInput = ui.content.querySelector('#add-dev-sn');
           if (snInput) {
               snInput.addEventListener('input', (e) => {
                   const start = snInput.selectionStart;
                   let val = snInput.value;
                   
                   // Strip non-numeric for IMEI logic
                   const digits = val.replace(/\D/g, '');
                   
                   // Re-apply formatting if it looks like an IMEI
                   if (digits.length >= 8) val = this.formatIMEI(digits);
                   else val = digits.toUpperCase(); // For S/N fallback
                   
                   if (snInput.value !== val) {
                       snInput.value = val;
                       const diff = val.length - (e.target.dataset.lastLen || 0);
                       snInput.setSelectionRange(start + diff, start + diff);
                   }
                   e.target.dataset.lastLen = val.length;
                   const cleanDigits = val.replace(/\D/g, '');
                   if (cleanDigits.length >= 15 && cleanDigits.length <= 16) {
                       if (!this.validateIMEI(cleanDigits)) this.showFieldError(snInput, 'Invalid IMEI checksum');
                       else this.clearFieldError(snInput);
                   } else this.clearFieldError(snInput);
               });
           }
    },

    async handleCustomerSearch(query) {
         if (!query) { ui.content.querySelector('#cust-results').innerHTML = ''; return; }
         try {
             const customers = await API.searchCustomers(query);
             const resultsDiv = ui.content.querySelector('#cust-results');
             resultsDiv.innerHTML = customers.length ? customers.map(c => `
                 <div class="card cust-item" data-id="${c.id}" style="padding: 16px; cursor: pointer; border-left: 4px solid transparent; transition: all 0.2s; border: 1px solid rgba(255,255,255,0.05);">
                     <div style="font-weight: 700;">${c.name}</div>
                     <div style="font-size: 11px; opacity: 0.6; margin-top: 4px;">📞 ${c.phone || 'No phone'}</div>
                 </div>
             `).join('') : `<div class="empty-state">${t('cust_none')}</div>`;
 
             resultsDiv.querySelectorAll('.cust-item').forEach(item => {
                 item.addEventListener('click', async () => {
                     FormState.selectedCustomer = customers.find(c => c.id == item.dataset.id);
                     FormState.tempCustomer = null; 
                     FormState.isAdding = true; 
                     FormState.step = 2;
                     this.render();
                 });
             });
         } catch (err) { console.error(err); }
    },

    async handleAddCustomer(e) {
        e.preventDefault();
        this.clearFieldErrors();
        
        const nameInput = ui.content.querySelector('#add-cust-name');
        const emailInput = ui.content.querySelector('#add-cust-email');
        const phoneInput = ui.content.querySelector('#add-cust-phone');
        
        const name = nameInput.value.trim();
        const email = emailInput.value.trim();
        const phone = phoneInput.value.trim();
        
        let hasError = false;
        if (!name) { this.showFieldError(nameInput, 'Name is required'); hasError = true; }
        if (email && !this.validateEmail(email)) { this.showFieldError(emailInput, 'Invalid email format'); hasError = true; }
        if (phone && !this.validatePhone(phone)) { this.showFieldError(phoneInput, 'Invalid phone format'); hasError = true; }
        if (hasError) return;

        FormState.selectedCustomer = null; 
        FormState.tempCustomer = { name, phone, email };
        
        FormState.devices = []; 
        FormState.isAdding = false;
        FormState.step = 2;
        this.render();
    },

    async handleAddDevice(e) {
        e.preventDefault();
        this.clearFieldErrors();

        const brandInput = ui.content.querySelector('#add-dev-brand');
        const modelInput = ui.content.querySelector('#add-dev-model');
        const snInput = ui.content.querySelector('#add-dev-sn');
        
        const brand = brandInput.value.trim();
        const model = modelInput.value.trim();
        const imei = snInput.value.trim();
        
        let hasError = false;
        if (!brand) { this.showFieldError(brandInput, 'Brand is required'); hasError = true; }
        if (!model) { this.showFieldError(modelInput, 'Model is required'); hasError = true; }

        const digitsOnly = imei.replace(/\D/g, '');
        if (digitsOnly.length >= 15 && digitsOnly.length <= 16) {
            if (!this.validateIMEI(digitsOnly)) { this.showFieldError(snInput, 'Invalid IMEI checksum'); hasError = true; }
        }
        if (hasError) return;

        const data = {
            brand: brand,
            model: model,
            serial: imei,
            color: ui.content.querySelector('#add-dev-color').value,
            lock_type: ui.content.querySelector('#add-dev-lock').value,
            passcode: ui.content.querySelector('#add-dev-pass').value
        };

        FormState.selectedDevice = null;
        FormState.tempDevice = data;
        
        FormState.isAdding = false;
        FormState.step = 3;
        this.render();
    },

    async loadCustomerDevices() {
        if (!FormState.selectedCustomer) { FormState.devices = []; return; }
        try {
            FormState.devices = await API.getCustomerDevices(FormState.selectedCustomer.id);
            FormState.step = 2;
            FormState.isAdding = false;
            this.render();
        } catch (err) { console.error(err); }
    },

    async handleSubmit(e) {
        e.preventDefault();
        
        const checkedAcc = Array.from(ui.content.querySelectorAll('input[name="accessories"]:checked'))
            .map(cb => cb.value);
        const otherAcc = ui.content.querySelector('#job-accessories-other').value.trim();
        if (otherAcc) checkedAcc.push(otherAcc);
        
        const accessoriesStr = checkedAcc.join(', ');

        const ticketData = {
            error: ui.content.querySelector('#job-error').value,
            error_description: ui.content.querySelector('#job-desc').value,
            accessories: accessoriesStr,
            priority: ui.content.querySelector('#job-priority').value,
            estimated_cost: parseFloat(ui.content.querySelector('#job-cost').value) || 0,
            deposit_paid: parseFloat(ui.content.querySelector('#job-deposit').value) || 0,
            internal_notes: ""
        };

        const payload = {
            customer: FormState.tempCustomer || { id: FormState.selectedCustomer.id },
            device: FormState.tempDevice || { id: FormState.selectedDevice.id },
            ticket: ticketData
        };

        try {
            ui.content.innerHTML = '<div class="loading">Creating ticket...</div>';
            const result = await API.createTicketComposite(payload);
            
            ui.content.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; animation: slideUp 0.5s ease-out; padding: 24px;">
                    <div style="font-size: 72px; margin-bottom: 24px; filter: drop-shadow(0 0 20px rgba(245, 158, 11, 0.3));">✨</div>
                    <h2 style="font-size: 28px; color: var(--text-main); margin-bottom: 12px; font-weight: 800; letter-spacing: -0.5px;">${t('form_done_title')}</h2>
                    <p style="color: var(--text-sub); font-size: 16px; margin-bottom: 40px;">${t('form_done_msg')}</p>
                    
                    <div style="display: flex; flex-direction: column; gap: 16px; width: 100%; max-width: 280px;">
                        <button class="btn-primary" id="btn-print" style="margin-top: 0; background: rgba(245, 158, 11, 0.1); border: 2px solid var(--accent-color); color: var(--accent-color); box-shadow: none;">
                            <span style="margin-right: 8px;">🖨️</span> ${t('form_print')}
                        </button>
                        <button class="btn-primary" id="btn-done" style="margin-top: 0;">
                            ${t('form_hub')}
                        </button>
                    </div>
                </div>
            `;
            ui.content.querySelector('#btn-done').addEventListener('click', () => {
                document.dispatchEvent(new CustomEvent('loadDashboard'));
            });
            ui.content.querySelector('#btn-print').addEventListener('click', async () => {
                try {
                    const btn = ui.content.querySelector('#btn-print');
                    btn.disabled = true;
                    btn.innerHTML = 'Sending to printer...';
                    await API.printTicket(result.ticket_id);
                    btn.innerHTML = t('form_sent_print');
                    setTimeout(() => { btn.disabled = false; btn.innerHTML = t('form_print_again'); }, 3000);
                } catch (err) {
                    alert('Print failed: ' + err.message);
                    ui.content.querySelector('#btn-print').disabled = false;
                    ui.content.querySelector('#btn-print').innerHTML = t('form_print');
                }
            });
        } catch (err) {
            alert('Failed: ' + err.message);
            this.render();
        }
    }
};
