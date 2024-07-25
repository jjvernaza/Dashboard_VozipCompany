from sqlalchemy import create_engine

def get_engine():
    return create_engine('mysql+pymysql://root:WFClJvsXnNlTyZGbqXFIofJymrvmZpNk@viaduct.proxy.rlwy.net:10602/railway')
