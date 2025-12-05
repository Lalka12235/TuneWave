#TuneWave

**TuneWave is a platform where users can find like-minded music lovers, listen to tracks together in real time, discuss music, and discover new genres. The recommendation algorithm selects rooms with music and people, and suggests interesting tracks based on preferences**

**Technology Stack**

**Backend:**
- **Language: Python**
- **Framework: FastAPI**
- **Database: PostgreSQL (main)**
- **ORM: SQLAlchemy**
- **Migration: Alembic**
- **Authentication: OAuth2 (Google/Spotify)**
- **redis**
- **rabbitmq**
- **nginx**

**DevOps:**
- **Containerization: Docker**
- **CI/CD: GitLab**
- **Hosting: https://www.heroku.com**

**Frontend:**
- **Language: TypeScript/JavaScript**
- **Framework: React**
- **Styling: Tailwind CSS**

**Additional**
- **WebSockets – for synchronizing listening and chats**
- **Redis – for caching**
- **RabbitMQ – for asynchronous task processing (sending email, background Spotify data processing, notifications) and a reliable message queue**

**Minimum functionality for testing (MVP):**
1. Registration and authorization (OAuth via Google/Spotify/).

2. Creating rooms (public and private).

3. Joining a room (listening to music in real time).

4. Adding tracks to the queue.

5. Chat in the room (the main method of communication).
6. Room recommendations based on genres and listening history.
7. Listening history (in the user profile).


# API Docs

---

Here's your API documentation in a uniform style:

## WebSocket Chat

### `GET /ws/chat/{room_id}`

**Description:**
WebSocket endpoint for connecting to a room chat.

**Parameters:**

| Name | Type | Location | Description |
|----------|------|----------------|---------------------------|
| room_id | UUID | path | Unique room ID |
| token | str | query | Authentication token |

**Features:**
- Send and receive messages in real time
- Messages in JSON format, `text` key
- Send messages to all participants
- Notification when a user leaves

---

## User API

### `GET /users/me`

**Description:**
Get the current user's profile.

**Authentication:** Yes (JWT)

**Response:**
`UserResponse` - user profile data.

**Limits:**
10 requests per minute

### `PUT /users/{user_id}`

**Description:**
Update a user's profile.

**Parameters:**

| Name | Type | Description |
|----------|------|---------------------|
| user_id | UUID | User ID |

**Request Body:**
`UserUpdate`

**Response:**
Updated profile `UserResponse`

### `POST /users/me/avatar`

**Description:**
Upload a user's avatar.

**Data Form:**
`avatar_file` (UploadFile)

**Response:**
`UserResponse` with the updated avatar URL

**Limits:**
5 requests per minute

### `GET /users/{user_id}`

**Description:**
Get public user information.

**Parameters:**
`user_id` - UUID

**Response:**
`UserResponse`

**Limits:**
20 requests per minute

---

## Track API

### `GET /track/{spotify_id}`

**Description:**
Get a track by Spotify ID.

**Parameters:**

| Name | Type | Description |
|------------|------|------------------|
| spotify_id | str | Spotify track ID |

**Response:**
`TrackBase` with track information

**Limits:**
15 requests per minute

### `POST /track/`

**Description:**
Create a track based on Spotify data.

**Request Body:**
`TrackCreate`

**Response:**
Created track `TrackCreate`

**Limits:**
10 requests per minute

---

## Favorite Track API

### `GET /favorites/me`

**Description:**
Get the current user's favorite tracks.

**Response:**
`list[FavoriteTrackResponse]`

**Limits:**
15 requests per minute

### `POST /favorites/me`

**Description:**
Add a track to favorites.

**Request Body:**
`FavoriteTrackAdd`

**Response:**
`FavoriteTrackResponse`

**Limits:**
5 requests per minute

### `DELETE /favorites/me/{spotify_id}`

**Description:**
Remove a track from favorites.

**Parameters:**
`spotify_id` - str

**Response:**
Operation Status

**Limits:**
5 requests per minute

### `GET /favorites/{user_id}`

**Description:**
Get a user's favorite tracks.

**Parameters:**
`user_id` - UUID

**Response:**
`list[FavoriteTrackResponse]`

**Limits:**
10 requests per minute

---

## Room API

### Basic Operations

| Method | URL | Description | Requirements |
|-------|--------------------|----------------------------------|------------------------|
| POST | `/rooms/` | Create a room | Authentication |
| PUT | `/rooms/{room_id}` | Update a room | Room owner |
| DELETE | `/rooms/{room_id}` | Delete a room | Room owner |
| POST | `/rooms/{room_id}/join` | Join a room | Authentication |
| POST | `/rooms/{room_id}/leave` | Leave a room | Room member |
| GET | `/rooms/{room_id}/members` | Get members | No |
| GET | `/rooms/by-name/` | Find a room by name | No |
| GET | `/rooms/my-rooms` | Get a user's rooms | Authentication |
| GET | `/rooms/` | Get all rooms | No |
| GET | `/rooms/{room_id}` | Get a room by ID | No |

