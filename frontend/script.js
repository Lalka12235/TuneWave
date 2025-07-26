// script.js

let config = {}; // Объект для хранения конфигурации
const responseDiv = document.getElementById('response');
const googleLoginButton = document.getElementById('google-login-button');
const spotifyLoginButton = document.getElementById('spotify-login-button');

// Функция для загрузки конфигурации с бэкенда
async function loadConfig() {
    try {
        const response = await fetch('http://localhost:8000/auth/config'); // Запрос к вашему эндпоинту конфига
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        config = await response.json();
        responseDiv.textContent = "Конфигурация загружена. Выберите способ входа.";
        googleLoginButton.style.display = 'flex'; // Показываем кнопку Google
        spotifyLoginButton.style.display = 'flex'; // Показываем кнопку Spotify
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


// Функция, которая выполняется при загрузке страницы
window.onload = function() {
    const urlParams = new URLSearchParams(window.location.search);
    const accessToken = urlParams.get('access_token');
    const error = urlParams.get('error');

    // ИСПРАВЛЕНО: Проверяем, является ли это колбэком OAuth
    if (accessToken) {
        // Если токен есть, это колбэк. Отображаем токен и не загружаем конфиг.
        responseDiv.textContent = `Успешный логин!\nВаш токен доступа: ${accessToken}\n\n`;
        localStorage.setItem('jwt_token', accessToken); // Сохраняем токен
        // Опционально: очищаем URL после получения токена (для продакшена)
        // window.history.replaceState({}, document.title, window.location.pathname);
    } else if (error) {
        // Если есть ошибка, это тоже колбэк. Отображаем ошибку и не загружаем конфиг.
        responseDiv.textContent = `Ошибка логина: ${error}`;
    } else {
        // Если токена и ошибки в URL нет, это обычная загрузка страницы.
        // Тогда загружаем конфигурацию.
        loadConfig(); 
    }

    // Также проверяем хэш в URL (если токен был передан в хэше, хотя мы сейчас используем параметры запроса)
    if (window.location.hash) {
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        const hashAccessToken = hashParams.get('access_token');
        if (hashAccessToken) {
            responseDiv.textContent = `Успешный логин (из хэша)!\nВаш токен доступа: ${hashAccessToken}\n\n`;
            localStorage.setItem('jwt_token', hashAccessToken); // Сохраняем токен
            // Опционально: очищаем хэш в URL (для продакшена)
            // window.history.replaceState({}, document.title, window.location.pathname + window.location.search);
        }
    }

    console.log("Access Token from URL:", accessToken); // Для отладки
};