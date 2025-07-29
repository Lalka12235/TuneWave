// frontend/rooms.js

// --- Вспомогательные функции для UI ---
const responseMessageDiv = document.getElementById('response-message');
const apiResponseDiv = document.getElementById('api-response');
const jwtTokenSpan = document.getElementById('jwt-token');
const roomsListDiv = document.getElementById('rooms-list'); // Для всех комнат
const myRoomsListDiv = document.getElementById('my-rooms-list'); // Для моих комнат
const spotifySearchResultsDiv = document.getElementById('spotify-search-results'); // Для результатов поиска Spotify

// Элементы модального окна для пароля
const joinRoomPasswordModal = document.getElementById('join-room-password-modal');
const modalRoomNameSpan = document.getElementById('modal-room-name');
const modalRoomPasswordInput = document.getElementById('modal-room-password');
const confirmJoinButton = document.getElementById('confirm-join-button');
const joinModalCloseButton = joinRoomPasswordModal.querySelector('.close-button');

// Элементы модального окна для участников
const membersModal = document.getElementById('members-modal');
const membersModalRoomNameSpan = document.getElementById('members-modal-room-name');
const membersListDisplay = document.getElementById('members-list-display');
const membersModalCloseButton = membersModal.querySelector('.members-close-button');

let currentRoomToJoinId = null; // Для хранения ID комнаты, к которой пытаемся присоединиться

function displayMessage(message, isError = false) {
    responseMessageDiv.textContent = message;
    responseMessageDiv.style.backgroundColor = isError ? '#f8d7da' : '#d4edda';
    responseMessageDiv.style.color = isError ? '#721c24' : '#155724';
}

function displayApiResponse(data) {
    apiResponseDiv.textContent = JSON.stringify(data, null, 2);
    apiResponseDiv.style.backgroundColor = '#f0f0f0';
    apiResponseDiv.style.color = '#000';
}

function getAuthToken() {
    return localStorage.getItem('jwt_token');
}

function clearForms() {
    document.getElementById('create-room-form').reset();
    document.getElementById('get-room-form').reset();
    document.getElementById('update-room-form').reset();
    document.getElementById('delete-room-form').reset();
    document.getElementById('spotify-search-form').reset(); // Очищаем форму поиска Spotify
    // Скрываем поля пароля
    document.getElementById('create-password-group').style.display = 'none';
    document.getElementById('update-password-group').style.display = 'none';
    document.getElementById('create-is-private').checked = false;
    document.getElementById('update-is-private').checked = false;
}

// --- Функции взаимодействия с API ---

const BASE_URL = 'http://127.0.0.1:8000'; // Убедитесь, что это правильный адрес вашего бэкенда

let isFetchingRooms = false; // Флаг для предотвращения множественных одновременных вызовов fetchRooms