**Limits:**
10 requests per minute (except creating a room - 5 requests)

### Managing Members

| Method | URL | Description |
|-------|-----------------------------|----------------------------------|
| PUT | `/rooms/{room_id}/members/{user_id}/role` | Change a member's role |
| POST | `/rooms/{room_id}/invite/{user_id}` | Invite a user |

**Requirements:**
Room owner or moderator

**Limits:**
5 requests per minute

### Bans

| Method | URL | Description |
|-------|----------------------------|-------------------------|
| POST | `/rooms/{room_id}/members/{user_id}/ban` | Ban a user |
| DELETE| `/rooms/{room_id}/members/{user_id}/ban` | Unban a user |

**Requirements:**
Room owner

**Limits:**
5 requests per minute

### Track Queue

| Method | URL | Description

### Bans

| Method | URL | Description |
|-------|----------------------------|-------------------------|
| POST | `/rooms/{room_id}/members/{user_id}/ban` | Ban a user |
| DELETE| `/rooms/{room_id}/members/{user_id}/ban` | Unban a user |

**Requirements:**
Room owner

**Limits:**
5 requests per minute

### Track Queue

| Method | URL | Description |
|-------|-----------------------------|---------------------------|
| POST | `/rooms/{room_id}/queue` | Add a track to the queue |
| GET | `/rooms/{room_id}/queue` | Get the track queue |
| DELETE| `/rooms/{room_id}/queue/{association_id}` | Remove a track from the queue |

**Requirements:**
Room owner (for POST/DELETE)

**Limits:**
10 requests per minute

---

## Chat API

### `GET /chat/{room_id}`

**Description:**
Get message history with pagination.

**Parameters:**

| Name | Type | Description |
|------------------|-----------|--------------------------------|
| room_id | UUID | Room ID |
| limit | int | Message limit (required) |
| before_timestamp | datetime | Pagination - get old |

**Response:**
`list[MessageResponse]`

**Limits:**
10 requests per minute

### `POST /chat/{room_id}`

**Description:**
Send a message to the chat.

**Request Body:**
`MessageCreate`

**Response:**
`MessageResponse`

**Limits:**
5 requests per 5 seconds

---

## Friendship API

### Basic Operations

| Method | URL | Description |
|-------|-----------------------------|--------------------------|
| POST | `/friendships/send-request` | Send a friend request |
| PUT | `/friendships/{id}/accept` | Accept the request |
| PUT | `/friendships/{id}/decline` | Decline the request |
| DELETE | `/friendships/{id}` | Delete the friendship |

**Limits:**
5 requests per minute

### Retrieving Data

| Method | URL | Description |
|-------|------------------------------|--------------------------|
| GET | `/friendships/my-friends` | Get friends |
| GET | `/friendships/my-send-requests` | Sent requests |
| GET | `/friendships/my-received-requests` | Received requests |

**Limits:**
15 requests per minute

---

## Notification API

### `GET /notifications/my`

**Description:**
Get user notifications.

**Parameters:**

| Name | Type | Description | Default |
|----------|----------------------|---------|
| limit | int | Notification limit | 10 |
| offset | int | Pagination offset | 0 |

**Response:**
`list[NotificationResponse]`

**Limits:**
10 requests per minute

### `PUT /notifications/{id}/mark-read`

**Description:**
Mark a notification as read.

**Response:**
`NotificationResponse`

**Limits:**
5 requests per minute

### `DELETE /notifications/{id}`

**Description:**
Delete a notification.

**Response:**
Operation status

**Limits:**
5 requests per minute

---

## Ban API

### `GET /ban/my-issued`

**Description:**
Get bans issued by the current user.

**Response:**
`list[BanResponse]`

### `GET /ban/my-received`

**Description:**
Get bans received by the current user.

**Response:**
`list[BanResponse]`

**Limits:**
15 requests per minute

---

## Auth API

### `GET /auth/config`

**Description:**
Get OAuth configurations for the frontend.

**Response:**
`FrontendConfig`

**Limits:**
15 requests per minute

### Google OAuth

| Method | URL | Description |
|-------|-------------------|------------------------------------------|
| GET | `/auth/google/login` | Redirect to Google authorization |
| GET | `/auth/google/callback` | Process callback, issue JWT |

### Spotify OAuth

| Method | URL | Description |
|-------|----------------------|------------------------------------------|
| GET | `/auth/spotify/callback` | Process Spotify callback, issue JWT |

After successful authentication via OAuth, a redirect to the frontend occurs with the JWT token in the URL parameter.
