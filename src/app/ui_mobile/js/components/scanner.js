import { state, ui } from '../state.js?v=5.8';
import { API } from '../api.js?v=5.8';
import { t } from '../i18n.js?v=5.8';

let html5QrCode = null;

export const Scanner = {
    load() {
        const isStaff = state.user.role === 'staff';
        ui.screenTitle.textContent = isStaff ? t('scan_lookup') : t('scan_title');
        
        ui.content.innerHTML = `
            <div class="card" style="margin-bottom: 24px;">
                <h3 style="font-size: 14px; text-transform: uppercase; margin-bottom: 12px; opacity: 0.7;">${t('scan_manual')}</h3>
                
                <div style="display: flex; background: rgba(255,255,255,0.05); padding: 4px; border-radius: 8px; margin-bottom: 12px;">
                     <button class="type-btn active" data-type="ticket" style="flex: 1; padding: 8px; border: none; background: var(--accent-color); color: black; border-radius: 6px; font-weight: 700; transition: all 0.2s;">${t('scan_ticket')}</button>
                     <button class="type-btn" data-type="invoice" style="flex: 1; padding: 8px; border: none; background: transparent; color: #888; border-radius: 6px; font-weight: 700; transition: all 0.2s;">${t('scan_invoice')}</button>
                </div>

                <div style="display: flex; gap: 8px;">
                    <input type="text" id="manual-ticket-id" placeholder="${t('scan_enter_id')}" style="flex: 1;">
                    <button class="btn-primary" id="search-btn" style="margin-top: 0; width: auto; padding: 12px 20px;">${t('scan_go')}</button>
                </div>
                <p id="search-error" style="color: var(--error-color); margin: 8px 0 0; font-size: 12px; display: none;"></p>
            </div>

            <div class="scanner-container">
                <div id="reader-wrapper" style="display: none; width: 100%; max-width: 400px; margin: 0 auto 0; position: relative;">
                    <div id="reader" style="width: 100%;"></div>
                    <!-- Reticle Overlay -->
                    <div class="scanner-reticle">
                        <div class="reticle-corner reticle-tl"></div>
                        <div class="reticle-corner reticle-tr"></div>
                        <div class="reticle-corner reticle-bl"></div>
                        <div class="reticle-corner reticle-br"></div>
                        <div class="laser-line"></div>
                    </div>
                </div>
                
                <div id="scanner-placeholder" class="scanner-box" style="margin-bottom: 20px;">
                    <div class="scanner-overlay"></div>
                    <p style="margin-top: 20px;">${isStaff ? t('scan_instr_staff') : t('scan_instr_tech')}</p>
                </div>
                
                <div id="scanner-controls" style="width: 100%; max-width: 400px;">
                    <button class="btn-primary" id="start-scan">
                        ${t('scan_open')}
                    </button>
                    
                    <button class="btn-primary" id="stop-scan" style="display: none; background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); margin-top: 0;">
                        ${t('scan_stop')}
                    </button>



                    <div class="scanner-controls-row" id="extra-controls" style="display: none;">
                        <button class="btn-secondary" id="flip-camera">
                            <span class="btn-icon">🔄</span> ${t('scan_flip')}
                        </button>
                    </div>

                    <div class="scanner-controls-row">
                        <button class="btn-secondary" id="btn-paste">
                            <span class="btn-icon">📋</span> ${t('scan_paste')}
                        </button>
                    </div>
                </div>
            </div>
        `;

        const searchBtn = ui.content.querySelector('#search-btn');
        const searchInput = ui.content.querySelector('#manual-ticket-id');
        const errorMsg = ui.content.querySelector('#search-error');
        const startBtn = ui.content.querySelector('#start-scan');
        const stopBtn = ui.content.querySelector('#stop-scan');
        const readerWrapper = ui.content.querySelector('#reader-wrapper');
        const placeholder = ui.content.querySelector('#scanner-placeholder');
        const typeBtns = ui.content.querySelectorAll('.type-btn');

        // Toggle Logic
        typeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const type = e.target.dataset.type;
                this.activeSearchType = type;
                
                // Update UI
                typeBtns.forEach(b => {
                    b.classList.remove('active');
                    b.style.background = 'transparent';
                    b.style.color = '#888';
                });
                
                e.target.classList.add('active');
                e.target.style.background = 'var(--accent-color)';
                e.target.style.color = 'black';
                
                ui.content.querySelector('#manual-ticket-id').placeholder = type === 'ticket' ? t('scan_ph_ticket') : t('scan_ph_inv');
            });
        });

        searchBtn.addEventListener('click', async () => {
            const id = searchInput.value.trim();
            if (!id) return;
            this.handleScanResult(id);
        });



        const flipBtn = ui.content.querySelector('#flip-camera');
        const pasteBtn = ui.content.querySelector('#btn-paste');


        startBtn.addEventListener('click', () => {
            this.startScanner();
        });

        stopBtn.addEventListener('click', () => {
            this.stopScanner();
        });

        flipBtn.addEventListener('click', () => {
            this.flipCamera();
        });



        pasteBtn.addEventListener('click', async () => {
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    this.handleScanResult(text);
                } else {
                    alert(t('scan_clip_empty'));
                }
            } catch (err) {
                // Fallback for non-secure contexts
                 const val = prompt(t('scan_paste_prompt'));
                 if(val) this.handleScanResult(val);
            }
        });



    },

    activeSearchType: 'ticket',
    currentFacingMode: "environment", // environment or user

    async startScanner() {
        const startBtn = ui.content.querySelector('#start-scan');
        const stopBtn = ui.content.querySelector('#stop-scan');
        const extraControls = ui.content.querySelector('#extra-controls');
        const readerWrapper = ui.content.querySelector('#reader-wrapper');
        const placeholder = ui.content.querySelector('#scanner-placeholder');
        const manualInput = ui.content.querySelector('#manual-ticket-id');

        // Critical Check: Modern browsers only allow camera access on HTTPS or localhost
        if (!window.isSecureContext && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
            alert(t('err_camera_secure'));
            return;
        }

        try {
            if (!html5QrCode) {
                html5QrCode = new Html5Qrcode("reader");
            }

            placeholder.style.display = 'none';
            readerWrapper.style.display = 'block';
            startBtn.style.display = 'none';

            stopBtn.style.display = 'block';
            extraControls.style.display = 'flex';

            const config = { fps: 10, qrbox: { width: 250, height: 250 } };

            await html5QrCode.start(
                { facingMode: this.currentFacingMode },
                config,
                (decodedText, decodedResult) => {
                    this.onScanSuccess(decodedText);
                },
                (errorMessage) => {
                    // silent errors as it scans constantly
                }
            );
        } catch (err) {
            console.error("Scanner start failed", err);
            
            // Check for Secure Context / SSL Error (common on local IPs)
            const isSecureContextError = !window.isSecureContext && (
                err.name === 'NotAllowedError' || 
                err.message.includes('permission') ||
                err.message.includes('secure')
            );

            if (isSecureContextError) {
                const currentIP = window.location.host;
                
                // Replace scanner UI with Help Guide
                ui.content.innerHTML = `
                <div class="card" style="border: 1px solid var(--error-color); background: rgba(239, 68, 68, 0.05);">
                    <h3 style="color: var(--error-color); margin-bottom: 12px;">⚠️ Camera Access Blocked</h3>
                    <p style="font-size: 13px; margin-bottom: 16px; line-height: 1.5;">
                        Android Chrome blocks cameras on "insecure" connections (like this local IP), but you can fix it in 30 seconds.
                    </p>
                    
                    <div style="background: var(--bg-secondary); padding: 12px; border-radius: 8px; margin-bottom: 16px;">
                        <ol style="margin-left: 20px; font-size: 13px; line-height: 1.6;">
                            <li>Open Chrome's address bar.</li>
                            <li>Type: <b style="color: var(--accent-color);">chrome://flags</b></li>
                            <li>Search for: <b>unsafely</b></li>
                            <li>Find <b>"Insecure origins treated as secure"</b></li>
                            <li>Change it to <b>Enabled</b></li>
                            <li>Type this IP in the box:<br><code style="background:black; padding:2px 4px; border-radius:4px;">http://${currentIP}</code></li>
                            <li>Click <b>Relaunch</b>.</li>
                        </ol>
                    </div>
                    
                    <button class="btn-primary" onclick="window.location.reload()">I Fixed It (Reload)</button>
                </div>
                `;
                return;
            }

            let msg = t('err_camera_error') + (err.message || err);
            if (err.name === 'NotAllowedError') {
                msg = t('err_camera_denied');
            } else if (err.name === 'NotFoundError') {
                msg = t('err_camera_not_found');
            }
            alert(msg);
            this.stopScanner();

        }
    },
    async stopScanner() {
        if (!ui.content.isConnected) return; // Prevent errors if unmounted

        const startBtn = ui.content.querySelector('#start-scan');
        const stopBtn = ui.content.querySelector('#stop-scan');
        const readerWrapper = ui.content.querySelector('#reader-wrapper');
        const placeholder = ui.content.querySelector('#scanner-placeholder');


        if (html5QrCode) {
            try {
                if (html5QrCode.isScanning) {
                    await html5QrCode.stop();
                }
            } catch (err) {
                // Ignore stop errors
            }
        }
        
        if (readerWrapper) readerWrapper.style.display = 'none';
        const extraControls = ui.content.querySelector('#extra-controls');
        if (extraControls) extraControls.style.display = 'none';
        
        if (placeholder) placeholder.style.display = 'block';
        if (startBtn) startBtn.style.display = 'block';
        if (stopBtn) stopBtn.style.display = 'none';

    },

    async flipCamera() {
        this.currentFacingMode = this.currentFacingMode === "environment" ? "user" : "environment";
        await this.stopScanner();
        await this.startScanner();
    },

    onScanSuccess(decodedText) {
        // Vibrate and Beep
        if (navigator.vibrate) navigator.vibrate(200);
        
        // Simple beep using AudioContext
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.frequency.value = 800;
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            gain.gain.exponentialRampToValueAtTime(0.00001, ctx.currentTime + 0.1);
            osc.stop(ctx.currentTime + 0.1);
        } catch(e) { console.log("Audio play failed", e); }

        // DEBUG: Alert the result to check if it matches expectations
        // alert("DEBUG: Scanned Code = [" + decodedText + "]"); // Commented out for prod

        console.log("Scanned result:", decodedText);
        this.stopScanner();
        this.handleScanResult(decodedText);
    },

    async handleScanResult(result) {
        const errorMsg = ui.content.querySelector('#search-error');
        
        try {
            if (errorMsg) errorMsg.style.display = 'none';
            
            // Show loading state
            const originalTitle = ui.screenTitle.textContent;
            ui.screenTitle.textContent = t('inv_loading'); // Re-using loading text
            
            // 1. Try smart ticket/invoice lookup based on toggle
            try {
                if (this.activeSearchType === 'invoice') {
                     // Direct Invoice Detail Lookup
                     const inv = await API.getInvoiceDetail(result.trim());
                     if (inv && inv.id) {
                         // Switch to Invoices tab and load detail
                         document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                         const invNav = document.querySelector('.nav-item[data-screen="invoices"]');
                         if (invNav) invNav.classList.add('active');

                         import('./invoice.js?v=5.8').then(m => {
                             m.Invoice.load();
                             setTimeout(() => m.Invoice.openDetail(inv), 100);
                         });
                         return;
                     }
                } else {
                    // Ticket Lookup (Default)
                    const data = await API.lookupTicket(result.trim());
                    if (data.id) {
                        document.dispatchEvent(new CustomEvent('viewTicket', { detail: { id: data.id } }));
                        return;
                    }
                }
            } catch (ticketErr) {
                console.log("Primary lookup failed, trying fallback...", ticketErr);
            }

            // 2. Fallback to Customer Search
            const customers = await API.searchCustomers(result.trim());
            if (customers.length === 1) {
                // If exactly one match, go to detail
                import('./customers.js?v=5.8').then(m => m.Customers.loadProfile(customers[0].id));
                return;
            } else if (customers.length > 1) {
                // If multiple matches, show the Clients list with that query
                // We need to switch to Customers screen
                document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                const custNav = document.querySelector('.nav-item[data-screen="customers"]');
                if (custNav) custNav.classList.add('active');
                
                import('./customers.js?v=5.8').then(m => {
                    m.Customers.load();
                    // Small delay to allow load() to render input
                    setTimeout(() => {
                        const input = document.querySelector('#customer-search');
                        if (input) {
                            input.value = result.trim();
                            m.Customers.handleSearch(result.trim());
                        }
                    }, 50);
                });
                return;
            }

            // 3. Fallback to Device Search (IMEI / Serial)
            // (Only for Staff role)
            if (state.user.role === 'staff') {
                const devices = await API.searchDevices(result.trim());
                if (devices.length >= 1 && devices[0].customer) {
                    import('./customers.js?v=5.8').then(m => m.Customers.loadProfile(devices[0].customer.id));
                    return;
                }
            }

            throw new Error(t('scan_no_match'));

        } catch (err) {
            console.error("Lookup failed", err);
            if (errorMsg) {
                errorMsg.textContent = t('scan_no_match');
                errorMsg.style.display = 'block';
            } else {
                 alert(t('scan_no_match') + ': ' + result);
            }
        } finally {
            // Restore title only if we are still on the same screen context (simple check)
            if (ui.screenTitle.textContent === t('inv_loading')) {
                // We likely didn't navigate away, so restore title
                const isStaff = state.user.role === 'staff';
                ui.screenTitle.textContent = isStaff ? t('scan_lookup') : t('scan_title');
            }
        }
    }
};
