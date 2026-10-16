from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import NoResultFound

from ..db import SessionDep
from ..models.users import LoginRequest
from ..utilities.security import verify_password
from ..utilities.users import get_user_by_email

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/", status_code=status.HTTP_200_OK)
def login_user(session: SessionDep, data: LoginRequest):
    try:
        user = get_user_by_email(session, data.email)

        if not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid user credentials",
            )

        return {"message": "Login successful", "user_id": str(user.id)}
    except NoResultFound as _:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid user credentials"
        )
