import { state, ui } from '../state.js?v=5.8';
import { API } from '../api.js?v=5.8';

export const Auth = {
    async login(username, password) {
        if (ui.loginError) ui.loginError.textContent = '';
        try {
            const data = await API.login(username, password);
            state.user = data;
            sessionStorage.setItem('msa_user', JSON.stringify(data));
            return data;
        } catch (error) {
            ui.loginError.textContent = error.message;
            throw error;
        }
    },

    logout() {
        state.user = null;
        sessionStorage.removeItem('msa_user');
    }
};
