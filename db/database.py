import configparser

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


config_path = 'config.ini'
# Создание объекта для чтения настроек
config = configparser.ConfigParser()
config.read(config_path)


db_user = config['DB SETTINGS']['DbUser']
user_password = config['DB SETTINGS']['UserPassword']
db_name = config['DB SETTINGS']['DbName']
host = config['DB SETTINGS']['Host']
engine = create_engine(
    f'postgresql+psycopg2://{db_user}:{user_password}@{host}/{db_name}',
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
