// frontend/tracks.js

// Глобальные функции и переменные, определенные в app.js, доступны здесь
// const BASE_URL;
// const displayMessage;
// const displayApiResponse;
// const getAuthToken;

console.log('tracks.js: Скрипт tracks.js загружен.'); // Лог 1

const spotifySearchResultsDiv = document.getElementById('spotify-search-results');

async function searchSpotifyTracks(event) {
    event.preventDefault(); // КРИТИЧНО: Предотвращаем стандартное поведение формы (перезагрузку страницы)
    console.log('tracks.js: searchSpotifyTracks: Функция вызвана. Предотвращено стандартное поведение формы.'); // Лог 4

    const token = getAuthToken();
    if (!token) {
        displayMessage('Вы не авторизованы. Пожалуйста, войдите.', true);
        return;
    }

    const queryInput = document.getElementById('spotify-search-query');
    const query = queryInput ? queryInput.value : '';
    if (!query) {
        displayMessage('Пожалуйста, введите поисковый запрос.', true);
        return;
    }

    if (spotifySearchResultsDiv) spotifySearchResultsDiv.innerHTML = '<p>Поиск треков на Spotify...</p>';
    displayApiResponse({}); // Очищаем предыдущий ответ API

    try {
        const response = await fetch(`${BASE_URL}/spotify/search/tracks?query=${encodeURIComponent(query)}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();

        if (!response.ok) {
            let errorMessage = data.detail || 'Ошибка при поиске треков Spotify';
            if (Array.isArray(data.detail) && data.detail.length > 0 && data.detail[0].msg) {
                errorMessage = data.detail[0].msg;
            }
            throw new Error(errorMessage);
        }

        displayMessage('Результаты поиска Spotify загружены.');
        displayApiResponse(data); // Показываем полный ответ API

        renderSpotifySearchResults(data); // Рендерим результаты в отдельной секции

    } catch (error) {
        displayMessage(`Ошибка поиска треков Spotify: ${error.message}`, true);
        console.error('tracks.js: Ошибка поиска треков Spotify:', error);
        if (spotifySearchResultsDiv) spotifySearchResultsDiv.innerHTML = `<p style="color: red;">Ошибка: ${error.message}</p>`;
    }
}

function renderSpotifySearchResults(data) {
    if (spotifySearchResultsDiv) spotifySearchResultsDiv.innerHTML = ''; // Очищаем предыдущие результаты

    if (!data.tracks || !data.tracks.items || data.tracks.items.length === 0) {
        if (spotifySearchResultsDiv) spotifySearchResultsDiv.innerHTML = '<p>По вашему запросу ничего не найдено.</p>';
        return;
    }

    data.tracks.items.forEach(track => {
        const trackItem = document.createElement('div');
        trackItem.className = 'spotify-track-item';

        const imageUrl = track.album.images.length > 0 ? track.album.images[0].url : 'https://placehold.co/60x60/cccccc/333333?text=No+Image';
        const artists = track.artists.map(artist => artist.name).join(', ');

        trackItem.innerHTML = `
            <img src="${imageUrl}" alt="Обложка альбома ${track.name}" onerror="this.onerror=null;this.src='https://placehold.co/60x60/cccccc/333333?text=No+Image';">
            <div class="spotify-track-info">
                <strong>${track.name}</strong>
                <p>${artists} - ${track.album.name}</p>
            </div>
            <!-- Здесь можно добавить кнопку "Добавить в очередь" -->
        `;
        if (spotifySearchResultsDiv) spotifySearchResultsDiv.appendChild(trackItem);
    });
}

// Функция инициализации для tracks.js, вызываемая из app.js
window.initTracksPage = function() {
    console.log('tracks.js: initTracksPage: Функция инициализации вызвана.'); // Лог 2

    // Добавляем небольшую задержку, чтобы дать DOM время на полное формирование
    // Это критически важно, так как HTML вставляется динамически.
    setTimeout(() => {
        const spotifySearchForm = document.getElementById('spotify-search-form');
        if (spotifySearchForm) {
            console.log('tracks.js: initTracksPage: Форма spotify-search-form найдена.'); // Лог 3a
            spotifySearchForm.addEventListener('submit', searchSpotifyTracks);
            console.log('tracks.js: initTracksPage: Обработчик события submit прикреплен к spotify-search-form.'); // Лог 3b
        } else {
            console.error('tracks.js: initTracksPage: ОШИБКА! Форма spotify-search-form не найдена в DOM после задержки!'); // Лог 3c
        }
    }, 100); // Увеличена задержка до 100 миллисекунд для большей надежности
};