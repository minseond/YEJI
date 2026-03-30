import axios from 'axios';
import { AUTH_EXPIRED_EVENT } from '../utils/authEvents';

const api = axios.create({
    baseURL: '/', // Proxy will handle the rest
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add token if exists
api.interceptors.request.use(
    (config) => {
        // Check for token (supporting both key names if needed, but sticking to 'accessToken' as per roadmap)
        const token = localStorage.getItem('accessToken');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
            // console.log("Token attached to request");
        } else {
            // console.warn("No access token found in localStorage");
        }
        return config;
    },
    (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor for global error handling
api.interceptors.response.use(
    (response) => {
        // Detect if we got HTML instead of JSON (usually means redirect to login/session expired)
        const contentType = response.headers['content-type'] || '';
        if (contentType.includes('text/html') && typeof response.data === 'string' && response.data.includes('<!DOCTYPE html')) {
            console.error('Session Expired or Protected Resource: Received HTML login page instead of JSON.');

            // Clear identity from local storage
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('userId');

            // Notify application
            window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT));

            return Promise.reject({
                response: {
                    status: 401,
                    statusText: 'Session Expired (HTML Redirect Detected)',
                    data: { message: '로그인 세션이 만료되었습니다. 다시 로그인해주세요.' }
                }
            });
        }

        return response;
    },
    (error) => {
        console.error('API Response Error:', error.response?.status, error.config?.url, error.response?.data || error.message);

        // Handle 401 Unauthorized globally
        if (error.response?.status === 401) {
            console.warn("Unauthorized! Clearing session and notifying App...");

            // Clear identity from local storage
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('userId');

            // Notify application
            window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT));
        }

        return Promise.reject(error);
    }
);

export default api;
