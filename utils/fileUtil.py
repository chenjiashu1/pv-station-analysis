# import markdown2
# from weasyprint import HTML
# import tempfile
import os

import pandas as pd
import pdfkit
import requests
from obs import ObsClient, PutObjectHeader

from config import file_download_path, huaweiyun_sk, huaweiyun_ak, huaweiyun_endpoint, huaweiyun_bucket_name, \
    huaweiyun_object_key_prefix
from utils.codeUtil import get_url_fingerprint_code

# def markdown_to_pdf(markdown_text):
#     # 将 Markdown 转 HTML
#     html_content = markdown2.markdown(markdown_text)
#
#     # 创建临时文件路径
#     with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmpfile:
#         pdf_path = tmpfile.name
#
#     # 将 HTML 转 PDF 并保存到临时文件
#     HTML(string=html_content).write_pdf(pdf_path)
#
#     return pdf_path

obsClient = ObsClient(access_key_id=huaweiyun_ak,
                      secret_access_key=huaweiyun_sk,
                      server=huaweiyun_endpoint)


def markdown_to_pdf2(markdown_content):
    output_path = "output.pdf"
    pdfkit.from_string(markdown_content, output_path)
    return output_path


def parse_pdf(filepath):
    # PDF解析实现
    import pdfplumber
    import pandas as pd

    # 新增：将PDF转换为Excel
    all_tables = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                df = pd.DataFrame(table[2:], columns=table[1])
                all_tables.append(df)

    if all_tables:
        output_path = filepath.replace('.pdf', '.xlsx')
        pd.concat(all_tables).to_excel(output_path, index=False)
        print(f"pdf已转换成Excel文件: {output_path}")
        parsed_data = parse_excel(output_path)

        print(f"parse_pdf: {parsed_data}")

        return parsed_data


def parse_excel(filepath):
    # Excel解析实现
    df = pd.read_excel(filepath)
    # 这里需要根据实际Excel格式实现具体解析逻辑
    # 示例：假设Excel有列：县区、年份、月份、变电站名称、光伏类型、电压等级(kw)、主变数量、主变容量(MVA)、可开放容(MW)
    parsed_data = []
    for _, row in df.iterrows():
        parsed_data.append({
            "provinceName": "云南省",
            "cityName": "昆明市",
            "countyName": row.get('县区', ''),
            "year": row.get('年份', ''),
            "month": row.get('月份', ''),
            "substationName": row.get('变电站名称', ''),
            "pv_type": row.get('光伏类型', ''),
            "v": str(row.get('电压等级(kw)', '')),
            "master_change_count": str(row.get('主变数量', '')),
            "master_change_capacity": str(row.get('主变容量(MVA)', '')),
            "open_capacity": str(row.get('可开放容(MW)', ''))
        })
        print(f"parse_excel: {parsed_data}")
    return parsed_data


def parse_document(filepath):
    """解析文档并返回数据列表"""
    try:
        # 获取文件扩展名
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()

        # 解析不同类型的文档
        if ext == '.pdf':
            return parse_pdf(filepath)
        elif ext in ['.xls', '.xlsx']:
            return parse_excel(filepath)
        else:
            print(f"不支持的文档类型: {ext}")
            return []
    except Exception as e:
        print(f"解析文档时发生错误: {str(e)}")
        return []


# 存储下载文件的目录
DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)


