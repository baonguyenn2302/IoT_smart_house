from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import TokenOut, UserOut
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenOut, summary="Đăng nhập")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == form.username))
    if user is None or not verify_password(form.password, user.password):
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")
    return TokenOut(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut, summary="Hồ sơ người đang đăng nhập")
def me(user: User = Depends(get_current_user)):
    return user