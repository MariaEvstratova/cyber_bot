import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session


SqlAlchemyBase = orm.declarative_base()

__factory = None


def global_init(db_url = None, db_local_path = "db/data_base.db"):
    global __factory

    if __factory:
        return

    if not (db_url is None):
        conn_str = db_url
        print(f"Выполнено подключение к облачной базе данных")
    else:
        conn_str = f'sqlite:///{db_local_path.strip()}?check_same_thread=False'
        print(f"Выполнено подключение к локальной базе данных по адресу {conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()