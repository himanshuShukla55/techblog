from sqlmodel import Field, SQLModel


class LogoutRequest(SQLModel):
    refresh_token: str = Field(nullable=False)