async function fetchRooms(targetDiv = roomsListDiv) {
    console.log(`--- fetchRooms START for ${targetDiv.id} ---`);
    if (isFetchingRooms) {
        console.log('fetchRooms already in progress, skipping.');
        return;
    }

    isFetchingRooms = true;
    
    try {
        displayMessage('Загрузка списка комнат...');
        const response = await fetch(`${BASE_URL}/rooms/`);
        const data = await response.json();

        if (!response.ok) {
            console.error('API Error in fetchRooms:', data);
            throw new Error(data.detail || 'Ошибка при получении комнат');
        }

        targetDiv.innerHTML = ''; // Очищаем список перед обновлением
        if (data.length === 0) {
            targetDiv.innerHTML = '<p>Пока нет доступных комнат.</p>';
        } else {
            data.forEach(room => {
                try {
                    const roomItem = document.createElement('div');
                    roomItem.className = 'room-item';
                    roomItem.innerHTML = `
                        <strong>${room.name}</strong>
                        <p>ID: ${room.id}</p>
                        <p>Макс. участников: ${room.max_members}</p>
                        <p>Приватная: ${room.is_private ? 'Да' : 'Нет'}</p>
                        <p>Владелец ID: ${room.owner_id}</p>
                        <p>Создана: ${new Date(room.created_at).toLocaleString()}</p>
                        <p>Сейчас играет: ${room.current_track_id || 'Ничего'}</p>
                        <p>Позиция: ${room.current_track_position_ms || '0'} мс</p>
                        <p>Воспроизведение: ${room.is_playing ? 'Да' : 'Нет'}</p>
                        <div class="room-actions">
                            <button class="get-btn" data-room-id="${room.id}">Получить</button>
                            <button class="update-btn" data-room-id="${room.id}" data-room-name="${room.name}">Обновить</button>
                            <button class="delete-btn" data-room-id="${room.id}">Удалить</button>
                            <button class="join-btn" data-room-id="${room.id}" data-room-name="${room.name}" data-is-private="${room.is_private}">Присоединиться</button>
                            <button class="leave-btn" data-room-id="${room.id}">Выйти</button>
                            <button class="members-btn" data-room-id="${room.id}" data-room-name="${room.name}">Участники</button>
                        </div>
                    `;
                    targetDiv.appendChild(roomItem);
                } catch (renderError) {
                    console.error('Error rendering room item:', room, renderError);
                }
            });

            // Добавляем обработчики событий для кнопок в списке
            targetDiv.querySelectorAll('.get-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    document.getElementById('get-room-id').value = e.target.dataset.roomId;
                    document.getElementById('get-room-name').value = '';
                    displayMessage(`ID комнаты подставлен в форму "Получить по ID". Нажмите кнопку.`);
                });
            });
            targetDiv.querySelectorAll('.update-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    document.getElementById('update-room-id').value = e.target.dataset.roomId;
                    displayMessage(`ID комнаты ${e.target.dataset.roomName} подставлен в форму обновления.`);
                });
            });
            targetDiv.querySelectorAll('.delete-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    document.getElementById('delete-room-id').value = e.target.dataset.roomId;
                    displayMessage(`ID комнаты подставлен в форму удаления. Нажмите "Удалить Комнату" для подтверждения.`);
                });
            });

            // Новые обработчики для кнопок членства
            targetDiv.querySelectorAll('.join-btn').forEach(button => {
                button.addEventListener('click', handleJoinRoomClick);
            });
            targetDiv.querySelectorAll('.leave-btn').forEach(button => {
                button.addEventListener('click', handleLeaveRoomClick);
            });
            targetDiv.querySelectorAll('.members-btn').forEach(button => {
                button.addEventListener('click', handleViewMembersClick);
            });
        }
        displayMessage('Список комнат загружен.');
    } catch (error) {
        displayMessage(`Ошибка загрузки комнат: ${error.message}`, true);
        console.error('Global Error in fetchRooms:', error);
    } finally {
        isFetchingRooms = false;
        console.log('--- fetchRooms END ---');
    }
}

