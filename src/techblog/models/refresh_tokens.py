from sqlmodel import Field, SQLModel


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    token_hash: str = Field(primary_key=True)


class RefreshTokenRequest(SQLModel):
    refresh_token: str = Field(nullable=False)


class RefreshTokenResponse(SQLModel):
    access_token: str
    refresh_token:str
    token_type: str
