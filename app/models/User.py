from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from mongoengine import (
    Document, StringField, EmbeddedDocumentListField, EmbeddedDocument,
    ListField, BooleanField, DateTimeField
)


class RolUser(EmbeddedDocument):
    name = StringField(required=True, choices=["admin", "employee", "client"])
    permissions = ListField(StringField(choices=[
        "create_booking", "view_booking", "cancel_booking",
        "manage_users", "view_reports", "manage_rooms",
        "process_payments", "view_analytics"
    ]))


class User(Document):
    name = StringField(required=True)
    email = StringField(required=True, unique=True)
    hashed_password = StringField(required=True)
    telephone = StringField()
    roles = EmbeddedDocumentListField(RolUser)
    active = BooleanField(default=True)
    creation_date = DateTimeField(default=datetime.now)

    # Campos adicionales para autenticación
    last_login = DateTimeField()
    is_verified = BooleanField(default=False)
    reset_token = StringField()
    reset_token_expires = DateTimeField()

    meta = {
        'collection': 'users',
        'indexes': ['email', 'active', 'creation_date']
    }

    def set_password(self, password: str):
        """Genera hash de la contraseña"""
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifica la contraseña"""
        return check_password_hash(self.hashed_password, password)

    def has_permission(self, permission: str) -> bool:
        """Verifica si el usuario tiene un permiso específico"""
        for role in self.roles:
            if permission in role.permissions:
                return True
        return False

    def has_role(self, role_name: str) -> bool:
        """Verifica si el usuario tiene un rol específico"""
        return any(role.name == role_name for role in self.roles)

    def get_primary_role(self) -> str:
        """Obtiene el rol principal del usuario"""
        if self.roles:
            return self.roles[0].name
        return "client"

    def to_dict(self) -> dict:
        """Convierte a diccionario para serialización"""
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "telephone": self.telephone,
            "roles": [
                {
                    "name": role.name,
                    "permissions": role.permissions
                } for role in self.roles
            ],
            "active": self.active,
            "is_verified": self.is_verified,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }

    @classmethod
    def create_user_with_role(cls, name: str, email: str, password: str,
                              role_name: str = "client", telephone: str = None):
        """Método helper para crear usuario con rol por defecto"""
        # Definir permisos por rol
        role_permissions = {
            "admin": ["create_booking", "view_booking", "cancel_booking",
                      "manage_users", "view_reports", "manage_rooms",
                      "process_payments", "view_analytics"],
            "employee": ["create_booking", "view_booking", "cancel_booking",
                         "view_reports", "manage_rooms"],
            "client": ["create_booking", "view_booking", "cancel_booking"]
        }

        user = cls(
            name=name,
            email=email,
            telephone=telephone
        )
        user.set_password(password)

        # Crear rol con permisos
        role = RolUser(
            name=role_name,
            permissions=role_permissions.get(role_name, ["create_booking", "view_booking"])
        )
        user.roles = [role]

        return user