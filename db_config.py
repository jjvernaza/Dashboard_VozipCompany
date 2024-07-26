from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configuración del motor
def get_engine():
    return create_engine('mysql+pymysql://avnadmin:AVNS_5uSGQcVeHQEIRQ1YA8b@mysql-f2a31f6-jjvernazamayor-66da.g.aivencloud.com:19544/vozip_database')

# Crear una sesión
engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()
