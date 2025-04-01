**“TuneWave” – веб-приложение для совместного прослушивания музыки, обсуждения и знакомств по музыкальным интересам.**

**TuneWave – это платформа, где пользователи могут находить единомышленников по музыкальным вкусам, слушать треки вместе в реальном времени, обсуждать музыку и открывать новые жанры. Алгоритм рекомендаций подбирает комнаты с музыкой и людьми, а также предлагает интересные треки на основе предпочтений.**

**Технологический стек**

**Backend:**
 **• Язык: Python**
 **• Фреймворк: FastAPI**
 **• База данных: PostgreSQL (основная), MongoDB (для истории прослушиваний, рекомендаций)**
 **• ORM: SQLAlchemy**
 **• Migration: Alembic**
 **• Аутентификация: OAuth2 (Google/Spotify/Yandex Music в перспективе)**

**DevOps:**
 **• Контейнеризация: Docker**
 **• CI/CD: GitLab**
 **• Хостинг: https://www.heroku.com**

**Frontend:**
 **• Язык: TypeScript/JavaScript**
 **• Фреймворк: React**
 **• Стилизация: Tailwind CSS**

**Дополнительно (в перспективе)**
 **• WebSockets – для синхронизации прослушивания и чатов**
 **• Redis – для кеширования (необязательно на старте)**

**Минимальный функционал для теста (MVP):**
 1. Регистрация и авторизация (OAuth через Google/Spotify/Yandex Music в будущем).
 2. Создание комнат (публичные и приватные).
 3. Подключение к комнате (прослушивание музыки в реальном времени).
 4. Добавление треков в очередь (через ссылки).
 5. Чат в комнате (основной способ общения).
 6. Рекомендации комнат на основе жанров и истории прослушиваний.
 7. История прослушиваний (в профиле пользователя).
