// frontend/rooms.js

// Глобальные функции и переменные, определенные в app.js, доступны здесь
// const BASE_URL;
// const displayMessage;
// const displayApiResponse;
// const getAuthToken;

console.log('rooms.js: Скрипт rooms.js загружен.');

// Элементы UI, специфичные для rooms_content.html
const roomsListDiv = document.getElementById('rooms-list'); // Для всех комнат
const myRoomsListDiv = document.getElementById('my-rooms-list'); // Для моих комнат

// Элементы модального окна для пароля
const joinRoomPasswordModal = document.getElementById('join-room-password-modal');
const modalRoomNameSpan = document.getElementById('modal-room-name');
const modalRoomPasswordInput = document.getElementById('modal-room-password');
const confirmJoinButton = joinRoomPasswordModal ? document.getElementById('confirm-join-button') : null; // Проверка на null
const joinModalCloseButton = joinRoomPasswordModal ? joinRoomPasswordModal.querySelector('.close-button') : null; // Проверка на null

// Элементы модального окна для участников
const membersModal = document.getElementById('members-modal');
const membersModalRoomNameSpan = document.getElementById('members-modal-room-name');
const membersListDisplay = document.getElementById('members-list-display');
const membersModalCloseButton = membersModal ? membersModal.querySelector('.members-close-button') : null; // Проверка на null

let currentRoomToJoinId = null; // Для хранения ID комнаты, к которой пытаемся присоединиться
let isFetchingRooms = false; // Флаг для предотвращения множественных одновременных вызовов fetchRooms

function clearForms() {
    const createRoomForm = document.getElementById('create-room-form');
    const getRoomForm = document.getElementById('get-room-form');
    const updateRoomForm = document.getElementById('update-room-form');
    const deleteRoomForm = document.getElementById('delete-room-form');

    if (createRoomForm) createRoomForm.reset();
    if (getRoomForm) getRoomForm.reset();
    if (updateRoomForm) updateRoomForm.reset();
    if (deleteRoomForm) deleteRoomForm.reset();
    
    // Скрываем поля пароля
    const createPasswordGroup = document.getElementById('create-password-group');
    const updatePasswordGroup = document.getElementById('update-password-group');
    const createIsPrivate = document.getElementById('create-is-private');
    const updateIsPrivate = document.getElementById('update-is-private');

    if (createPasswordGroup) createPasswordGroup.style.display = 'none';
    if (updatePasswordGroup) updatePasswordGroup.style.display = 'none';
    if (createIsPrivate) createIsPrivate.checked = false;
    if (updateIsPrivate) updateIsPrivate.checked = false;
}