def download_document(url, document_type):
    """下载文档并保存到本地"""
    try:
        # 生成URL指纹
        url_fingerprint = get_url_fingerprint_code(url)

        # 检查是否已经下载过该文档
        existing_files = os.listdir(DOWNLOAD_DIR)
        if any(url_fingerprint in f for f in existing_files):
            print(f"文档已下载过: {url}")
            return None, url_fingerprint

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.2151.97",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.google.com/"
        }
        # 下载文档
        response = requests.get(url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()

        # 根据文档类型设置文件扩展名
        file_extension = {
            'pdf': '.pdf',
            'excel': '.xlsx',
            'doc': '.docx'
        }.get(document_type, '')

        # 生成文件名
        filename = f"{url_fingerprint}{file_extension}"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        # 写入文件
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        print(f"文档下载成功: {url} -> {filename}")
        return filepath, url_fingerprint
    except Exception as e:
        print(f"下载文档时发生错误: {str(e)}")
        return None, url_fingerprint


def uploadToHuaweiyunOssBySource_url(source_url, fileName):
    """
    将文件从源URL上传到华为云OSS，并返回OSS的访问URL

    参数：
        source_url (str): 源文件URL
        ak (str): 华为云Access Key ID
        sk (str): 华为云Secret Access Key
        endpoint (str): 华为云OSS Endpoint（如：obs.cn-north-4.myhuaweicloud.com）
        bucket_name (str): OSS桶名称
        object_key (str): 对象存储路径（包含文件名）

    返回：
        str: 华为云OSS文件访问URL 或 None（上传失败时）
    """

    object_key = huaweiyun_object_key_prefix + fileName

    try:

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.2151.97",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.google.com/"
        }
        # 下载文档
        response = requests.get(source_url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()  # 检查HTTP请求状态

        # 设置上传头部信息
        putObjectHeader = PutObjectHeader()
        putObjectHeader.contentType = response.headers.get('Content-Type', 'application/octet-stream')
        putObjectHeader.acl = 'public-read'  # 设置对象为公共读

        result = obsClient.putObject(huaweiyun_bucket_name,
                                     object_key,
                                     response.raw,
                                     headers=putObjectHeader)

        if result.status < 300:
            # 构造OSS访问URL（虚拟托管样式）
            oss_url = f"https://{huaweiyun_bucket_name}.{huaweiyun_endpoint}/{object_key}"
            return oss_url
        print(f"uploadToHuaweiyunOssBySource_url==={result}")
        return ""

    except requests.exceptions.RequestException as e:
        print(f"下载文件失败: {str(e)}")
        return ""
    except Exception as e:
        print(f"上传到OSS失败: {str(e)}")
        return ""
    finally:
        if obsClient:
            try:
                obsClient.close()  # 关闭客户端连接
            except:
                pass


def download_oss_file(oss_url):
    """
    从 OSS URL 下载文件并保存到指定的本地路径。

    :param oss_url: 要下载的文件的 OSS URL
    :param save_path: 本地保存路径，默认为 D:/tempFile
    :return: 下载后的本地文件路径
    """
    # 创建保存目录（如果不存在）
    os.makedirs(file_download_path, exist_ok=True)

    # 获取文件名
    file_name = os.path.basename(oss_url)
    local_file_path = file_download_path + file_name
    # local_file_path = os.path.join(file_download_path, file_name)

    # 下载文件
    response = requests.get(oss_url)
    if response.status_code == 200:
        with open(local_file_path, 'wb') as f:
            f.write(response.content)
        return local_file_path
    else:
        raise Exception(f"下载失败，状态码：{response.status_code}")


def uploadLocalFileToOss(file_path, fileName):
    """
    Uploads a local file to Alibaba Cloud OSS.

    :param file_path: Path of the file on the local system
    :return: True if upload was successful, False otherwise
    """
    # 这里需要添加实际的OSS上传逻辑
    try:
        putObjectHeader = PutObjectHeader()
        putObjectHeader.contentType = 'application/octet-stream'
        putObjectHeader.acl = 'public-read'  # 设置对象为公共读
        # 初始化OSS客户端
        # auth = oss2.Auth(huaweiyun_ak, huaweiyun_sk)
        # bucket = oss2.Bucket(auth, huaweiyun_endpoint, huaweiyun_bucket_name)
        object_key = huaweiyun_object_key_prefix + fileName
        #
        # # 上传文件
        # result = bucket.upload_file(object_key, file_path)
        result = obsClient.putFile(huaweiyun_bucket_name,
                                   object_key,
                                   file_path,
                                   headers=putObjectHeader)
        print(f'uploadLocalFileToOss-result: {result}')
        # 检查上传结果
        if result.status == 200:
            return result.body.objectUrl
        else:
            return ("上传oss未成功")
    except Exception as e:
        print(f'uploadLocalFileToOss-failed: {e}')
        return ("上传oss未成功")


def upload_content_to_oss(html_content, fileName):
    """
        Uploads a local file to Alibaba Cloud OSS.

        :return: True if upload was successful, False otherwise
        """
    # 这里需要添加实际的OSS上传逻辑
    try:
        putObjectHeader = PutObjectHeader()
        putObjectHeader.contentType = 'application/octet-stream'
        putObjectHeader.acl = 'public-read'  # 设置对象为公共读
        # 初始化OSS客户端
        # auth = oss2.Auth(huaweiyun_ak, huaweiyun_sk)
        # bucket = oss2.Bucket(auth, huaweiyun_endpoint, huaweiyun_bucket_name)
        object_key = huaweiyun_object_key_prefix + fileName
        #
        # # 上传文件
        # result = bucket.upload_file(object_key, file_path)
        result = obsClient.putContent(huaweiyun_bucket_name,
                                      object_key,
                                      html_content,
                                      headers=putObjectHeader)
        print(f'upload_content_to_oss-result: {result}')
        # 检查上传结果
        if result.status == 200:
            return result.body.objectUrl
        else:
            return ("上传oss未成功")
    except Exception as e:
        print(f'upload_content_to_oss-failed: {e}')
        return ("上传oss未成功")
