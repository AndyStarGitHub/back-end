from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.company import CompanyRepository
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyRead,
    CompanyListResponse,
)


class CompanyService:
    def __init__(self, repo: CompanyRepository | None = None) -> None:
        self.repo = repo or CompanyRepository()

    async def create_company(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
        data: CompanyCreate,
    ) -> CompanyRead:
        """
        Створити компанію. Кожен юзер може створювати багато компаній.
        Owner = current_user.id, visibility за замовчуванням 'hidden'.
        """
        obj = await self.repo.create_one(
            db,
            name=data.name,
            description=data.description,
            visibility="hidden",
            owner_id=current_user.id,
        )
        return CompanyRead.from_orm(obj)

    async def _get_company_or_404(
        self,
        db: AsyncSession,
        company_id: UUID,
    ):
        company = await self.repo.get_by_id(db, company_id)
        if company is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )
        return company

    def _ensure_owner(self, company, current_user: Any) -> None:
        if company.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the owner of this company",
            )

    async def get_company(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: Any | None,
    ) -> CompanyRead:
        """
        Якщо компанія public — бачать усі.
        Якщо hidden — лише owner, іншим 404.
        """
        company = await self._get_company_or_404(db, company_id)

        if company.visibility == "hidden":
            if current_user is None or company.owner_id != current_user.id:
                # Можна 403, але часто краще маскувати як 404
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found",
                )

        return CompanyRead.from_orm(company)

    async def update_company(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: Any,
        data: CompanyUpdate,
    ) -> CompanyRead:
        """
        Оновлення name / description / visibility — тільки для owner.
        """
        company = await self._get_company_or_404(db, company_id)
        self._ensure_owner(company, current_user)

        values = data.dict(exclude_unset=True)
        obj = await self.repo.update_one(db, company_id, **values)
        if obj is None:
            # формально не має статись, бо ми вже перевірили існування
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )

        return CompanyRead.from_orm(obj)

    async def delete_company(
        self,
        db: AsyncSession,
        *,
        company_id: UUID,
        current_user: Any,
    ) -> None:
        """
        Видалення компанії — тільки для owner.
        """
        company = await self._get_company_or_404(db, company_id)
        self._ensure_owner(company, current_user)

        deleted = await self.repo.delete_one(db, company_id)
        if not deleted:
            # на всякий випадок
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )

    async def list_public_companies(
        self,
        db: AsyncSession,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> CompanyListResponse:
        """
        Список public компаній з пагінацією.
        """
        total, items = await self.repo.get_public_paginated(
            db,
            offset=offset,
            limit=limit,
        )
        return CompanyListResponse(
            total=total,
            items=[CompanyRead.from_orm(i) for i in items],
            offset=offset,
            limit=limit,
        )

    async def list_my_companies(
        self,
        db: AsyncSession,
        *,
        current_user: Any,
        offset: int = 0,
        limit: int = 50,
    ) -> CompanyListResponse:
        total, items = await self.repo.get_by_owner_paginated(
            db,
            owner_id=current_user.id,
            offset=offset,
            limit=limit,
        )
        return CompanyListResponse(
            total=total,
            items=[CompanyRead.from_orm(i) for i in items],
            offset=offset,
            limit=limit,
        )