async function fetchRooms(targetDiv = roomsListDiv) {
    console.log(`rooms.js: fetchRooms START for ${targetDiv.id}`);
    if (isFetchingRooms) {
        console.log('rooms.js: fetchRooms уже в процессе, пропуск.');
        return;
    }

    isFetchingRooms = true;
    
    try {
        displayMessage('Загрузка списка комнат...');
        const response = await fetch(`${BASE_URL}/rooms/`);
        const data = await response.json();

        if (!response.ok) {
            console.error('rooms.js: API Error in fetchRooms:', data);
            throw new Error(data.detail || 'Ошибка при получении комнат');
        }

        if (targetDiv) { // Проверка на существование targetDiv
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
                        console.error('rooms.js: Ошибка рендеринга элемента комнаты:', room, renderError);
                    }
                });

                // Добавляем обработчики событий для кнопок в списке
                targetDiv.querySelectorAll('.get-btn').forEach(button => {
                    button.addEventListener('click', (e) => {
                        const getRoomIdInput = document.getElementById('get-room-id');
                        const getRoomNameInput = document.getElementById('get-room-name');
                        if (getRoomIdInput) getRoomIdInput.value = e.target.dataset.roomId;
                        if (getRoomNameInput) getRoomNameInput.value = '';
                        displayMessage(`ID комнаты подставлен в форму "Получить по ID". Нажмите кнопку.`);
                    });
                });
                targetDiv.querySelectorAll('.update-btn').forEach(button => {
                    button.addEventListener('click', (e) => {
                        const updateRoomIdInput = document.getElementById('update-room-id');
                        if (updateRoomIdInput) updateRoomIdInput.value = e.target.dataset.roomId;
                        displayMessage(`ID комнаты ${e.target.dataset.roomName} подставлен в форму обновления.`);
                    });
                });
                targetDiv.querySelectorAll('.delete-btn').forEach(button => {
                    button.addEventListener('click', (e) => {
                        const deleteRoomIdInput = document.getElementById('delete-room-id');
                        if (deleteRoomIdInput) deleteRoomIdInput.value = e.target.dataset.roomId;
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
        } else {
            console.error('rooms.js: Target div for rooms list not found:', targetDiv.id);
            displayMessage('Ошибка: Не удалось найти элемент для отображения списка комнат.', true);
        }
    } catch (error) {
        displayMessage(`Ошибка загрузки комнат: ${error.message}`, true);
        console.error('rooms.js: Глобальная ошибка в fetchRooms:', error);
    } finally {
        isFetchingRooms = false;
        console.log('rooms.js: fetchRooms END');
    }
}

async function fetchMyRooms() {
    console.log('rooms.js: fetchMyRooms START');
    const token = getAuthToken();
    if (!token) {
        displayMessage('Вы не авторизованы. Невозможно получить список ваших комнат.', true);
        if (myRoomsListDiv) myRoomsListDiv.innerHTML = '<p>Пожалуйста, войдите, чтобы увидеть ваши комнаты.</p>';
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

        if (myRoomsListDiv) { // Проверка на существование myRoomsListDiv
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
                        const getRoomIdInput = document.getElementById('get-room-id');
                        const getRoomNameInput = document.getElementById('get-room-name');
                        if (getRoomIdInput) getRoomIdInput.value = e.target.dataset.roomId;
                        if (getRoomNameInput) getRoomNameInput.value = '';
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
        } else {
            console.error('rooms.js: My rooms list div not found.');
            displayMessage('Ошибка: Не удалось найти элемент для отображения ваших комнат.', true);
        }
    } catch (error) {
        displayMessage(`Ошибка загрузки ваших комнат: ${error.message}`, true);
        console.error('rooms.js: Ошибка загрузки ваших комнат:', error);
    }
    console.log('rooms.js: fetchMyRooms END');
}

async function createRoom(event) {
    event.preventDefault();
    console.log('rooms.js: createRoom called.');

    const token = getAuthToken();
    if (!token) {
        displayMessage('Вы не авторизованы. Пожалуйста, войдите.', true);
        return;
    }

    const nameInput = document.getElementById('create-name');
    const maxMembersInput = document.getElementById('create-max-members');
    const isPrivateCheckbox = document.getElementById('create-is-private');
    const passwordInput = document.getElementById('create-password');

    const name = nameInput ? nameInput.value : '';
    const maxMembers = maxMembersInput ? parseInt(maxMembersInput.value, 10) : 0;
    const isPrivate = isPrivateCheckbox ? isPrivateCheckbox.checked : false;
    const password = passwordInput ? passwordInput.value : '';

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
        console.error('rooms.js: Ошибка создания комнаты:', error);
    }
}

async function getRoomById(event) {
    event.preventDefault();
    console.log('rooms.js: getRoomById called.');
    const roomIdInput = document.getElementById('get-room-id');
    const roomId = roomIdInput ? roomIdInput.value : '';
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
    }
    catch (error) {
        displayMessage(`Ошибка получения комнаты по ID: ${error.message}`, true);
        console.error('rooms.js: Ошибка получения комнаты по ID:', error);
    }
}

async function getRoomByName(event) {
    event.preventDefault();
    console.log('rooms.js: getRoomByName called.');
    const roomNameInput = document.getElementById('get-room-name');
    const roomName = roomNameInput ? roomNameInput.value : '';
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
        console.error('rooms.js: Ошибка получения комнаты по имени:', error);
    }
}

