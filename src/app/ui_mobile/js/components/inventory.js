import { state, ui } from '../state.js?v=5.8';
import { API } from '../api.js?v=5.8';
import { t } from '../i18n.js?v=5.8';

const InventoryState = {
    query: '',
    categoryId: null,
    supplierId: null,
    categories: [],
    suppliers: [],
    // Pagination
    parts: [],
    page: 0,
    limit: 20,
    hasMore: true,
    isLoadingMore: false
};

export const Inventory = {
    async load() {
        ui.screenTitle.textContent = t('nav_stock') + ' Search';
        ui.content.innerHTML = `
            <div class="search-container">
                <input type="text" id="inventory-search" placeholder="${t('inv_search_ph_parts')}">
                
                <div style="display: flex; gap: 8px; margin-top: 12px; overflow-x: auto; padding-bottom: 8px;">
                    <select id="filter-category" class="filter-select" style="flex: 1; min-width: 120px;">
                        <option value="">${t('inv_all_cats')}</option>
                    </select>
                </div>

                <div id="inventory-results" style="margin-top: 16px;"></div>
            </div>
        `;

        // Load Metadata
        try {
            const categories = await API.getCategories();
            
            InventoryState.categories = categories;
            
            const catSelect = ui.content.querySelector('#filter-category');

            catSelect.innerHTML += categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');

            // Initial load of all stock
            // Reset state
            InventoryState.query = '';
            InventoryState.page = 0;
            InventoryState.parts = [];
            InventoryState.hasMore = true;
            
            this.handleSearch(true);

            // Bind Events
            const searchInput = ui.content.querySelector('#inventory-search');
            searchInput.addEventListener('input', this.debounce((e) => {
                InventoryState.query = e.target.value;
                this.resetAndSearch();
            }, 300));

            catSelect.addEventListener('change', (e) => {
                InventoryState.categoryId = e.target.value || null;
                this.resetAndSearch();
            });

        } catch (error) {
            console.error('Metadata load failure', error);
        }
    },
    
    resetAndSearch() {
        InventoryState.page = 0;
        InventoryState.hasMore = true;
        InventoryState.parts = [];
        this.handleSearch(true);
    },

    async handleSearch(initial = false) {
        const resultsDiv = ui.content.querySelector('#inventory-results');
        const { query, categoryId } = InventoryState;

        if (InventoryState.isLoadingMore && !initial) return;
        InventoryState.isLoadingMore = true;
        
        const skip = InventoryState.page * InventoryState.limit;

        try {
            if (initial) {
                resultsDiv.innerHTML = '<div class="loading" style="padding: 20px;">Refreshing stock...</div>';
            } else {
                const btn = document.getElementById('btn-load-more-stock');
                if (btn) btn.textContent = t('loading_wait');
            }
            
            const parts = await API.searchInventory(query, categoryId, null, InventoryState.limit, skip);
            
            if (initial) {
                InventoryState.parts = parts;
            } else {
                InventoryState.parts = [...InventoryState.parts, ...parts];
            }
            
            InventoryState.hasMore = parts.length === InventoryState.limit;
            InventoryState.page++;
            
            this.renderList();

        } catch (err) {
            resultsDiv.innerHTML = `<div class="error">Search failed: ${err.message}</div>`;
        } finally {
            InventoryState.isLoadingMore = false;
        }
    },
    
    renderList() {
        const resultsDiv = ui.content.querySelector('#inventory-results');
        if (!resultsDiv) return;
        
        if (InventoryState.parts.length === 0) {
             resultsDiv.innerHTML = '<div class="empty-state">No parts found matching filters</div>';
             return;
        }

        let html = InventoryState.parts.map(p => `
            <div class="card">
                <div class="card-title">${p.name}</div>
                <div class="card-sub">SKU: ${p.sku} | Stock: <span style="font-weight: bold; color: ${p.stock < 5 ? '#ef4444' : '#10b981'}">${p.stock}</span></div>
                <div class="card-id" style="margin-top: 8px; font-size: 14px; color: #F59E0B;">${p.price.toLocaleString()} Ks</div>
            </div>
        `).join('');
        
        // Add Load More
        if (InventoryState.hasMore) {
             html += `
                <div style="padding: 20px; text-align: center;">
                    <button id="btn-load-more-stock" class="btn-secondary" style="width: 100%; padding: 12px;">${t('btn_load_more')}</button>
                </div>
            `;
        }
        
        resultsDiv.innerHTML = html;
        
        if (InventoryState.hasMore) {
            const btn = resultsDiv.querySelector('#btn-load-more-stock');
            if (btn) {
                btn.addEventListener('click', () => {
                    this.handleSearch(false);
                });
            }
        }
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};
