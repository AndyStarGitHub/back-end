from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFound, Forbidden
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.models.user import User


async def remove_member_from_company(
    db: AsyncSession,
    company_id: str,
    member_user_id: int,
    current_user: User,
) -> None:

    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company: Company | None = result.scalar_one_or_none()
    if company is None:
        raise NotFound("Company not found")

    if company.owner_id != current_user.id:
        raise Forbidden("Only company owner can remove members")

    if member_user_id == company.owner_id:
        raise Forbidden("Owner cannot be removed from the company")

    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company.id,
            CompanyMember.user_id == member_user_id,
        )
    )
    membership: CompanyMember | None = result.scalar_one_or_none()
    if membership is None:
        raise Forbidden("User is not a member of this company")

    await db.delete(membership)
    await db.commit()


async def leave_company(
    db: AsyncSession,
    company_id: str,
    current_user: User,
) -> None:

    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company: Company | None = result.scalar_one_or_none()
    if company is None:
        raise NotFound("Company not found")

    if company.owner_id == current_user.id:
        raise Forbidden("Owner cannot leave the company")

    result = await db.execute(
        select(CompanyMember).where(
            CompanyMember.company_id == company.id,
            CompanyMember.user_id == current_user.id,
        )
    )
    membership: CompanyMember | None = result.scalar_one_or_none()
    if membership is None:
        raise Forbidden("User is not a member of this company")

    await db.delete(membership)
    await db.commit()


async def list_company_members(
    db: AsyncSession,
    company_id: str,
    limit: int = 20,
    offset: int = 0,
) -> Sequence[User]:

    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company: Company | None = result.scalar_one_or_none()
    if company is None:
        raise NotFound("Company not found")

    stmt = (
        select(User)
        .join(CompanyMember, CompanyMember.user_id == User.id)
        .where(CompanyMember.company_id == company.id)
        .order_by(User.id)
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(stmt)
    users = result.scalars().all()
    return users