async function fetchMyRooms() {
    console.log('--- fetchMyRooms START ---');
    const token = getAuthToken();
    if (!token) {
        displayMessage('Вы не авторизованы. Невозможно получить список ваших комнат.', true);
        myRoomsListDiv.innerHTML = '<p>Пожалуйста, войдите, чтобы увидеть ваши комнаты.</p>';
        return;
    }

    try {
        displayMessage('Загрузка списка ваших комнат...');
        const response = await fetch(`${BASE_URL}/rooms/my-rooms`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Ошибка при получении ваших комнат');
        }

        myRoomsListDiv.innerHTML = '';
        if (data.length === 0) {
            myRoomsListDiv.innerHTML = '<p>Вы пока не состоите ни в одной комнате.</p>';
        } else {
            data.forEach(room => {
                const roomItem = document.createElement('div');
                roomItem.className = 'room-item';
                roomItem.innerHTML = `
                    <strong>${room.name}</strong>
                    <p>ID: ${room.id}</p>
                    <p>Макс. участников: ${room.max_members}</p>
                    <p>Приватная: ${room.is_private ? 'Да' : 'Нет'}</p>
                    <p>Владелец ID: ${room.owner_id}</p>
                    <p>Создана: ${new Date(room.created_at).toLocaleString()}</p>
                    <p>Сейчас играет: ${room.current_track_id || 'Ничего'}</p>
                    <p>Позиция: ${room.current_track_position_ms || '0'} мс</p>
                    <p>Воспроизведение: ${room.is_playing ? 'Да' : 'Нет'}</p>
                    <div class="room-actions">
                        <button class="get-btn" data-room-id="${room.id}">Получить</button>
                        <button class="leave-btn" data-room-id="${room.id}">Выйти</button>
                        <button class="members-btn" data-room-id="${room.id}" data-room-name="${room.name}">Участники</button>
                    </div>
                `;
                myRoomsListDiv.appendChild(roomItem);
            });

            // Добавляем обработчики событий для кнопок в списке "Мои Комнаты"
            myRoomsListDiv.querySelectorAll('.get-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    document.getElementById('get-room-id').value = e.target.dataset.roomId;
                    document.getElementById('get-room-name').value = '';
                    displayMessage(`ID комнаты подставлен в форму "Получить по ID". Нажмите кнопку.`);
                });
            });
            myRoomsListDiv.querySelectorAll('.leave-btn').forEach(button => {
                button.addEventListener('click', handleLeaveRoomClick);
            });
            myRoomsListDiv.querySelectorAll('.members-btn').forEach(button => {
                button.addEventListener('click', handleViewMembersClick);
            });
        }
        displayMessage('Список ваших комнат загружен.');
    } catch (error) {
        displayMessage(`Ошибка загрузки ваших комнат: ${error.message}`, true);
        console.error('Ошибка загрузки ваших комнат:', error);
    }
    console.log('--- fetchMyRooms END ---');
}


async function createRoom(event) {
    event.preventDefault();

    const token = getAuthToken();
    if (!token) {
        displayMessage('Вы не авторизованы. Пожалуйста, войдите.', true);
        return;
    }

    const name = document.getElementById('create-name').value;
    const maxMembers = parseInt(document.getElementById('create-max-members').value, 10);
    const isPrivate = document.getElementById('create-is-private').checked;
    const password = document.getElementById('create-password').value;

    const roomData = {
        name,
        max_members: maxMembers,
        is_private: isPrivate,
    };

    if (isPrivate) {
        if (!password) {
            displayMessage('Для приватной комнаты требуется пароль.', true);
            return;
        }
        roomData.password = password;
    } else {
        if (password) {
            displayMessage('Пароль не может быть установлен для не приватной комнаты.', true);
            return;
        }
    }

    try {
        displayMessage('Создание комнаты...');
        const response = await fetch(`${BASE_URL}/rooms/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(roomData)
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Ошибка при создании комнаты');
        }

        displayMessage(`Комната "${data.name}" успешно создана! ID: ${data.id}`);
        displayApiResponse(data);
        clearForms();
        fetchRooms(); // Обновляем список всех комнат
        fetchMyRooms(); // Обновляем список моих комнат
    } catch (error) {
        displayMessage(`Ошибка создания комнаты: ${error.message}`, true);
        console.error('Ошибка создания комнаты:', error);
    }
}

async function getRoomById(event) {
    event.preventDefault();
    const roomId = document.getElementById('get-room-id').value;
    if (!roomId) {
        displayMessage('Пожалуйста, введите ID комнаты.', true);
        return;
    }

    try {
        displayMessage(`Получение комнаты по ID: ${roomId}...`);
        const response = await fetch(`${BASE_URL}/rooms/${roomId}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Ошибка при получении комнаты по ID');
        }

        displayMessage(`Комната "${data.name}" найдена.`);
        displayApiResponse(data);
    } catch (error) {
        displayMessage(`Ошибка получения комнаты по ID: ${error.message}`, true);
        console.error('Ошибка получения комнаты по ID:', error);
    }
}

