// frontend/auth.js

const BASE_URL = 'http://127.0.0.1:8000'; // Убедитесь, что это правильный адрес вашего бэкенда

const googleLoginButton = document.getElementById('google-login-btn');
const spotifyLoginButton = document.getElementById('spotify-login-btn');
const messageDiv = document.getElementById('message');

let config = {}; // Объект для хранения конфигурации

// Функция для отображения сообщений (локальная для auth.js)
function displayMessage(message, isError = false) {
    if (messageDiv) {
        messageDiv.textContent = message;
        messageDiv.style.backgroundColor = isError ? '#f8d7da' : '#d4edda';
        messageDiv.style.color = isError ? '#721c24' : '#155724';
        messageDiv.style.display = 'block';
    } else {
        console.warn("auth.js: Элемент 'message' не найден в DOM. Сообщение: " + message);
    }
}

// Функция для загрузки конфигурации с бэкенда
async function loadConfig() {
    try {
        displayMessage("Загрузка конфигурации...");
        const response = await fetch(`${BASE_URL}/auth/config`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        config = await response.json();
        displayMessage("Конфигурация загружена. Выберите способ входа.");
        if (googleLoginButton) googleLoginButton.style.display = 'block';
        if (spotifyLoginButton) spotifyLoginButton.style.display = 'block';
    } catch (error) {
        displayMessage(`Ошибка загрузки конфигурации: ${error.message}`, true);
        console.error("auth.js: Ошибка загрузки конфигурации:", error);
    }
}

// Функция для входа через Google
function loginWithGoogle() {
    if (!config.google_client_id || !config.google_redirect_uri || !config.google_scopes) {
        displayMessage("Ошибка: Конфигурация Google не загружена или неполна.", true);
        return;
    }

    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
                    `response_type=code&` +
                    `client_id=${config.google_client_id}&` +
                    `redirect_uri=${config.google_redirect_uri}&` +
                    `scope=${encodeURIComponent(config.google_scopes)}&` +
                    `access_type=offline&` +
                    `prompt=consent`;
    
    window.location.href = authUrl;
}

// Функция для входа через Spotify
function loginWithSpotify() {
    if (!config.spotify_client_id || !config.spotify_redirect_uri || !config.spotify_scopes) {
        displayMessage("Ошибка: Конфигурация Spotify не загружена или неполна.", true);
        return;
    }

    const scopes = encodeURIComponent(config.spotify_scopes);

    const authUrl = `https://accounts.spotify.com/authorize?` +
                    `response_type=code&` +
                    `client_id=${config.spotify_client_id}&` +
                    `scope=${scopes}&` +
                    `redirect_uri=${config.spotify_redirect_uri}&` +
                    `show_dialog=true`;
    
    window.location.href = authUrl;
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    console.log('auth.js: DOMContentLoaded - Инициализация страницы авторизации.');

    if (googleLoginButton) {
        googleLoginButton.addEventListener('click', loginWithGoogle);
        console.log('auth.js: Обработчик клика для Google прикреплен.');
    } else {
        console.warn('auth.js: Кнопка Google не найдена.');
    }

    if (spotifyLoginButton) {
        spotifyLoginButton.addEventListener('click', loginWithSpotify);
        console.log('auth.js: Обработчик клика для Spotify прикреплен.');
    } else {
        console.warn('auth.js: Кнопка Spotify не найдена.');
    }
    
    const urlParams = new URLSearchParams(window.location.search);
    const accessToken = urlParams.get('access_token');
    const error = urlParams.get('error');

    const storedToken = localStorage.getItem('jwt_token');

    if (accessToken) {
        localStorage.setItem('jwt_token', accessToken);
        displayMessage("Авторизация успешна! Перенаправление на главную страницу...");
        window.history.replaceState({}, document.title, window.location.pathname); 
        window.location.href = 'index.html'; // МГНОВЕННОЕ ПЕРЕНАПРАВЛЕНИЕ
    } else if (error) {
        displayMessage(`Ошибка авторизации: ${error}`, true);
        console.error("auth.js: Ошибка авторизации:", error);
        window.history.replaceState({}, document.title, window.location.pathname);
        loadConfig();
    } else if (storedToken) {
        displayMessage("Вы уже авторизованы. Перенаправление на главную страницу...");
        window.location.href = 'index.html'; 
    } else {
        loadConfig();
    }
});