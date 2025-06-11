from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from mongoengine import DoesNotExist

from app.models.User import User, RolUser
from app.schemas.user_schema import (
    UserCreate, UserResponse, UserLogin, TokenResponse,
    PasswordResetRequest, PasswordReset
)
from app.utils.auth import (
    authenticate_user, create_access_token, get_current_active_user,
    generate_reset_token
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate):
    try:
        # Verificar si el email ya existe
        existing_user = User.objects.get(email=user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
    except DoesNotExist:
        pass  # Email disponible

    try:
        # Crear usuario usando el método helper
        new_user = User.create_user_with_role(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
            role_name=user_data.role.value,
            telephone=user_data.telephone
        )

        # Guardar en base de datos
        new_user.save()

        print(f"Usuario registrado: {new_user.email}")
        return new_user.to_dict()

    except Exception as e:
        print(f"Error al registrar usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/login", response_model=TokenResponse)
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cuenta desactivada"
        )

    # Crear token de acceso
    access_token_expires = timedelta(minutes=1440)  # 24 horas
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )

    print(f"Usuario autenticado: {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 86400,  # 24 horas en segundos
        "user": user.to_dict()
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return current_user.to_dict()


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def send_password_reset_email(request: PasswordResetRequest):
    try:
        user = User.objects.get(email=request.email, active=True)

        # Generar token de reset
        reset_token = generate_reset_token()
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)  # 1 hora
        user.save()

        # TODO: Implementar envío de email
        # send_reset_email(user.email, reset_token)

        print(f"Token de reset generado para: {user.email}")
        print(f"Token: {reset_token}")  # Solo para desarrollo

        return {"message": "Se ha enviado un email con instrucciones para resetear la contraseña"}

    except DoesNotExist:
        # Por seguridad, no revelar si el email existe o no
        return {"message": "Se ha enviado un email con instrucciones para resetear la contraseña"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(reset_data: PasswordReset):
    try:
        user = User.objects.get(
            reset_token=reset_data.token,
            reset_token_expires__gte=datetime.utcnow(),
            active=True
        )

        # Cambiar contraseña
        user.set_password(reset_data.new_password)
        user.reset_token = None
        user.reset_token_expires = None
        user.save()

        print(f"Contraseña reseteada para: {user.email}")

        return {"message": "Contraseña actualizada exitosamente"}

    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado"
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout_user(current_user: User = Depends(get_current_active_user)):
    # En JWT stateless, el logout se maneja en el frontend eliminando el token
    # Aquí podrías implementar una blacklist de tokens si fuera necesario

    print(f"Usuario desconectado: {current_user.email}")

    return {"message": "Sesión cerrada exitosamente"}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(current_user: User = Depends(get_current_active_user)):
    access_token_expires = timedelta(minutes=1440)  # 24 horas
    access_token = create_access_token(
        data={"sub": current_user.email, "user_id": str(current_user.id)},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 86400,
        "user": current_user.to_dict()
    }