from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from med_backend.auth.schemas import User
from med_backend.auth.services import get_current_active_user
from med_backend.db.dependencies import get_db_session
from med_backend.forms import crud, services
from med_backend.forms.schemas import (
    BaseForm,
    CreateFormField,
    Form,
    FormAssigment,
    FormField,
    ListForm,
)
from med_backend.forms.services import assign_form
from med_backend.users.services import get_current_active_manager

router = APIRouter()


@router.get("/all", response_model=list[ListForm])
async def get_all_forms(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_manager),
    session: AsyncSession = Depends(get_db_session),
):
    forms = await crud.get_forms(session, skip, limit)
    return forms


@router.get("/list", response_model=list[ListForm])
async def get_all_forms(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    forms = await crud.filter_form_assigment(session, current_user.id, skip, limit)
    return forms


@router.post("/create", response_model=Form)
async def create_form_view(
    data: BaseForm,
    current_user: User = Depends(get_current_active_manager),
    session: AsyncSession = Depends(get_db_session),
) -> Form:
    db_form = await crud.create_form(session, data, current_user.id)
    form = await services.get_full_form(session, db_form.id)
    return form


@router.get("/{form_id}", response_model=Form)
async def get_form(
    form_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
) -> Form:
    form = await services.get_full_form(session, form_id)
    return form


@router.get("/{form_id}/fields", response_model=List[FormField])
async def create_form_field_view(
    form_id: int,
    current_user: User = Depends(get_current_active_manager),
    session: AsyncSession = Depends(get_db_session),
):
    form = await services.get_form(session, form_id)
    if form.user.id != current_user.id:
        raise HTTPException(
            status_code=401,
            detail="You are not allowed to access this form",
        )
    fields = await services.get_questions(session, form_id)
    return fields


@router.post("/{form_id}/fields", response_model=FormField)
async def create_form_field_view(
    form_id: int,
    data: CreateFormField,
    current_user: User = Depends(get_current_active_manager),
    session: AsyncSession = Depends(get_db_session),
):
    field = await crud.create_form_field(session, data, current_user.id, form_id)
    return field


@router.post("/{form_id}/assign", status_code=status.HTTP_201_CREATED)
async def create_assigment_view(
    form_id: int,
    data: FormAssigment,
    current_user: User = Depends(get_current_active_manager),
    session: AsyncSession = Depends(get_db_session),
):
    form = await services.get_form(session, form_id)
    if form.user.id != current_user.id:
        raise HTTPException(
            status_code=401,
            detail="You are not allowed to access this form",
        )
    await assign_form(session, data, form_id)
    return {"message": "created"}