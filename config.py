import os

import dashscope

# ================db========================
# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'pv_station_analysis'
}

DATABASE_URI = os.getenv('DATABASE_URI',
                         f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
                         )
# 'mysql+pymysql://root:root@localhost/pv_station_analysis'

# ================llm========================


SELF_ALI_ACCESS_KEY = "sk-77e9f67bb6454269a7b695b3a7f226d6"
COMPANY_ALI_ACCESS_KEY = "sk-ad510e9560454dcc977de24bc3fac065"
ALI_ACCESS_KEY = COMPANY_ALI_ACCESS_KEY
dashscope.api_key = ALI_ACCESS_KEY

# ================gaode========================


GAODE_ACCESS_KEY = "a27fb67760d05b94310381ebf65cfb5f"

# ================dify========================


DIFY_BASE_URL = "http://localhost"
# DIFY_BASE_URL = "http://host.docker.internal"
DATASET_ID = "95319f14-0a6d-438f-95cf-82f9aaca49da"  # 替换为你的知识库ID
DIFY_KNOEWLEDGE_KEY = "dataset-rBfmZMxGAN1oQ2oveUcw9a3Q"  # 替换为你的API Key

# =======================oss================
huaweiyun_ak = "WHBM2GPU8CDWSBCEMUNX"
huaweiyun_sk = "2nuezsQMAHwOu2wJGiaZnFqCquUlb7JD9v6HDTkd"
huaweiyun_endpoint = "obs.cn-south-1.myhuaweicloud.com"
huaweiyun_bucket_name = "aurora-test-obs"
huaweiyun_object_key_prefix=  "cjs/"
file_download_path= "D:/tempFile/downLoad"
file_upload_path= "D:/tempFile/upload"