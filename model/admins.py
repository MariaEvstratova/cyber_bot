from data.admins import Admins

class AdminsModel:

    def __init__(self, id: int = None, name: str = None, email: str = None, password: str = None):
        self.id = id
        self.name = name
        self.email = email
        self.password = password


    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
        }


def db_admin_to_model(db_admin: Admins) -> AdminsModel:
    return AdminsModel(db_admin.id, db_admin.name, db_admin.email, db_admin.hashed_password)
