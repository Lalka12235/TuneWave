// frontend/app.js

const BASE_URL = 'http://127.0.0.1:8000'; // Убедитесь, что это правильный адрес вашего бэкенда

// Глобальные элементы UI из index.html
const dynamicContentArea = document.getElementById('dynamic-content');
const responseMessageDiv = document.getElementById('response-message');
const apiResponseDiv = document.getElementById('api-response');
const currentUsernameSpan = document.getElementById('current-username');
const logoutButton = document.getElementById('logout-button');

// Глобальные функции для сообщений и API ответов
// Они будут доступны для всех загружаемых скриптов
window.displayMessage = function(message, isError = false) {
    if (responseMessageDiv) {
        responseMessageDiv.textContent = message;
        responseMessageDiv.style.backgroundColor = isError ? '#f8d7da' : '#d4edda';
        responseMessageDiv.style.color = isError ? '#721c24' : '#155724';
    } else {
        console.warn('displayMessage: Элемент response-message не найден.');
    }
};

window.displayApiResponse = function(data) {
    if (apiResponseDiv) {
        apiResponseDiv.textContent = JSON.stringify(data, null, 2);
        apiResponseDiv.style.backgroundColor = '#f0f0f0';
        apiResponseDiv.style.color = '#000';
    } else {
        console.warn('displayApiResponse: Элемент api-response не найден.');
    }
};

window.getAuthToken = function() {
    return localStorage.getItem('jwt_token');
};

// Карта для хранения функций инициализации страниц
const pageInitFunctions = {
    'rooms_content.html': 'initRoomsPage',
    'tracks_content.html': 'initTracksPage',
    // 'profile_content.html': 'initProfilePage', // Если будет
};

// Функция для загрузки контента в dynamic-content-area
async function loadContent(pageUrl) {
    console.log(`app.js: Загрузка контента: ${pageUrl}`);
    try {
        const response = await fetch(pageUrl);
        if (!response.ok) {
            throw new Error(`Не удалось загрузить страницу: ${response.statusText}`);
        }
        const htmlContent = await response.text();
        dynamicContentArea.innerHTML = htmlContent;

        // Удаляем старый скрипт, если он есть
        const oldScript = dynamicContentArea.querySelector('script');
        if (oldScript) {
            console.log(`app.js: Удален старый скрипт: ${oldScript.src}`);
            oldScript.remove(); 
        }

        // Загружаем новый скрипт, если он ассоциирован с этой страницей
        const scriptFileName = pageUrl.replace('_content.html', '.js'); // rooms_content.html -> rooms.js
        const initFunctionName = pageInitFunctions[pageUrl];

        if (scriptFileName && initFunctionName) {
            const script = document.createElement('script');
            script.src = scriptFileName;
            script.onload = () => {
                console.log(`app.js: Скрипт ${scriptFileName} загружен.`);
                if (typeof window[initFunctionName] === 'function') {
                    window[initFunctionName](); // Вызываем функцию инициализации из глобальной области видимости
                    console.log(`app.js: Функция инициализации ${initFunctionName} вызвана.`);
                } else {
                    console.warn(`app.js: Функция инициализации ${initFunctionName} не найдена для ${scriptFileName}.`);
                }
            };
            script.onerror = (e) => {
                console.error(`app.js: Ошибка загрузки скрипта ${scriptFileName}:`, e);
                displayMessage(`Ошибка загрузки скрипта для ${pageUrl}.`, true);
            };
            dynamicContentArea.appendChild(script); 
        } else {
            console.log(`app.js: Нет ассоциированного скрипта для ${pageUrl}.`);
        }
        
        window.displayMessage(`Страница "${pageUrl}" загружена.`);
        window.displayApiResponse({}); // Очищаем ответ API при смене страницы

    } catch (error) {
        window.displayMessage(`Ошибка загрузки контента: ${error.message}`, true);
        console.error('app.js: Ошибка загрузки контента:', error);
        dynamicContentArea.innerHTML = `<p style="color: red;">Не удалось загрузить страницу.</p>`;
    }
}

// Функция для получения информации о текущем пользователе
async function fetchCurrentUser() {
    console.log('app.js: Проверка текущего пользователя.');
    const token = window.getAuthToken();
    if (!token) {
        currentUsernameSpan.textContent = 'Гость';
        console.log('app.js: Токен не найден, перенаправление на auth.html.');
        window.location.href = 'auth.html';
        return;
    }

    try {
        const response = await fetch(`${BASE_URL}/users/me`, { 
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();

        if (response.ok) {
            currentUsernameSpan.textContent = data.username || 'Пользователь';
            console.log(`app.js: Пользователь "${data.username}" успешно загружен.`);
        } else {
            console.error('app.js: Ошибка получения данных пользователя:', data.detail);
            localStorage.removeItem('jwt_token');
            window.location.href = 'auth.html';
            window.displayMessage(data.detail || 'Ошибка получения данных пользователя. Пожалуйста, войдите снова.', true);
        }
    } catch (error) {
        console.error('app.js: Ошибка fetchCurrentUser:', error);
        localStorage.removeItem('jwt_token');
        window.location.href = 'auth.html';
        window.displayMessage(`Ошибка: ${error.message}. Пожалуйста, войдите снова.`, true);
    }
}

// Обработчик выхода
if (logoutButton) {
    logoutButton.addEventListener('click', () => {
        console.log('app.js: Выход из системы.');
        localStorage.removeItem('jwt_token');
        window.location.href = 'auth.html';
    });
} else {
    console.warn('app.js: Кнопка выхода не найдена.');
}


// Обработчики навигационных ссылок
document.getElementById('nav-rooms').addEventListener('click', (e) => {
    e.preventDefault();
    loadContent(e.target.dataset.target);
});
document.getElementById('nav-tracks').addEventListener('click', (e) => {
    e.preventDefault();
    loadContent(e.target.dataset.target);
});
document.getElementById('nav-profile').addEventListener('click', (e) => {
    e.preventDefault();
    // Пока что profile_content.html не существует, можно загрузить заглушку
    dynamicContentArea.innerHTML = '<h2>Раздел "Профиль" в разработке!</h2><p>Здесь вы сможете управлять своими данными и настройками.</p>';
    window.displayMessage('Раздел "Профиль" загружен.');
    window.displayApiResponse({});
});


// Инициализация приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    console.log('app.js: DOMContentLoaded - Инициализация приложения.');
    fetchCurrentUser(); // Проверяем пользователя при загрузке
    loadContent('rooms_content.html'); // Загружаем раздел "Комнаты" по умолчанию
});