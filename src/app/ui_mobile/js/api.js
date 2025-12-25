import { state } from './state.js?v=5.8';
import { t } from './i18n.js?v=5.8';

export const API = {
    baseUrl: '/api',

    async request(endpoint, method = 'GET', body = null) {
        const headers = {
            'Content-Type': 'application/json',
        };

        // Add user identification if available
        const savedUser = sessionStorage.getItem('msa_user');
        if (savedUser) {
            const user = JSON.parse(savedUser);
            headers['X-User-ID'] = user.user.id;
            headers['X-User-Role'] = user.role;
        }

        const options = {
            method,
            headers
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, options);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || t('err_general'));
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    // Financial
    getFinancialSummary(days = 30) {
        return this.request(`/financial/summary?days=${days}`);
    },

    getTransactions(limit = 50, skip = 0, type = null) {
        let url = `/financial/transactions?limit=${limit}&skip=${skip}`;
        if (type) url += `&type=${type}`;
        return this.request(url);
    },

    addTransaction(data) {
        return this.request('/financial/transactions', 'POST', data);
    },

    deleteTransaction(id) {
        return this.request(`/financial/transactions/${id}`, 'DELETE');
    },

    getExpenseCategories(type) {
        return this.request(`/financial/categories?type=${type}`);
    },

    login(username, password) {
        return this.request('/login', 'POST', { username, password });
    },

    verifyPairing(pin) {
        return this.request('/verify-pairing', 'POST', { pin });
    },

    getStats() {
        return this.request('/stats/summary');
    },

    getWeeklyStats() {
        return this.request('/stats/weekly');
    },

    async getTickets(techId = null, mode = 'all', limit = 20, skip = 0) {
        const params = new URLSearchParams();
        if (techId) params.append('tech_id', techId);
        if (mode) params.append('mode', mode);
        
        // Pagination
        params.append('limit', limit);
        params.append('skip', skip);

        return this.request(`/tickets/?${params.toString()}`);
    },

    createTicket(data) {
        return this.request('/tickets/', 'POST', data);
    },

    createTicketComposite(data) {
        return this.request('/tickets/composite', 'POST', data);
    },

    getBrands() {
        return this.request('/metadata/brands');
    },

    getErrors() {
        return this.request('/metadata/errors');
    },

    getCategories() {
        return this.request('/metadata/categories');
    },

    getSuppliers() {
        return this.request('/metadata/suppliers');
    },

    printTicket(ticketId) {
        return this.request(`/tickets/${ticketId}/print`, 'POST');
    },

    createCustomer(data) {
        return this.request('/customers/', 'POST', data);
    },

    createDevice(customerId, data) {
        return this.request(`/customers/${customerId}/devices`, 'POST', data);
    },

    searchCustomers(query) {
        return this.request(`/customers/search?q=${encodeURIComponent(query)}`);
    },

    getCustomerDevices(customerId) {
        return this.request(`/customers/${customerId}/devices`);
    },

    getTechnicians() {
        return this.request('/technicians/');
    },

    getTicketDetail(id) {
        return this.request(`/tickets/${id}`);
    },

    lookupTicket(query) {
        return this.request(`/tickets/lookup/${encodeURIComponent(query)}`);
    },

    updateStatus(id, data) {
        return this.request(`/tickets/${id}/status`, 'PATCH', data);
    },

    getTicketParts(id) {
        return this.request(`/tickets/${id}/parts`);
    },

    addTicketPart(id, data) {
        return this.request(`/tickets/${id}/parts`, 'POST', data);
    },

    removeTicketPart(id, itemId) {
        return this.request(`/tickets/${id}/parts/${itemId}`, 'DELETE');
    },

    getTicketHistory(id) {
        return this.request(`/tickets/${id}/history`);
    },

    searchInventory(query, categoryId = null, supplierId = null, limit = 20, skip = 0) {
        const params = new URLSearchParams();
        if (query) params.append('q', query);
        if (categoryId) params.append('category_id', categoryId);
        if (supplierId) params.append('supplier_id', supplierId);
        
        params.append('limit', limit);
        params.append('skip', skip);
        
        const queryString = params.toString();
        const url = `/inventory/search${queryString ? `?${queryString}` : ''}`;
        return this.request(url);
    },

    getCustomers(limit = 20, skip = 0) {
        return this.request(`/customers/?limit=${limit}&skip=${skip}`);
    },

    getCustomerDetail(id) {
        return this.request(`/customers/${id}`);
    },

    updateCustomer(id, data) {
        return this.request(`/customers/${id}`, 'PATCH', data);
    },

    searchDevices(query) {
        return this.request(`/devices/search?q=${encodeURIComponent(query)}`);
    },

    getInvoices(limit = 20, skip = 0) {
        return this.request(`/invoices/?limit=${limit}&skip=${skip}`);
    },

    async createInvoiceFromTicket(ticketId, data = null) {
        return this.request(`/invoices/from-ticket/${ticketId}`, 'POST', data);
    },

    getInvoiceDetail(id) {
        return this.request(`/invoices/${id}`);
    },

    printInvoice(id) {
        return this.request(`/invoices/${id}/print`, 'POST');
    },

    async addPayment(invoiceId, data) {
        return this.request(`/invoices/${invoiceId}/payments`, 'POST', data);
    },

    async uploadPhoto(ticketId, file, type = 'general') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('photo_type', type);

        const response = await fetch(`${this.baseUrl}/tickets/${ticketId}/photos`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || t('err_upload_photo'));
        }

        return response.json();
    },

    // Tech Features
    startLabor(ticketId) {
        return this.request(`/tickets/${ticketId}/labor/start`, 'POST');
    },

    stopLabor(ticketId) {
        return this.request(`/tickets/${ticketId}/labor/stop`, 'POST');
    },

    getActiveTimer(ticketId) {
        return this.request(`/tickets/${ticketId}/labor/active`);
    },

    saveDiagnostics(ticketId, results, notes) {
        return this.request(`/tickets/${ticketId}/diagnostics`, 'POST', { results, technician_notes: notes });
    },

    getTechStats(techId) {
        return this.request(`/stats/tech/${techId}`);
    },

    getTechnicianPerformance(techId) {
        return this.request(`/technicians/${techId}/performance`);
    }
};