async function updateRoom(event) {
    event.preventDefault();
    console.log('rooms.js: updateRoom called.');

    const token = getAuthToken();
    if (!token) {
        displayMessage('Вы не авторизованы. Пожалуйста, войдите.', true);
        return;
    }

    const roomIdInput = document.getElementById('update-room-id');
    const roomId = roomIdInput ? roomIdInput.value : '';
    if (!roomId) {
        displayMessage('Пожалуйста, введите ID комнаты для обновления.', true);
        return;
    }

    const updateData = {};
    const nameInput = document.getElementById('update-name');
    const maxMembersInput = document.getElementById('update-max-members');
    const isPrivateCheckbox = document.getElementById('update-is-private');
    const passwordInput = document.getElementById('update-password');

    const name = nameInput ? nameInput.value : '';
    const maxMembers = maxMembersInput ? maxMembersInput.value : '';
    const isPrivateChecked = isPrivateCheckbox ? isPrivateCheckbox.checked : false;
    const password = passwordInput ? passwordInput.value : '';

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
        console.error('rooms.js: Ошибка обновления комнаты:', error);
    }
}

async function deleteRoom(event) {
    event.preventDefault();
    console.log('rooms.js: deleteRoom called.');

    const token = getAuthToken();
    if (!token) {
        displayMessage('Вы не авторизованы. Пожалуйста, войдите.', true);
        return;
    }

    const roomIdInput = document.getElementById('delete-room-id');
    const roomId = roomIdInput ? roomIdInput.value : '';
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
        console.error('rooms.js: Ошибка удаления комнаты:', error);
    }
}

// --- ФУНКЦИИ ДЛЯ УПРАВЛЕНИЯ УЧАСТНИКАМИ ---

function handleJoinRoomClick(event) {
    console.log('rooms.js: handleJoinRoomClick called.');
    const roomId = event.target.dataset.roomId;
    const roomName = event.target.dataset.roomName;
    const isPrivate = event.target.dataset.isPrivate === 'true';

    currentRoomToJoinId = roomId;

    if (isPrivate) {
        if (modalRoomNameSpan) modalRoomNameSpan.textContent = roomName;
        if (modalRoomPasswordInput) modalRoomPasswordInput.value = '';
        if (joinRoomPasswordModal) joinRoomPasswordModal.style.display = 'flex';
    } else {
        joinRoom(roomId, null);
    }
}

async function joinRoom(roomId, password) {
    console.log('rooms.js: joinRoom called.');
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
        if (joinRoomPasswordModal) joinRoomPasswordModal.style.display = 'none';
        fetchRooms();
        fetchMyRooms();
    } catch (error) {
        displayMessage(`Ошибка присоединения к комнате: ${error.message}`, true);
        console.error('rooms.js: Ошибка присоединения к комнате:', error);
    }
}

async function handleLeaveRoomClick(event) {
    console.log('rooms.js: handleLeaveRoomClick called.');
    const roomId = event.target.dataset.roomId;
    if (!confirm(`Вы уверены, что хотите покинуть комнату с ID: ${roomId}?`)) {
        return;
    }
    leaveRoom(roomId);
}

async function leaveRoom(roomId) {
    console.log('rooms.js: leaveRoom called.');
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
        console.error('rooms.js: Ошибка выхода из комнаты:', error);
    }
}

async function handleViewMembersClick(event) {
    console.log('rooms.js: handleViewMembersClick called.');
    const roomId = event.target.dataset.roomId;
    const roomName = event.target.dataset.roomName;

    if (membersModalRoomNameSpan) membersModalRoomNameSpan.textContent = roomName;
    if (membersListDisplay) membersListDisplay.innerHTML = '<p>Загрузка участников...</p>';
    if (membersModal) membersModal.style.display = 'flex';

    try {
        const response = await fetch(`${BASE_URL}/rooms/${roomId}/members`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Ошибка при получении участников комнаты');
        }

        if (membersListDisplay) { // Проверка на существование membersListDisplay
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
        }
    } catch (error) {
        if (membersListDisplay) membersListDisplay.innerHTML = `<p style="color: red;">Ошибка загрузки участников: ${error.message}</p>`;
        console.error('rooms.js: Ошибка загрузки участников:', error);
    }
}

