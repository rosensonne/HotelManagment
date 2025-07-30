from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from bson import ObjectId
from mongoengine import DoesNotExist

from app.models.User import User
from app.schemas.user_schema import (
    UserResponse, UserUpdate, UserListResponse, UserRole
)
from app.utils.auth import (
    get_current_active_user, require_permissions, require_roles, oauth2_scheme
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_active_user)):
    return current_user.to_dict()


@router.put("/me", response_model=UserResponse)
def update_my_profile(
        user_update: UserUpdate,
        current_user: User = Depends(get_current_active_user)
):
    try:
        # Actualizar solo los campos proporcionados
        update_data = user_update.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)

        current_user.save()

        print(f"Perfil actualizado: {current_user.email}")
        return current_user.to_dict()

    except Exception as e:
        print(f"Error al actualizar perfil: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el perfil"
        )


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
        user_id: str,
        token: str = Depends(oauth2_scheme),
        current_user: User = Depends(require_permissions(["manage_users"])),
):
    print(f"Token recibido: {token}"),  # Debug
    print(f"Usuario actual: {current_user.email}")

    try:
        user_oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

    try:
        user = User.objects.get(id=user_oid)
        return user.to_dict()

    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
        user_id: str,
        user_update: UserUpdate,
        current_user: User = Depends(require_permissions(["manage_users"]))
):
    try:
        user_oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

    try:
        user = User.objects.get(id=user_oid)

        # Actualizar campos
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        user.save()

        print(f"Usuario actualizado por admin: {user.email}")
        return user.to_dict()

    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )


@router.get("/", response_model=UserListResponse)
def get_all_users(
        page: int = Query(1, ge=1, description="Número de página"),
        limit: int = Query(10, ge=1, le=100, description="Usuarios por página"),
        role: Optional[UserRole] = Query(None, description="Filtrar por rol"),
        active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
        search: Optional[str] = Query(None, description="Buscar por nombre o email"),
        current_user: User = Depends(require_permissions(["manage_users"]))
):
    try:
        # Construir query
        query = {}

        if role:
            query['roles__name'] = role.value

        if active is not None:
            query['active'] = active

        if search:
            # Búsqueda en nombre o email (insensible a mayúsculas)
            query['$or'] = [
                {'name': {'$regex': search, '$options': 'i'}},
                {'email': {'$regex': search, '$options': 'i'}}
            ]

        # Calcular offset
        offset = (page - 1) * limit

        # Obtener usuarios
        users_query = User.objects.filter(**query)
        total = users_query.count()
        users = users_query.skip(offset).limit(limit)

        # Convertir a dict
        users_data = [user.to_dict() for user in users]

        return {
            "users": users_data,
            "total": total,
            "page": page,
            "limit": limit
        }

    except Exception as e:
        print(f"Error al obtener usuarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener la lista de usuarios"
        )


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def deactivate_user(
        user_id: str,
        current_user: User = Depends(require_permissions(["manage_users"]))
):
    try:
        user_oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

    # No permitir que se desactive a sí mismo
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta"
        )

    try:
        user = User.objects.get(id=user_oid)
        user.active = False
        user.save()

        print(f"Usuario desactivado: {user.email}")
        return {"message": "Usuario desactivado exitosamente"}

    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )


@router.post("/{user_id}/activate", status_code=status.HTTP_200_OK)
def activate_user(
        user_id: str,
        current_user: User = Depends(require_permissions(["manage_users"]))
):
    try:
        user_oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

    try:
        user = User.objects.get(id=user_oid)
        user.active = True
        user.save()

        print(f"Usuario activado: {user.email}")
        return {"message": "Usuario activado exitosamente"}

    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )


@router.get("/stats/summary")
def get_user_stats(
        current_user: User = Depends(require_permissions(["view_reports"]))
):
    try:
        total_users = User.objects.count()
        active_users = User.objects.filter(active=True).count()
        inactive_users = total_users - active_users

        # Estadísticas por rol
        role_stats = {}
        for role in ["admin", "employee", "client"]:
            count = User.objects.filter(roles__name=role, active=True).count()
            role_stats[role] = count

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "role_distribution": role_stats
        }

    except Exception as e:
        print(f"Error al obtener estadísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estadísticas"
        )