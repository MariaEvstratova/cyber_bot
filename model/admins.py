from data.admins import Admins

class AdminsModel:

    def __init__(self, id: int = None, name: str = None, email: str = None, password: str = None, is_active: bool = None):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.is_active = is_active
        self.is_authenticated = True

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return True

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'is_activ': self.is_active
        }


def db_admin_to_model(db_admin: Admins) -> AdminsModel:
    return AdminsModel(db_admin.id, db_admin.name, db_admin.email, db_admin.hashed_password, True)
