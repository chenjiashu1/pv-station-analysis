import requests
import json
from bs4 import BeautifulSoup
import re
import os
import hashlib
import pandas as pd

from database.db_connection import engine
from database.models import save_open_capacity, save_url_fingerprint

# 存储下载文件的目录
DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)


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
            print(f"调用接口获取可开放容量html链接资源如下: {html_links}")
            return html_links
        else:
            print(f"接口请求失败: {result['message']}")
            return []
    except Exception as e:
        print(f"获取HTML链接时发生错误: {str(e)}")
        return []


def extract_download_links(html_url):
    """从HTML页面中提取所有文档下载链接"""
    try:
        response = requests.get(html_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找所有可能包含下载链接的a标签
        links = soup.find_all('a', href=True)
        
        # 存储找到的所有下载链接
        download_links = []
        
        # 常见文档类型的正则表达式模式
        doc_patterns = {
            'pdf': r'\.pdf$|\/PDF',
            'excel': r'\.xls$|\.xlsx$|\/XLSX?|$$Excel',
            'doc': r'\.doc$|\.docx$|\/DOCX?|$$Word'
        }
        
        # 检查每个链接是否匹配文档类型
        for link in links:
            href = link['href'].lower()
            for doc_type, pattern in doc_patterns.items():
                if re.search(pattern, href):
                    # 如果是相对路径，补全URL
                    if href.startswith('/'):
                        from urllib.parse import urljoin
                        full_url = urljoin(html_url, href)
                    else:
                        full_url = href
                    
                    # 添加到下载链接列表
                    download_links.append(full_url)
        
        if not download_links:
            print(f"在{html_url}中未找到文档下载链接")
        print(f"提取到如下下载链接： {html_url}")
        return download_links
    except Exception as e:
        print(f"提取下载链接时发生错误({html_url}): {str(e)}")
        return []


def download_document(url, document_type):
    """下载文档并保存到本地"""
    try:
        # 生成URL指纹
        url_fingerprint = hashlib.md5(url.encode()).hexdigest()
        
        # 检查是否已经下载过该文档
        existing_files = os.listdir(DOWNLOAD_DIR)
        if any(url_fingerprint in f for f in existing_files):
            print(f"文档已下载过: {url}")
            return None, url_fingerprint
        
        # 下载文档
        response = requests.get(url, stream=True, timeout=60)
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


def parse_document(filepath):
    """解析文档并返回数据列表"""
    try:
        # 获取文件扩展名
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()
        
        # 解析不同类型的文档
        if ext == '.pdf':
            # PDF解析实现
            import PyPDF2
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                # 这里需要根据实际PDF格式实现具体解析逻辑
                # 示例：假设文本中有类似"晋宁区2024年8月变电站名称分布式电压等级(kw)主变数量主变容量(MVA)可开放容(MW)"的数据
                pattern = r'(.*?)\\s*(2024年)\\s*(8月)\\s*(.*?)\\s*Distributed\\s*(.*?)\\s*(\\d+)\\s*(.*?)\\s*(.*?)'
                matches = re.findall(pattern, text)
                
                # 将匹配结果转换为指定格式
                parsed_data = [{
                    "provinceName": "云南省",
                    "cityName": "昆明市",
                    "countyName": match[0],
                    "year": match[1],
                    "month": match[2],
                    "substationName": match[3],
                    "pv_type": "分布式",
                    "v": match[4],
                    "master_change_count": match[5],
                    "master_change_capacity": match[6],
                    "open_capacity": match[7]
                } for match in matches]
                
                return parsed_data
        elif ext in ['.xls', '.xlsx']:
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
            return parsed_data
        elif ext in ['.doc', '.docx']:
            # Word文档解析实现
            from docx import Document
            doc = Document(filepath)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            # 这里需要根据实际Word格式实现具体解析逻辑
            # 示例：假设文本中有类似"晋宁区2024年8月变电站名称分布式电压等级(kw)主变数量主变容量(MVA)可开放容(MW)"的数据
            pattern = r'(.*?)\\s*(2024年)\\s*(8月)\\s*(.*?)\\s*Distributed\\s*(.*?)\\s*(\\d+)\\s*(.*?)\\s*(.*?)'
            matches = re.findall(pattern, text)
            
            # 将匹配结果转换为指定格式
            parsed_data = [{
                "provinceName": "云南省",
                "cityName": "昆明市",
                "countyName": match[0],
                "year": match[1],
                "month": match[2],
                "substationName": match[3],
                "pv_type": "分布式",
                "v": match[4],
                "master_change_count": match[5],
                "master_change_capacity": match[6],
                "open_capacity": match[7]
            } for match in matches]
            
            return parsed_data
        else:
            print(f"不支持的文档类型: {ext}")
            return []
    except Exception as e:
        print(f"解析文档时发生错误: {str(e)}")
        return []


def open_capacity_nan_fang_crawl():
    """主函数"""
    try:
        # 获取HTML链接
        html_links = get_html_links()
        if not html_links:
            print("没有找到符合条件的HTML链接")
            return
        
        print(f"找到{len(html_links)}个HTML链接")
        
        # 处理每个HTML链接
        for html_url in html_links:
            print(f"处理链接: {html_url}")
            
            # 提取文档下载链接
            download_urls = extract_download_links(html_url)

            if not download_urls:
                print(f"无法从{html_url}提取下载链接")
                continue
            
            print(f"找到{len(download_urls)}个下载链接: {', '.join(download_urls)}")
            download_urls = [download_urls[0]]
            # 处理每个下载链接
            for download_url in download_urls:
                # 判断文档类型
                if download_url.lower().endswith('.pdf'):
                    document_type = 'pdf'
                elif download_url.lower().endswith(('.xls', '.xlsx')):
                    document_type = 'excel'
                elif download_url.lower().endswith(('.doc', '.docx')):
                    document_type = 'doc'
                else:
                    print(f"不支持的文档类型: {download_url}")
                    continue
                
                print(f"处理下载链接: {download_url}")
            
                # 下载文档
                filepath, url_fingerprint = download_document(download_url, document_type)
                if not filepath:
                    print(f"下载文档失败: {download_url}")
                    continue
                
                # 解析文档
                parsed_data = parse_document(filepath)
                if not parsed_data:
                    print(f"解析文档失败: {filepath}")
                    continue
                
                print(f"成功解析{len(parsed_data)}条数据")
                
                # 每50行数据插入一次数据库
                batch_size = 50
                for i in range(0, len(parsed_data), batch_size):
                    batch_data = parsed_data[i:i+batch_size]
                    save_open_capacity(batch_data)
                save_url_fingerprint(url_fingerprint)

            
        print("数据处理完成")
        return "数据处理完成"
    except Exception as e:
        print(f"主程序运行时发生错误: {str(e)}")
        return "数据处理失败"