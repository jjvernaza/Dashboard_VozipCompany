from sqlalchemy import create_engine

def get_engine():
    return create_engine('mysql+pymysql://root:ju4nj0s3@127.0.0.1:3306/vozip_python')
