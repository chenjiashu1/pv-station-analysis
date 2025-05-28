import requests
import json
from bs4 import BeautifulSoup

from database.models import insert_open_capacity, insert_SourceInfo, find_not_db_SourceInfo, exist_url_fingerprint_code, \
    update_SourceInfo_toDb
from urllib.parse import urlparse, parse_qs

from utils.aiUtil import ai_parse_document
from utils.codeUtil import get_url_fingerprint_code
from utils.fileUtil import uploadToHuaweiyunOssBySource_url, download_oss_file


def get_html_links():
    """调用接口获取可开放容量html链接资源"""
    url = "https://95598.csg.cn/ucs/ma/wt/searchService/queryInformationList"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    data = {
        "areaCode": "0501",
        "level": "2",
        "classId": "b524e5cf537f4eefb42c05e2f57a436f",
        "pageNo": 1,
        "pageSize": 15,
        "version": "cn",
        "keyword": "可开放容量信息"
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        result = response.json()

        if result["sta"] == "00":
            # 过滤包含"月分布式光伏"内容的所有link中的html链接
            html_links = [
                item["link"] for item in result["data"]["infoList"]
                if "月分布式光伏" in item.get("infoTitle", "") and item["link"].endswith((".html", ".htm"))
            ]
            print(f"one===调用接口获取可开放容量html链接资源{len(html_links)}个如下: {html_links}")

            return html_links
        else:
            print(f"接口请求失败: {result['message']}")
            return []
    except Exception as e:
        print(f"获取HTML链接时发生错误: {str(e)}")
        return []


def get_document_type_from_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    # 获取 'documentType' 参数的值列表，默认返回空列表
    document_types = query_params.get('documentType', [])
    # 返回第一个值（如果存在），否则返回 None
    return document_types[0] if document_types else None


def extract_download_links(html_url):
    """从HTML页面中提取所有文档下载链接"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.2151.97",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.google.com/"
        }
        response = requests.get(html_url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找所有可能包含下载链接的a标签
        links = soup.find_all('a', href=True)

        # 存储找到的所有下载链接
        download_links = []

        # 常见文档类型的正则表达式模式
        # doc_patterns = {
        #     'pdf': r'\.pdf$|\/PDF',
        #     'excel': r'\.xls$|\.xlsx$|\/XLSX?|$$Excel',
        #     'doc': r'\.doc$|\.docx$|\/DOCX?|$$Word'
        # }

        doc_patterns = {
            'pdf': "pdf|PDF",
            'excel': "xls|xlsx|XLSX|Excel",
            'doc': "doc|docx|DOCX|Word"
        }
        # 检查每个链接是否匹配支持的文档类型
        for link in links:
            href = link['href']
            # 获取文件扩展名并匹配支持的类型
            supported_types = {"pdf": "pdf", "PDF": "pdf", "xls": "excel", "xlsx": "excel"}
            document_type = get_document_type_from_url(href)
            for doc_type, pattern in supported_types.items():
                if doc_type == document_type:
                    # 如果是相对路径，补全URL
                    if href.startswith('/'):
                        from urllib.parse import urljoin
                        full_url = urljoin(html_url, href)
                    else:
                        full_url = href
                    url_fingerprint_code  = get_url_fingerprint_code(full_url)
                    if not exist_url_fingerprint_code(url_fingerprint_code):
                        # 添加到下载链接列表
                        download_links.append(full_url)
                    else:
                        print(f"已爬取过该的文件，不再爬取: {full_url}")

        if not download_links:
            print(f"在: {html_url} 中未找到文档下载链接")
        print(f"提取到如下下载链接： {html_url}")
        return download_links
    except Exception as e:
        print(f"提取下载链接时发生错误({html_url}): {str(e)}")
        return []


def open_capacity_nan_fang_crawl():
    """主函数"""
    try:
        # 获取HTML链接
        html_links = get_html_links()
        if not html_links:
            print("没有找到符合条件的HTML链接")
            return

        all_download_urls = batch_extract_download_links(html_links)

        return download_to_oss(all_download_urls)
    except Exception as e:
        print(f"主程序运行时发生错误: {str(e)}")
        return "数据处理失败"


def open_capacity_nan_fang_parseToDb():
    sourceInfos = find_not_db_SourceInfo()
    if sourceInfos:
        for sourceInfo in sourceInfos:
            ai_parse_document_and_db(sourceInfo)
    return "南方电网可开放容量数据解析并落库完成"


def ai_parse_document_and_db(sourceInfo):
    oss_url = sourceInfo.oss_url
    local_file_path = download_oss_file(oss_url)
    # 解析文档
    parsed_data_string = ai_parse_document(local_file_path)

    if not parsed_data_string:
        print(f"解析文档失败: {oss_url}")
        return ""
    parsed_data = []
    try:
        parsed_data = json.loads(parsed_data_string)
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
    print(f"ai_parse_document====成功解析出{len(parsed_data)}条可开放容量的数据")

    # 每50行数据插入一次数据库
    batch_size = 50
    for i in range(0, len(parsed_data), batch_size):
        batch_data = parsed_data[i:i + batch_size]
        insert_open_capacity(batch_data)
    update_SourceInfo_toDb(sourceInfo.id)
    print(f"ai_parse_document_and_db-oss_url====数据解析并落库完成:{oss_url}")


def download_to_oss(all_download_urls):
    oss_urls = []
    if all_download_urls:
        # todo cjs
        # all_download_urls = [all_download_urls[0]]
        # 处理每个下载链接
        for download_url in all_download_urls:
            print(f"two====开始上传文件：{download_url}到oss系统")
            document_type = get_document_type_from_url(download_url)
            url_fingerprint_code = get_url_fingerprint_code(download_url)
            fileName = url_fingerprint_code + "." + document_type
            oss_url = uploadToHuaweiyunOssBySource_url(download_url, fileName)
            if not oss_url:
                print(f"未成功上传三方文件到oss系统: {download_url}")
                continue
            print(f"three====上传成功，oss文件链接：{oss_url}")
            url_fingerprint_code = insert_SourceInfo(
                download_url, "南方电网-可开放容量", oss_url)
            print(f"three====并记录下载指纹：{url_fingerprint_code}")
            oss_urls.append(oss_url)
    return oss_urls

def batch_extract_download_links(html_links):
    # 处理每个HTML链接
    all_download_urls = []
    for html_url in html_links:
        print(f"处理链接: {html_url}")

        # 提取文档下载链接
        download_urls = extract_download_links(html_url)

        if not download_urls:
            print(f"无法从{html_url}提取下载链接")
            continue
        print(f"链接中有{len(download_urls)}个下载链接")
        all_download_urls = all_download_urls + download_urls
    print(f"two====总共找到{len(all_download_urls)}个下载链接: {', '.join(all_download_urls)}")
    return all_download_urls
