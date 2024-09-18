from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configuración del motor
def get_engine():
    return create_engine('mysql+pymysql://u8cwb0paehh1l8ue:ALFHA1EO6IWfl7Hm7Unm@buqpques8tk1uvbfib4j-mysql.services.clever-cloud.com:3306/buqpques8tk1uvbfib4j')

# Crear una sesión
engine = get_engine()
Session = sessionmaker(bind=engine)
session = Session()
