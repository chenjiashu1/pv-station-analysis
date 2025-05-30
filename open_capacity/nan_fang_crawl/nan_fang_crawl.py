import json
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from database.models import insert_SourceInfo, find_not_db_SourceInfo, exist_url_fingerprint_code
from utils.codeUtil import get_url_fingerprint_code
from utils.fileUtil import uploadToHuaweiyunOssBySource_url

queryPowerList = [{"areaCode": "05", "areaName": "云南电网", "level": "1", "id": "yn1000000000060064"},
                  {"areaCode": "0501", "areaName": "昆明供电局", "level": "2", "id": "yn1000000000085087"},
                  {"areaCode": "0502", "areaName": "曲靖供电局", "level": "2", "id": "yn1000000000095434"},
                  {"areaCode": "0503", "areaName": "红河供电局", "level": "2", "id": "yn1000000000100703"},
                  {"areaCode": "0504", "areaName": "玉溪供电局", "level": "2", "id": "yn1000000000105193"},
                  {"areaCode": "0506", "areaName": "楚雄供电局", "level": "2", "id": "yn1000000000095118"},
                  {"areaCode": "0505", "areaName": "大理供电局", "level": "2", "id": "yn1000000000095190"},
                  {"areaCode": "0507", "areaName": "昭通供电局", "level": "2", "id": "yn1000000000100886"},
                  {"areaCode": "0508", "areaName": "普洱供电局", "level": "2", "id": "yn1000000000095348"},
                  {"areaCode": "0510", "areaName": "临沧供电局", "level": "2", "id": "yn1000000000095331"},
                  {"areaCode": "0509", "areaName": "西双版纳供电局", "level": "2", "id": "yn1000000000060063"},
                  {"areaCode": "0511", "areaName": "文山供电局", "level": "2", "id": "yn1000000000095496"},
                  {"areaCode": "0512", "areaName": "保山供电局", "level": "2", "id": "yn1000000000095117"},
                  {"areaCode": "0513", "areaName": "德宏供电局", "level": "2", "id": "yn1000000000100738"},
                  {"areaCode": "0516", "areaName": "怒江供电局", "level": "2", "id": "yn1000000000095280"},
                  {"areaCode": "0515", "areaName": "迪庆供电局", "level": "2", "id": "yn1000000000100737"},
                  {"areaCode": "0514", "areaName": "丽江供电局", "level": "2", "id": "yn1000000000095300"},
                  {"areaCode": "0522", "areaName": "瑞丽供电局", "level": "2", "id": "yn1000000000105131"}]


def findAreaNameByAreaCode(areaCode):
    for pv in queryPowerList:
        if pv["areaCode"] == areaCode:
            return pv['areaName']
    raise "未找到该区域" + areaCode


def get_html_links(areaCode):
    """调用接口获取可开放容量html链接资源"""
    url = "https://95598.csg.cn/ucs/ma/wt/searchService/queryInformationList"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    data = {
        "areaCode": areaCode,
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


def extract_download_links(html_url, areaCode):
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
        linkInfoList = []

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
            link_name = link.text
            document_type = get_document_type_from_url(href)
            full_url = href
            url_fingerprint_code = get_url_fingerprint_code(full_url)
            if not exist_url_fingerprint_code(url_fingerprint_code):
                # 添加到下载链接列表
                linkInfo = {
                    "link_url": full_url,
                    "link_name": link_name,
                    "url_fingerprint_code": url_fingerprint_code,
                    "document_type": document_type,
                    "areaCode": areaCode
                }
                linkInfoList.append(linkInfo)
            else:
                print(f"已爬取过该的文件，不再爬取: {full_url}")
                continue

        if not linkInfoList:
            print(f"在: {html_url} 中未找到文档下载链接")
            return []
        print(f"提取到如下下载链接： {linkInfoList}")
        print(f"链接中有{len(linkInfoList)}个下载链接")
        return linkInfoList
    except Exception as e:
        print(f"提取下载链接时发生错误({html_url}): {str(e)}")
        return []


def open_capacity_nan_fang_crawl(areaCode):
    """主函数"""
    try:
        # 获取HTML链接
        html_links = get_html_links(areaCode)
        if not html_links:
            print("one======没有找到符合条件的HTML链接")
            return

        all_linkInfoList = batch_extract_download_links(html_links, areaCode)
        if not all_linkInfoList:
            print("two======没有提炼到符合条件的HTML下载链接")
            return
        return download_to_oss(all_linkInfoList)
    except Exception as e:
        print(f"主程序运行时发生错误: {str(e)}")
        return "数据处理失败"





def download_to_oss(all_linkInfoList):
    oss_urls = []
    if all_linkInfoList:
        # todo cjs
        all_linkInfoList = [all_linkInfoList[0]]
        # 处理每个下载链接
        for linkInfo in all_linkInfoList:
            download_url = linkInfo['link_url']
            print(f"two====开始上传文件：{download_url}到oss系统")
            document_type = linkInfo['document_type']
            url_fingerprint_code = linkInfo['url_fingerprint_code']
            fileName = url_fingerprint_code + "." + document_type
            oss_url = uploadToHuaweiyunOssBySource_url(download_url, fileName)
            if not oss_url:
                print(f"未成功上传三方文件到oss系统: {download_url}")
                continue
            print(f"three====上传成功，oss文件链接：{oss_url}")
            url_fingerprint_code = insert_SourceInfo(
                download_url, "南方电网-可开放容量", json.dumps(linkInfo, ensure_ascii=False), oss_url)
            print(f"three====并记录下载指纹：{url_fingerprint_code}")
            oss_urls.append(oss_url)
    return oss_urls


def batch_extract_download_links(html_links, areaCode):
    # 处理每个HTML链接
    all_linkInfoList = []
    for html_url in html_links:
        print(f"batch_extract_download_links===: {html_url}")

        # 提取文档下载链接
        linkInfoList = extract_download_links(html_url, areaCode)

        if not linkInfoList:
            print(f"无法从{html_url}提取下载链接")
            continue
        all_linkInfoList = all_linkInfoList + linkInfoList
    print(f"two====总共找到{len(all_linkInfoList)}个下载链接")
    return all_linkInfoList
