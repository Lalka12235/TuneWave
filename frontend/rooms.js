// frontend/rooms.js

// --- Вспомогательные функции для UI ---
const responseMessageDiv = document.getElementById('response-message');
const apiResponseDiv = document.getElementById('api-response');
const jwtTokenSpan = document.getElementById('jwt-token');
const roomsListDiv = document.getElementById('rooms-list');

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
    // Скрываем поля пароля
    document.getElementById('create-password-group').style.display = 'none';
    document.getElementById('update-password-group').style.display = 'none';
    document.getElementById('create-is-private').checked = false;
    document.getElementById('update-is-private').checked = false;
}

// --- Функции взаимодействия с API ---

const BASE_URL = 'http://127.0.0.1:8000'; // Убедитесь, что это правильный адрес вашего бэкенда

let isFetchingRooms = false; // Флаг для предотвращения множественных одновременных вызовов fetchRooms

async function fetchRooms() {
    console.log('--- fetchRooms START ---');
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

        roomsListDiv.innerHTML = '';
        if (data.length === 0) {
            roomsListDiv.innerHTML = '<p>Пока нет доступных комнат.</p>';
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
                        </div>
                    `;
                    roomsListDiv.appendChild(roomItem);
                } catch (renderError) {
                    console.error('Error rendering room item:', room, renderError);
                }
            });

            roomsListDiv.querySelectorAll('.get-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    document.getElementById('get-room-id').value = e.target.dataset.roomId;
                    document.getElementById('get-room-name').value = '';
                    displayMessage(`ID комнаты подставлен в форму "Получить по ID". Нажмите кнопку.`);
                });
            });
            roomsListDiv.querySelectorAll('.update-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    document.getElementById('update-room-id').value = e.target.dataset.roomId;
                    displayMessage(`ID комнаты ${e.target.dataset.roomName} подставлен в форму обновления.`);
                });
            });
            roomsListDiv.querySelectorAll('.delete-btn').forEach(button => {
                button.addEventListener('click', (e) => {
                    document.getElementById('delete-room-id').value = e.target.dataset.roomId;
                    displayMessage(`ID комнаты подставлен в форму удаления. Нажмите "Удалить Комнату" для подтверждения.`);
                });
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

async function createRoom(event) {
    event.preventDefault();

    const token = getAuthToken();
    if (!token) {
        displayMessage('Вы не авторизованы. Пожалуйста, войдите.', true);
        return;
    }

    const name = document.getElementById('create-name').value;
    // УДАЛЕНО: const description = document.getElementById('create-description').value;
    const maxMembers = parseInt(document.getElementById('create-max-members').value, 10);
    const isPrivate = document.getElementById('create-is-private').checked;
    const password = document.getElementById('create-password').value;

    const roomData = {
        name,
        // УДАЛЕНО: description: description || null,
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
        fetchRooms();
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
    // УДАЛЕНО: const description = document.getElementById('update-description').value;
    const maxMembers = document.getElementById('update-max-members').value;
    const isPrivateChecked = document.getElementById('update-is-private').checked;
    const password = document.getElementById('update-password').value;

    if (name) updateData.name = name;
    // УДАЛЕНО: if (description) updateData.description = description;
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
        fetchRooms();
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
        fetchRooms();
    } catch (error) {
        displayMessage(`Ошибка удаления комнаты: ${error.message}`, true);
        console.error('Ошибка удаления комнаты:', error);
    }
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

    document.getElementById('create-room-form').addEventListener('submit', createRoom);
    document.getElementById('get-by-id-btn').addEventListener('click', getRoomById);
    document.getElementById('get-by-name-btn').addEventListener('click', getRoomByName);
    document.getElementById('update-room-form').addEventListener('submit', updateRoom);
    document.getElementById('delete-room-form').addEventListener('submit', deleteRoom);
    document.getElementById('refresh-rooms-btn').addEventListener('click', fetchRooms);

    document.getElementById('create-is-private').addEventListener('change', (e) => {
        document.getElementById('create-password-group').style.display = e.target.checked ? 'block' : 'none';
        document.getElementById('create-password').required = e.target.checked;
    });

    document.getElementById('update-is-private').addEventListener('change', (e) => {
        document.getElementById('update-password-group').style.display = e.target.checked ? 'block' : 'none';
    });

    // Инициализация: загружаем список комнат при загрузке страницы
    fetchRooms();
    console.log('DOMContentLoaded finished');
});