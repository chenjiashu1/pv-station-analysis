import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import Text
from datetime import datetime

from sqlalchemy import Column, Integer, String
from sqlalchemy import TIMESTAMP, func, Index

from utils.codeUtil import get_url_fingerprint_code
from .db_connection import Base, session
from sqlalchemy import text

open_capacity_table_structure = """
CREATE TABLE open_capacity (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    provinceName VARCHAR(255) COMMENT '省份名称',
    cityName VARCHAR(255) COMMENT '城市名称',
    countyName VARCHAR(255) COMMENT '县/区名称',
    township VARCHAR(255) COMMENT '所属乡镇',
    year VARCHAR(255) COMMENT '年',
    month VARCHAR(255) COMMENT '月',
    substationName VARCHAR(255) COMMENT '变电站名称',
    line_name VARCHAR(255) COMMENT '线路名称',
    open_capacity VARCHAR(255) COMMENT '可开放容量（KW）',
    pv_type VARCHAR(255) DEFAULT '分布式' COMMENT '电站类型',
    v VARCHAR(255) COMMENT '电压等级（kV）',
    rated_capacity VARCHAR(255) COMMENT '额定容量（kW）',
    max_load VARCHAR(255) COMMENT '最大负荷（kW）',
    master_change_count VARCHAR(255) COMMENT '主变数量',
    master_change_capacity VARCHAR(255) COMMENT '主变容量（KVA）',
    create_time VARCHAR(255) COMMENT '创建时间'
) COMMENT='可开放容量';
"""
ai_scene_info = [{
    "scene": "open_capacity",
    "scene_name": "可开放容量",
    "table_structure": open_capacity_table_structure
}]


def findSceneInfoByScene(scene):
    for scene_info in ai_scene_info:
        if scene_info["scene"] == scene:
            return scene_info
    raise "未找到场景信息"


def execute_sql(sql):
    result = session.execute(text(sql))
    return result.mappings().all()


# 定义open_capacity表
class open_capacity(Base):
    __tablename__ = 'open_capacity'
    id = Column(Integer, primary_key=True, autoincrement=True)
    provinceName = Column(String(255), comment='省份名称')
    cityName = Column(String(255), comment='城市名称')
    countyName = Column(String(255), comment='县/区名称')
    township = Column(String(255), comment='所属乡镇')
    year = Column(String(255), comment='年')
    month = Column(String(255), comment='月')
    substationName = Column(String(255), comment='变电站名称')
    line_name = Column(String(255), comment='线路名称')
    open_capacity = Column(String(255), comment='可开放容量（KW）')
    pv_type = Column(String(255), comment='电站类型', default="分布式")
    v = Column(String(255), comment='电压等级（kV）')
    rated_capacity = Column(String(255), comment='额定容量（kW）')
    max_load = Column(String(255), comment='最大负荷（kW）')
    master_change_count = Column(String(255), comment='主变数量')
    master_change_capacity = Column(String(255), comment='主变容量（KVA）')
    create_time = Column(String(255), comment='创建时间')


def insert_open_capacity(data):
    """将数据保存到数据库"""
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        values = []
        for item in data:
            values.append(
                open_capacity(
                    provinceName=item['provinceName'],
                    cityName=item['cityName'],
                    countyName=item['countyName'],
                    year=item['year'],
                    month=item['month'],
                    substationName=item['substationName'],
                    pv_type="分布式",
                    v=item['v'],
                    master_change_count=item['master_change_count'],
                    master_change_capacity=item['master_change_capacity'],
                    open_capacity=item['open_capacity'],
                    create_time=current_time,
                    line_name=item.get('line_name', ''),
                    rated_capacity=item.get('rated_capacity', ''),
                    max_load=item.get('max_load', ''),
                    township=item.get('township', '')
                )
            )
        session.add_all(values)
        session.commit()
        return "保存成功"
    except Exception as e:
        session.rollback()  # 发生异常时回滚
        print(f"保存到数据库时发生错误: {str(e)}")
        return "保存失败"


