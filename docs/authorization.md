# Авторизация

## Развёртывание Keycloak (docker-compose)

Ниже — пошаговая инструкция по развёртыванию Keycloak в составе docker-compose, сформированная на основе файла docker-compose.yml в репозитории.

Ключевые компоненты:
- Postgres: контейнер базы данных (postgres:17.4) с томом для хранения данных.
- Keycloak: официальный образ quay.io/keycloak/keycloak:26.3.2, настроенный на использование Postgres.

Переменные окружения (хранятся в файле .env.example в репозитории; при развёртывании заведите локальный .env на основе примера):

См. .env.example для актуального списка и значений по умолчанию. В репозитории присутствует шаблон .env.example с необходимыми переменными, например:
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_DB
- POSTGRES_PORT
- KEYCLOAK_HTTP_PORT
- KC_BOOTSTRAP_ADMIN_USERNAME
- KC_BOOTSTRAP_ADMIN_PASSWORD

Рекомендуется скопировать .env.example в .env и изменить значения для окружения перед запуском (не коммитить .env в VCS).
Тома и сети:
- pgdata — для данных Postgres (/var/lib/postgresql/data)
- keycloak_data — для данных Keycloak (/opt/keycloak/data)
- Рекомендуется использовать отдельную docker-сеть (например, shedsoft_network) для изоляции сервисов.

Healthchecks и порядок старта:
- Postgres содержит healthcheck с pg_isready; Keycloak зависит от Postgres и ожидает его готовности (depends_on с condition: service_healthy).
- Keycloak также имеет HTTP healthcheck, проверяющий доступность корневого URL.

Пример простого запуска:
1. Подготовьте .env (или экспортируйте переменные окружения):
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=keycloak
   KEYCLOAK_HTTP_PORT=8155
   KC_BOOTSTRAP_ADMIN_USERNAME=admin
   KC_BOOTSTRAP_ADMIN_PASSWORD=secret

2. Запустите стек:
   docker compose up -d

3. Проверьте состояние сервисов:
   docker compose ps
   docker compose logs -f keycloak

4. Доступ к консоли администратора (пример):
   http://localhost:8155/
   учётные данные: KC_BOOTSTRAP_ADMIN_USERNAME / KC_BOOTSTRAP_ADMIN_PASSWORD

Импорт realm и автоматизация:
- Для автоматического импорта realm можно смонтировать папку с экспортом в /opt/keycloak/data/import и включить автозагрузку в конфигурации Keycloak (раскомментируйте соответствующую volume в docker-compose.yml).
- Экспортируйте и храните конфигурацию realm в репозитории конфигураций (config/) для возможности быстрого развёртывания и резервного копирования.

Дополнительные рекомендации:
- Для боевого развёртывания обязательно замените стандартные пароли и используйте секреты/систему управления секретами.
- При необходимости добавьте init‑скрипты для создания схемы БД/миграций.
- Для обеспечения корректного порядка старта в CI/CD используйте проверки готовности (wait-for-it или встроенные healthchecks).


