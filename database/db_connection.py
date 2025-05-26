from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine  # 显式导入 create_engine
from config import DATABASE_URI
from sqlalchemy.ext.declarative import declarative_base



engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()
# 创建基类
Base = declarative_base()

# 创建所有表
Base.metadata.create_all(engine)