class SourceInfo(Base):
    __tablename__ = 'source_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_url = Column(String(1023), nullable=False)
    source_type = Column(String(255), nullable=False)  # 来源途径，如：爬虫、API、手动输入等
    sourceLinkInfo = Column(String(1023), nullable=False)  # 来源信息
    url_fingerprint_code = Column(String(255), nullable=False, unique=True)  # 来源url指纹code，唯一标识
    oss_url = Column(String(1023))  # 可选字段，存储OSS地址
    had_save_db = Column(Integer, nullable=False)  # 是否爬取过，0-未持久化；1-已持久化
    create_time = Column(TIMESTAMP, default=func.current_timestamp())
    # 添加索引
    Index('idx_url_fingerprint_code', url_fingerprint_code)

    def to_dict(self):
        return {
            'id': self.id,
            'source_url': self.source_url,
            'source_type': self.source_type,
            'sourceLinkInfo': self.sourceLinkInfo,
            'url_fingerprint_code': self.url_fingerprint_code,
            'oss_url': self.oss_url,
            'had_save_db': self.had_save_db,
            'create_time': self.create_time
        }


# 检查是否已存在相同的url_fingerprint_code
def exist_url_fingerprint_code(url_fingerprint_code):
    existing = (session.query(SourceInfo)
                .filter_by(url_fingerprint_code=url_fingerprint_code)
                .first())
    if existing:
        return True
    return False


def find_not_db_SourceInfo():
    try:
        result = (session.query(SourceInfo)
                  .filter_by(had_save_db=0)
                  .limit(5)
                  .all())
        print(f"find_not_db_SourceInfo-result===={result}")

        return result
    except Exception as e:
        session.rollback()
        raise  # 可根据业务决定是否重新抛出异常

def find_SourceInfo_by_id(id):
    try:
        result = (session.query(SourceInfo)
                  .filter_by(id=id)
                  .first())
        print(f"find_SourceInfo_by_id-id===={id}")

        return result
    except Exception as e:
        session.rollback()
        raise  # 可根据业务决定是否重新抛出异常

def update_SourceInfo_toDb(id):
    try:
        source_info = session.query(SourceInfo).filter_by(id=id).first()
        if source_info:
            source_info.had_save_db = 1
            session.commit()
        return source_info
    except Exception as e:
        session.rollback()
        raise  # 可根据业务决定是否重新抛出异常


def insert_SourceInfo(source_url, source_type, sourceLinkInfo, oss_url):
    url_fingerprint_code = get_url_fingerprint_code(source_url)

    """
    插入SourceInfo记录
    :param source_url: 来源URL
    :param source_type: 来源途径
    :param url_fingerprint_code: URL指纹code（唯一）
    :param oss_url: OSS存储地址（可选）
    :return: 插入成功返回True，若指纹code已存在返回False
    """
    try:
        new_source = SourceInfo(
            source_url=source_url,
            source_type=source_type,
            sourceLinkInfo=sourceLinkInfo,
            url_fingerprint_code=url_fingerprint_code,
            had_save_db=0,
            oss_url=oss_url,
            create_time=datetime.now()
        )
        session.add(new_source)
        session.commit()
        return url_fingerprint_code
    except Exception as e:
        session.rollback()
        raise e


class AIAnalysisRecord(Base):
    __tablename__ = 'ai_analysis_record'

    id = Column(Integer, primary_key=True, autoincrement=True)
    scene = Column(String(255), nullable=False)  # 场景
    user_request = Column(Text, nullable=False)  # 用户要求
    sql_query = Column(Text, nullable=False)
    oss_url = Column(String(1023))  # HTML文件OSS地址
    create_time = Column(TIMESTAMP, default=func.current_timestamp())  # 创建时间

    def to_dict(self):
        return {
            'id': self.id,
            'scene': self.scene,
            'user_request': self.user_request,
            'oss_url': self.oss_url,
            'create_time': self.create_time
        }


def insert_ai_analysis_record(scene, user_request, sql_query, html_url):
    try:
        new_source = AIAnalysisRecord(
            scene=scene,
            user_request=user_request,
            sql_query=sql_query,
            oss_url=html_url,
            create_time=datetime.now()
        )
        session.add(new_source)
        session.commit()
        print(f"insert_analysis_record===成功")
        return "insert_analysis_record===成功"
    except Exception as e:
        session.rollback()
        raise e
