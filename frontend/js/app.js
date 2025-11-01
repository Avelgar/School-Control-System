import { API_BASE_URL } from './config.js';

const { createApp } = Vue;

const app = createApp({
    data() {
        return {
            showLogin: false,
            isLoading: false,
            loginData: {
                login: '',
                password: ''
            }
        };
    },
    async mounted() {
        await this.checkAuthStatus();
    },
    methods: {
        async checkAuthStatus() {
            const token = localStorage.getItem('authToken');
            
            if (token) {
                try {
                    const response = await fetch(`${API_BASE_URL}/auth/me`, {
                        method: 'GET',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });
                    
                    if (response.ok) {
                        window.location.href = '/main-page';
                    } else {
                        this.clearAuthData();
                    }
                } catch (error) {
                    console.error('Auth check error:', error);
                    this.clearAuthData();
                }
            }
        },

        closeModal() {
            this.showLogin = false;
        },

        async handleLoginSubmit() {
            if (!this.validateLoginForm()) {
                return;
            }
            
            this.isLoading = true;

            try {
                const userData = {
                    login: this.loginData.login,
                    password: this.loginData.password
                };
                
                const response = await fetch(`${API_BASE_URL}/auth/login`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(userData)
                });
                
                if (response.ok) {
                    const data = await response.json();
                    
                    localStorage.setItem('authToken', data.access_token);
                    
                    this.closeModal();
                    this.resetForm();
                    
                    setTimeout(() => {
                        window.location.href = '/main-page';
                    }, 500);
                    
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Ошибка входа');
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('Ошибка соединения с сервером');
            } finally {
                this.isLoading = false;
            }
        },

        validateLoginForm() {
            if (!this.loginData.login) {
                alert('Введите логин');
                return false;
            }
            
            if (!this.loginData.password) {
                alert('Введите пароль');
                return false;
            }
            
            return true;
        },

        resetForm() {
            this.loginData = {
                login: '',
                password: ''
            };
        },

        clearAuthData() {
            localStorage.removeItem('authToken');
        }
    }
});

app.mount('#app');