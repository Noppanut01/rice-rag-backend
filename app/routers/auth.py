from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    # 1. หา user จาก username
    user = db.query(User).filter(User.username == body.username).first()

    # 2. เช็ค user มีอยู่จริงและ password ถูก
    if not user or not verify_password(body.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="username หรือ password ไม่ถูกต้อง",
        )

    # 3. สร้าง JWT token
    token = create_access_token({"sub": user.username})

    return TokenResponse(access_token=token)


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="username นี้มีอยู่แล้ว")

    user = User(username=body.username, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()

    token = create_access_token({"sub": user.username})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        username=str(current_user.username),
        role=str(current_user.role),
    )
