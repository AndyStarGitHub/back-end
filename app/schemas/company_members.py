from pydantic import BaseModel


class CompanyMemberUser(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True
