from sqlalchemy import create_engine

# Configuración del motor
def get_engine():
    return create_engine(
        'mysql+pymysql://u8cwb0paehh1l8ue:ALFHA1EO6IWF17Hm7Unm@buqpques8tk1uvbfib4j-mysql.services.clever-cloud.com:3306/buqpques8tk1uvbfib4j',
        pool_size=10,        # Tamaño inicial del pool
        max_overflow=20,      # Número máximo de conexiones extras
        pool_recycle=1800,    # Tiempo de vida de una conexión (en segundos)
        pool_pre_ping=True    # Verifica que las conexiones estén activas
    )
