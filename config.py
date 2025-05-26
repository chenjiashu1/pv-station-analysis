import os

import dashscope

DATABASE_URI = os.getenv('DATABASE_URI', 'mysql+pymysql://root:root@localhost/pv_station')
# API_KEY = os.getenv('API_KEY', 'your_api_key_here')

ALI_ACCESS_KEY = "sk-77e9f67bb6454269a7b695b3a7f226d6"

GAODE_ACCESS_KEY ="a27fb67760d05b94310381ebf65cfb5f"

dashscope.api_key = ALI_ACCESS_KEY


DIFY_BASE_URL = "http://localhost"
# DIFY_BASE_URL = "http://host.docker.internal"
DATASET_ID = "95319f14-0a6d-438f-95cf-82f9aaca49da"  # 替换为你的知识库ID
DIFY_KNOEWLEDGE_KEY = "dataset-rBfmZMxGAN1oQ2oveUcw9a3Q"  # 替换为你的API Key