async function getRoomByName(event) {
    event.preventDefault();
    const roomName = document.getElementById('get-room-name').value;
    if (!roomName) {
        displayMessage('Пожалуйста, введите название комнаты.', true);
        return;
    }

    try {
        displayMessage(`Получение комнаты по имени: ${roomName}...`);
        const response = await fetch(`${BASE_URL}/rooms/by-name/?name=${encodeURIComponent(roomName)}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Ошибка при получении комнаты по имени');
        }

        displayMessage(`Комната "${data.name}" найдена.`);
        displayApiResponse(data);
    } catch (error) {
        displayMessage(`Ошибка получения комнаты по имени: ${error.message}`, true);
        console.error('Ошибка получения комнаты по имени:', error);
    }
}

async function updateRoom(event) {
    event.preventDefault();

    const token = getAuthToken();
    if (!token) {
        displayMessage('Вы не авторизованы. Пожалуйста, войдите.', true);
        return;
    }

    const roomId = document.getElementById('update-room-id').value;
    if (!roomId) {
        displayMessage('Пожалуйста, введите ID комнаты для обновления.', true);
        return;
    }

    const updateData = {};
    const name = document.getElementById('update-name').value;
    const maxMembers = document.getElementById('update-max-members').value;
    const isPrivateChecked = document.getElementById('update-is-private').checked;
    const password = document.getElementById('update-password').value;

    if (name) updateData.name = name;
    if (maxMembers) updateData.max_members = parseInt(maxMembers, 10);
    
    updateData.is_private = isPrivateChecked; 

    if (isPrivateChecked) {
        if (password) {
            updateData.password = password;
        } else {
            displayMessage('Для установки приватности комнаты или изменения пароля требуется новый пароль.', true);
            return;
        }
    } else {
        if (password) {
            displayMessage('Пароль не может быть установлен для не приватной комнаты.', true);
            return;
        }
        updateData.password = null;
    }

    if (Object.keys(updateData).length === 0) {
        displayMessage('Нет данных для обновления.', true);
        return;
    }

    try {
        displayMessage(`Обновление комнаты ${roomId}...`);
        const response = await fetch(`${BASE_URL}/rooms/${roomId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(updateData)
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Ошибка при обновлении комнаты');
        }

        displayMessage(`Комната "${data.name}" успешно обновлена!`);
        displayApiResponse(data);
        clearForms();
        fetchRooms(); // Обновляем список всех комнат
        fetchMyRooms(); // Обновляем список моих комнат
    } catch (error) {
        displayMessage(`Ошибка обновления комнаты: ${error.message}`, true);
        console.error('Ошибка обновления комнаты:', error);
    }
}

async function deleteRoom(event) {
    event.preventDefault();

    const token = getAuthToken();
    if (!token) {
        displayMessage('Вы не авторизованы. Пожалуйста, войдите.', true);
        return;
    }

    const roomId = document.getElementById('delete-room-id').value;
    if (!roomId) {
        displayMessage('Пожалуйста, введите ID комнаты для удаления.', true);
        return;
    }

    if (!confirm(`Вы уверены, что хотите удалить комнату с ID: ${roomId}?`)) {
        return;
    }

    try {
        displayMessage(`Удаление комнаты ${roomId}...`);
        const response = await fetch(`${BASE_URL}/rooms/${roomId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Ошибка при удалении комнаты');
        }

        displayMessage(`Комната с ID ${roomId} успешно удалена.`);
        displayApiResponse(data);
        clearForms();
        fetchRooms(); // Обновляем список всех комнат
        fetchMyRooms(); // Обновляем список моих комнат
    } catch (error) {
        displayMessage(`Ошибка удаления комнаты: ${error.message}`, true);
        console.error('Ошибка удаления комнаты:', error);
    }
}

// --- НОВЫЕ ФУНКЦИИ ДЛЯ УПРАВЛЕНИЯ УЧАСТНИКАМИ ---

function handleJoinRoomClick(event) {
    const roomId = event.target.dataset.roomId;
    const roomName = event.target.dataset.roomName;
    const isPrivate = event.target.dataset.isPrivate === 'true';

    currentRoomToJoinId = roomId;

    if (isPrivate) {
        modalRoomNameSpan.textContent = roomName;
        modalRoomPasswordInput.value = '';
        joinRoomPasswordModal.style.display = 'flex';
    } else {
        joinRoom(roomId, null);
    }
}

async function joinRoom(roomId, password) {
    const token = getAuthToken();
    if (!token) {
        displayMessage('Вы не авторизованы. Пожалуйста, войдите.', true);
        return;
    }

    const requestBody = { password: password }; 

    try {
        displayMessage(`Присоединение к комнате ${roomId}...`);
        const response = await fetch(`${BASE_URL}/rooms/${roomId}/join`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(requestBody)
        });
        const data = await response.json();

        if (!response.ok) {
            let errorMessage = data.detail || 'Ошибка при присоединении к комнате';
            if (Array.isArray(data.detail) && data.detail.length > 0 && data.detail[0].msg) {
                errorMessage = data.detail[0].msg;
            }
            throw new Error(errorMessage);
        }

        displayMessage(`Вы успешно присоединились к комнате "${data.name}"!`);
        displayApiResponse(data);
        joinRoomPasswordModal.style.display = 'none';
        fetchRooms();
        fetchMyRooms();
    } catch (error) {
        displayMessage(`Ошибка присоединения к комнате: ${error.message}`, true);
        console.error('Ошибка присоединения к комнате:', error);
    }
}

async function handleLeaveRoomClick(event) {
    const roomId = event.target.dataset.roomId;
    if (!confirm(`Вы уверены, что хотите покинуть комнату с ID: ${roomId}?`)) {
        return;
    }
    leaveRoom(roomId);
}

async function leaveRoom(roomId) {
    const token = getAuthToken();
    if (!token) {
        displayMessage('Вы не авторизованы. Пожалуйста, войдите.', true);
        return;
    }

    try {
        displayMessage(`Покидаю комнату ${roomId}...`);
        const response = await fetch(`${BASE_URL}/rooms/${roomId}/leave`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Ошибка при выходе из комнаты');
        }

        displayMessage(data.detail);
        displayApiResponse(data);
        fetchRooms();
        fetchMyRooms();
    } catch (error) {
        displayMessage(`Ошибка выхода из комнаты: ${error.message}`, true);
        console.error('Ошибка выхода из комнаты:', error);
    }
}

async function handleViewMembersClick(event) {
    const roomId = event.target.dataset.roomId;
    const roomName = event.target.dataset.roomName;

    membersModalRoomNameSpan.textContent = roomName;
    membersListDisplay.innerHTML = '<p>Загрузка участников...</p>';
    membersModal.style.display = 'flex';

    try {
        const response = await fetch(`${BASE_URL}/rooms/${roomId}/members`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Ошибка при получении участников комнаты');
        }

        membersListDisplay.innerHTML = '';
        if (data.length === 0) {
            membersListDisplay.innerHTML = '<p>В этой комнате пока нет участников.</p>';
        } else {
            const ul = document.createElement('ul');
            data.forEach(member => {
                const li = document.createElement('li');
                li.textContent = `Имя: ${member.username || 'Неизвестно'}, ID: ${member.id}`;
                ul.appendChild(li);
            });
            membersListDisplay.appendChild(ul);
        }
    } catch (error) {
        membersListDisplay.innerHTML = `<p style="color: red;">Ошибка загрузки участников: ${error.message}</p>`;
        console.error('Ошибка загрузки участников:', error);
    }
}

// --- НОВЫЕ ФУНКЦИИ SPOTIFY ---

async function searchSpotifyTracks(event) {
    event.preventDefault(); // Предотвращаем перезагрузку страницы

    const token = getAuthToken();
    if (!token) {
        displayMessage('Вы не авторизованы. Пожалуйста, войдите.', true);
        return;
    }

    const query = document.getElementById('spotify-search-query').value;
    if (!query) {
        displayMessage('Пожалуйста, введите поисковый запрос.', true);
        return;
    }

    spotifySearchResultsDiv.innerHTML = '<p>Поиск треков на Spotify...</p>';
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
        console.error('Ошибка поиска треков Spotify:', error);
        spotifySearchResultsDiv.innerHTML = `<p style="color: red;">Ошибка: ${error.message}</p>`;
    }
}

function renderSpotifySearchResults(data) {
    spotifySearchResultsDiv.innerHTML = ''; // Очищаем предыдущие результаты

    if (!data.tracks || !data.tracks.items || data.tracks.items.length === 0) {
        spotifySearchResultsDiv.innerHTML = '<p>По вашему запросу ничего не найдено.</p>';
        return;
    }

    data.tracks.items.forEach(track => {
        const trackItem = document.createElement('div');
        trackItem.className = 'spotify-track-item';

        const imageUrl = track.album.images.length > 0 ? track.album.images[0].url : 'https://placehold.co/60x60/cccccc/333333?text=No+Image';
        const artists = track.artists.map(artist => artist.name).join(', ');

        trackItem.innerHTML = `
            <img src="${imageUrl}" alt="Album Art for ${track.name}" onerror="this.onerror=null;this.src='https://placehold.co/60x60/cccccc/333333?text=No+Image';">
            <div class="spotify-track-info">
                <strong>${track.name}</strong>
                <p>${artists} - ${track.album.name}</p>
            </div>
            <!-- Здесь можно добавить кнопку "Добавить в очередь" -->
        `;
        spotifySearchResultsDiv.appendChild(trackItem);
    });
}


// --- Инициализация и обработчики событий ---
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded fired');

    const token = getAuthToken();
    if (!token) {
        console.log('No token found, redirecting to auth.html');
        window.location.href = 'auth.html';
        return; 
    }
    jwtTokenSpan.textContent = token.substring(0, 30) + '...';
    jwtTokenSpan.title = token;

    document.getElementById('logout-button').addEventListener('click', () => {
        console.log('Logout button clicked');
        localStorage.removeItem('jwt_token');
        window.location.href = 'auth.html';
    });

    // Обработчики для форм и кнопок CRUD комнат
    document.getElementById('create-room-form').addEventListener('submit', createRoom);
    document.getElementById('get-by-id-btn').addEventListener('click', getRoomById);
    document.getElementById('get-by-name-btn').addEventListener('click', getRoomByName);
    document.getElementById('update-room-form').addEventListener('submit', updateRoom);
    document.getElementById('delete-room-form').addEventListener('submit', deleteRoom);
    document.getElementById('refresh-rooms-btn').addEventListener('click', fetchRooms);
    document.getElementById('my-rooms-btn').addEventListener('click', fetchMyRooms);

    // Логика показа/скрытия поля пароля для создания комнаты
    document.getElementById('create-is-private').addEventListener('change', (e) => {
        document.getElementById('create-password-group').style.display = e.target.checked ? 'block' : 'none';
        document.getElementById('create-password').required = e.target.checked;
    });

    // Логика показа/скрытия поля пароля для обновления комнаты
    document.getElementById('update-is-private').addEventListener('change', (e) => {
        document.getElementById('update-password-group').style.display = e.target.checked ? 'block' : 'none';
    });

    // Обработчики для модального окна пароля при присоединении
    joinModalCloseButton.addEventListener('click', () => {
        joinRoomPasswordModal.style.display = 'none';
    });
    window.addEventListener('click', (event) => {
        if (event.target == joinRoomPasswordModal) {
            joinRoomPasswordModal.style.display = 'none';
        }
    });
    confirmJoinButton.addEventListener('click', () => {
        const password = modalRoomPasswordInput.value;
        if (currentRoomToJoinId) {
            joinRoom(currentRoomToJoinId, password);
        }
    });

    // Обработчики для модального окна участников
    membersModalCloseButton.addEventListener('click', () => {
        membersModal.style.display = 'none';
    });
    window.addEventListener('click', (event) => {
        if (event.target == membersModal) {
            membersModal.style.display = 'none';
        }
    });

    // НОВЫЙ ОБРАБОТЧИК ДЛЯ ПОИСКА SPOTIFY
    document.getElementById('spotify-search-form').addEventListener('submit', searchSpotifyTracks);


