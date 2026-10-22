from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Usuario, RolUsuario
from app.schemas import LoginRequest, TokenResponse, UsuarioOut
from app.security import verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["Autenticación y Usuarios"])
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    """Dependency to retrieve current authenticated user from JWT token."""
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionó token de autenticación.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload["sub"]
    user = db.query(Usuario).filter(Usuario.username == username, Usuario.activo == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo.",
        )
    
    return user


def require_roles(roles: List[RolUsuario]):
    """Role-based authorization dependency guard."""
    def role_checker(current_user: Usuario = Depends(get_current_user)):
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere uno de los siguientes roles: {[r.value for r in roles]}"
            )
        return current_user
    return role_checker


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Inicia sesión con usuario y contraseña, retornando token JWT y perfil."""
    user = db.query(Usuario).filter(Usuario.username == request.username).first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos."
        )
    
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta de usuario inactiva."
        )
    
    access_token = create_access_token(data={"sub": user.username, "rol": user.rol.value})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        usuario=UsuarioOut.model_validate(user)
    )


@router.get("/me", response_model=UsuarioOut)
def get_my_profile(current_user: Usuario = Depends(get_current_user)):
    """Retorna el perfil del usuario actualmente autenticado."""
    return UsuarioOut.model_validate(current_user)
