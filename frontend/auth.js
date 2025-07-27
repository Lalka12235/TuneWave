// frontend/auth.js

let config = {}; // Объект для хранения конфигурации
const responseDiv = document.getElementById('response');
const googleLoginButton = document.getElementById('google-login-button');
const spotifyLoginButton = document.getElementById('spotify-login-button');
const goToRoomsButton = document.getElementById('go-to-rooms-button'); // Новая кнопка

const BASE_URL = 'http://127.0.0.1:8000'; // Убедитесь, что это правильный адрес вашего бэкенда

// Функция для загрузки конфигурации с бэкенда
async function loadConfig() {
    try {
        responseDiv.textContent = "Загрузка конфигурации...";
        const response = await fetch(`${BASE_URL}/auth/config`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        config = await response.json();
        responseDiv.textContent = "Конфигурация загружена. Выберите способ входа.";
        googleLoginButton.style.display = 'flex';
        spotifyLoginButton.style.display = 'flex';
    } catch (error) {
        responseDiv.textContent = `Ошибка загрузки конфигурации: ${error.message}`;
        console.error("Ошибка загрузки конфигурации:", error);
    }
}

// Функция для входа через Google
function loginWithGoogle() {
    if (!config.google_client_id || !config.google_redirect_uri || !config.google_scopes) {
        responseDiv.textContent = "Ошибка: Конфигурация Google не загружена или неполна.";
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
        responseDiv.textContent = "Ошибка: Конфигурация Spotify не загружена или неполна.";
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

// Функция для перехода на страницу комнат
function navigateToRooms() {
    window.location.href = 'rooms.html';
}

// --- Инициализация и обработчики событий ---
document.addEventListener('DOMContentLoaded', () => {
    googleLoginButton.addEventListener('click', loginWithGoogle);
    spotifyLoginButton.addEventListener('click', loginWithSpotify);
    goToRoomsButton.addEventListener('click', navigateToRooms); // Обработчик для новой кнопки

    const urlParams = new URLSearchParams(window.location.search);
    const accessToken = urlParams.get('access_token');
    const error = urlParams.get('error');

    const storedToken = localStorage.getItem('jwt_token'); // Проверяем, есть ли токен в localStorage

    if (accessToken) {
        // Если токен есть в URL (после колбэка), сохраняем его и перенаправляем
        localStorage.setItem('jwt_token', accessToken);
        responseDiv.textContent = "Авторизация успешна! Перенаправление на страницу комнат...";
        window.history.replaceState({}, document.title, window.location.pathname); // Очищаем URL
        setTimeout(navigateToRooms, 1500); // Перенаправляем через 1.5 секунды
    } else if (error) {
        // Если есть ошибка в URL
        responseDiv.textContent = `Ошибка авторизации: ${error}`;
        console.error("Ошибка авторизации:", error);
        window.history.replaceState({}, document.title, window.location.pathname); // Очищаем URL
        loadConfig(); // Загружаем конфиг, чтобы пользователь мог попробовать снова
    } else if (storedToken) {
        // Если токена нет в URL, но он есть в localStorage (пользователь уже авторизован)
        responseDiv.textContent = "Вы уже авторизованы. Можете перейти к комнатам.";
        goToRoomsButton.style.display = 'block'; // Показываем кнопку "Перейти к Комнатам"
        googleLoginButton.style.display = 'none'; // Скрываем кнопки OAuth
        spotifyLoginButton.style.display = 'none';
    } else {
        // Если это первый вход и токена нет нигде
        loadConfig(); // Загружаем конфиг и показываем кнопки OAuth
    }
});