// Функция инициализации rooms.js - вызывается из app.js после загрузки rooms_content.html
window.initRoomsPage = function() {
    console.log('rooms.js: initRoomsPage вызвана. Прикрепление обработчиков событий.');

    // Обработчики для форм и кнопок CRUD комнат
    const createRoomForm = document.getElementById('create-room-form');
    if (createRoomForm) createRoomForm.addEventListener('submit', createRoom); else console.warn('rooms.js: create-room-form не найден.');

    const getByIdBtn = document.getElementById('get-by-id-btn');
    if (getByIdBtn) getByIdBtn.addEventListener('click', getRoomById); else console.warn('rooms.js: get-by-id-btn не найден.');

    const getByNameBtn = document.getElementById('get-by-name-btn');
    if (getByNameBtn) getByNameBtn.addEventListener('click', getRoomByName); else console.warn('rooms.js: get-by-name-btn не найден.');

    const updateRoomForm = document.getElementById('update-room-form');
    if (updateRoomForm) updateRoomForm.addEventListener('submit', updateRoom); else console.warn('rooms.js: update-room-form не найден.');

    const deleteRoomForm = document.getElementById('delete-room-form');
    if (deleteRoomForm) deleteRoomForm.addEventListener('submit', deleteRoom); else console.warn('rooms.js: delete-room-form не найден.');

    const refreshRoomsBtn = document.getElementById('refresh-rooms-btn');
    if (refreshRoomsBtn) refreshRoomsBtn.addEventListener('click', fetchRooms); else console.warn('rooms.js: refresh-rooms-btn не найден.');

    const myRoomsBtn = document.getElementById('my-rooms-btn');
    if (myRoomsBtn) myRoomsBtn.addEventListener('click', fetchMyRooms); else console.warn('rooms.js: my-rooms-btn не найден.');

    // Логика показа/скрытия поля пароля для создания комнаты
    const createIsPrivateCheckbox = document.getElementById('create-is-private');
    const createPasswordGroup = document.getElementById('create-password-group');
    const createPasswordInput = document.getElementById('create-password');
    if (createIsPrivateCheckbox && createPasswordGroup && createPasswordInput) {
        createIsPrivateCheckbox.addEventListener('change', (e) => {
            createPasswordGroup.style.display = e.target.checked ? 'block' : 'none';
            createPasswordInput.required = e.target.checked;
        });
    } else {
        console.warn('rooms.js: Элементы для приватной комнаты (создание) не найдены.');
    }

    // Логика показа/скрытия поля пароля для обновления комнаты
    const updateIsPrivateCheckbox = document.getElementById('update-is-private');
    const updatePasswordGroup = document.getElementById('update-password-group');
    if (updateIsPrivateCheckbox && updatePasswordGroup) {
        updateIsPrivateCheckbox.addEventListener('change', (e) => {
            updatePasswordGroup.style.display = e.target.checked ? 'block' : 'none';
        });
    } else {
        console.warn('rooms.js: Элементы для приватной комнаты (обновление) не найдены.');
    }

    // Обработчики для модального окна пароля при присоединении
    if (joinModalCloseButton) joinModalCloseButton.addEventListener('click', () => {
        if (joinRoomPasswordModal) joinRoomPasswordModal.style.display = 'none';
    }); else console.warn('rooms.js: Кнопка закрытия модального окна пароля не найдена.');

    if (confirmJoinButton) confirmJoinButton.addEventListener('click', () => {
        const password = modalRoomPasswordInput ? modalRoomPasswordInput.value : '';
        if (currentRoomToJoinId) {
            joinRoom(currentRoomToJoinId, password);
        }
    }); else console.warn('rooms.js: Кнопка подтверждения присоединения не найдена.');

    // Обработчики для модального окна участников
    if (membersModalCloseButton) membersModalCloseButton.addEventListener('click', () => {
        if (membersModal) membersModal.style.display = 'none';
    }); else console.warn('rooms.js: Кнопка закрытия модального окна участников не найдена.');

    // Закрытие модальных окон по клику вне их
    window.addEventListener('click', (event) => {
        if (event.target == joinRoomPasswordModal) {
            if (joinRoomPasswordModal) joinRoomPasswordModal.style.display = 'none';
        }
        if (event.target == membersModal) {
            if (membersModal) membersModal.style.display = 'none';
        }
    });

    // Инициализация: загружаем список всех комнат при загрузке страницы
    fetchRooms();
    // Также загружаем список моих комнат при загрузке страницы
    fetchMyRooms(); 
};