from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.core.errors import Forbidden, NotFound
from app.models.company import Company
from app.models.user import User
from app.repositories.company import CompanyRepository
from app.repositories.company_member import CompanyMemberRepository
from app.models.company_member import CompanyMember, CompanyMemberRoleEnum


company_repo = CompanyRepository()
company_member_repo = CompanyMemberRepository()


async def _get_company_or_404(db: AsyncSession, company_id) -> Company:
    company = await company_repo.get_by_id(db, company_id)
    if not company:
        raise NotFound("Company not found")
    return company


def _ensure_is_owner(current_user: User, company: Company) -> None:
    if company.owner_id != current_user.id:
        raise Forbidden("Only company owner can manage admins")


async def assign_admin(
    db: AsyncSession,
    *,
    company_id,
    member_user_id: int,
    current_user: User,
) -> CompanyMember:
    company = await _get_company_or_404(db, company_id)
    _ensure_is_owner(current_user, company)

    member = await company_member_repo.get_one_for_company_and_user(
        db,
        company_id=company_id,
        user_id=member_user_id,
    )
    if not member:
        raise Forbidden("User is not a member of this company")

    updated_member = await company_member_repo.update_one(
        db,
        obj_id=member.id,
        role=CompanyMemberRoleEnum.ADMIN,
    )
    if not updated_member:
        raise NotFound("Member not found")

    return updated_member


async def remove_admin(
    db: AsyncSession,
    *,
    company_id,
    member_user_id: int,
    current_user: User,
) -> CompanyMember:
    company = await _get_company_or_404(db, company_id)
    _ensure_is_owner(current_user, company)

    member = await company_member_repo.get_one_for_company_and_user(
        db,
        company_id=company_id,
        user_id=member_user_id,
    )
    if not member:
        raise NotFound("User is not a member of this company")

    updated_member = await company_member_repo.update_one(
        db,
        obj_id=member.id,
        role=CompanyMemberRoleEnum.MEMBER,
    )
    if not updated_member:
        raise NotFound("Member not found")

    return updated_member


async def list_admins(
    db: AsyncSession,
    *,
    company_id,
    current_user: User,
) -> Sequence[User]:
    company = await _get_company_or_404(db, company_id)

    admins = await company_member_repo.list_admins_for_company(
        db,
        company_id=company_id,
    )
    return admins
