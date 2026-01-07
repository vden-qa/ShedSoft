from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from shed_soft_user.api.schemas import (
    AddNote,
    AddNoteWithUserId,
    AddUser,
    NoteResponse,
    SUserId,
)
from shed_soft_user.config import settings
from shed_soft_user.dao.dao import NotesDAO, UsersDAO
from shed_soft_user.services.auth_dep import get_current_user, get_keycloak_client
from shed_soft_user.services.dao_dep import (
    get_session_with_commit,
    get_session_without_commit,
)
from shed_soft_user.services.keycloak_client import KeycloakClient

router = APIRouter(prefix="/api", tags=["API"])


@router.get("/login/callback", include_in_schema=False)
async def login_callback(
    code: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    session: AsyncSession = Depends(get_session_with_commit),
    keycloak: KeycloakClient = Depends(get_keycloak_client),
) -> RedirectResponse:
    """
    Обрабатывает callback после авторизации в Keycloak.
    Получает токен, информацию о пользователе, сохраняет пользователя в БД (если нужно)
    и устанавливает cookie с токенами. Обрабатывает ошибки от Keycloak.
    """
    if error:
        logger.error(f"Keycloak error: {error}, description: {error_description}")
        raise HTTPException(status_code=401, detail="Authorization code is required")

    if not code:
        raise HTTPException(status_code=401, detail="Authorization code is required")

    try:
        # Получение токенов от Keycloak
        token_data = await keycloak.get_tokens(code)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        id_token = token_data.get("id_token")

        if not access_token:
            raise HTTPException(status_code=401, detail="Токен доступа не найден")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token не найден")
        if not id_token:
            raise HTTPException(status_code=401, detail="ID token не найден")

        # Получение информации о пользователе
        user_info = await keycloak.get_user_info(access_token)
        user_id = user_info.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="ID пользователя не найден")

        # Проверка существования пользователя, создание нового при необходимости
        users_dao = UsersDAO(session)
        user = await users_dao.find_one_or_none_by_id(user_id)
        if not user and isinstance(user_info, dict):
            user_data = {
                "id": user_info.get("sub"),
                "email": user_info.get("email", ""),
                "email_verified": user_info.get("email_verified", False),
                "name": user_info.get("name", ""),
                "preferred_username": user_info.get("preferred_username", ""),
                "given_name": user_info.get("given_name", ""),
                "family_name": user_info.get("family_name", ""),
            }
            await users_dao.add(AddUser(**user_data))

        # Установка cookie с токенами и редирект
        response = RedirectResponse(url="/protected")
        is_secure = settings.is_production
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            path="/",
            max_age=token_data.get("expires_in", 3600),
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            path="/",
            max_age=token_data.get("refresh_expires_in", 2592000),
        )
        response.set_cookie(
            key="id_token",
            value=id_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            path="/",
            max_age=token_data.get("expires_in", 3600),
        )
        logger.info(f"User {user_id} logged in successfully")
        return response

    except Exception as e:
        logger.error(f"Ошибка обработки callback'а логина: {str(e)}")
        raise HTTPException(status_code=401, detail="Ошибка авторизации")


@router.get("/logout", include_in_schema=False)
async def logout(request: Request):
    id_token = request.cookies.get("id_token")
    params = {
        "client_id": settings.CLIENT_ID_USER,
        "post_logout_redirect_uri": settings.BASE_URL_USER,
    }
    if id_token:
        params["id_token_hint"] = id_token

    keycloak_logout_url = f"{settings.logout_url}?{urlencode(params)}"
    response = RedirectResponse(url=keycloak_logout_url)
    is_secure = settings.is_production
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/",
    )
    response.delete_cookie(
        key="id_token",
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/",
    )
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/",
    )
    return response


@router.post("/notes")
async def add_note(
    note: AddNote,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session_with_commit),
):
    try:
        user_id = user.get("sub")
        if not user_id:
            logger.error(f"Отсутствует user_id в информации о пользователе")
            raise HTTPException(status_code=401, detail="Отсутствует идентификатор пользователя")
        
        notes_dao = NotesDAO(session)
        result = await notes_dao.add(AddNoteWithUserId(user_id=user_id, **note.model_dump()))
        logger.info(f"Заметка успешно добавлена")
        
        return {"status": "ok", "message": "Note added successfully", "note": note}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Ошибка БД при добавлении заметки: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении заметки")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при добавлении заметки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/notes")
async def get_notes(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session_without_commit),
):
    try:
        notes_dao = NotesDAO(session)
        notes = await notes_dao.find_all(SUserId(user_id=user["sub"]))
        notes_response = [NoteResponse.model_validate(note) for note in notes]
        return {"status": "ok", "notes": notes_response}
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при получении заметок: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении заметок")


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: int,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session_with_commit),
):
    try:
        notes_dao = NotesDAO(session)
        note = await notes_dao.find_one_or_none_by_id(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Заметка не найдена")
        if note.user_id != user["sub"]:
            raise HTTPException(
                status_code=403, detail="У вас нет прав на удаление этой заметки"
            )
        await session.delete(note)
        # Коммит выполняется автоматически через get_session_with_commit
        return {"status": "ok", "message": "Заметка успешно удалена"}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при удалении заметки: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении заметки")


@router.put("/notes/{note_id}")
async def update_note(
    note_id: int,
    note: AddNote,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session_with_commit),
):
    try:
        notes_dao = NotesDAO(session)
        existing_note = await notes_dao.find_one_or_none_by_id(note_id)
        if not existing_note:
            raise HTTPException(status_code=404, detail="Заметка не найдена")
        if existing_note.user_id != user["sub"]:
            raise HTTPException(
                status_code=403, detail="У вас нет прав на обновление этой заметки"
            )
        existing_note.title = note.title
        existing_note.content = note.content
        # Коммит выполняется автоматически через get_session_with_commit
        return {"status": "ok", "message": "Заметка успешно обновлена", "note": note}
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при обновлении заметки: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении заметки")
