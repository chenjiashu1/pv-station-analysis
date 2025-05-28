from flask import request, jsonify
import os
from utils.aiUtil import call_qwen_plus, call_qwen_vl, call_qwen_vl_v2
from config import DIFY_BASE_URL, DATASET_ID, DIFY_KNOEWLEDGE_KEY, ALI_ACCESS_KEY
from crawl4ai import AsyncWebCrawler

def download_html(url):
    """下载HTML页面内容"""
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"下载失败，状态码: {response.status_code}")
def url_to_knownledge(url, fileName):
    prompt = ("# 您是电网系统知识工程师 + 数据清洗专家 + 文档管理架构师"
              "## 核心能力:"
              " * 1、解析上述文件"
            " * 2、对解析结果进行数据清洗"
            "* 3、对解析结果进行内容归类"
              "* 4、对结果以纯markdown格式输出结果"
              )
    md = call_qwen_vl_v2(prompt, [url])
    print(f"url_to_knownledge md={md}")
    upload_txt_to_dify(md, fileName)

def upload_txt_to_dify(html_content: str, fileName: str):
    url = f"{DIFY_BASE_URL}/v1/datasets/{DATASET_ID}/document/create-by-text"
    # 'http://localhost/v1/datasets/{dataset_id}/document/create-by-text' \
    'http://localhost/v1/datasets/95319f14-0a6d-438f-95cf-82f9aaca49da/document/create-by-text'
    headers = {
        "Authorization": f"Bearer {DIFY_KNOEWLEDGE_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": html_content,
        "name": fileName,
        "indexing_technique": "high_quality",
        "process_rule": {
            "mode": "automatic"
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("upload_txt_to_dify url:", url)
        print("upload_txt_to_dify 上传成功:", response.json())
    else:
        raise Exception(f"上传失败: {response.status_code}, {response.text}")

def upload_file_to_dify_web():
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({"result": "未提供文件"}), 400

    file = request.files['file']

    # 检查是否选择了文件
    if file.filename == '':
        return jsonify({"result": "未选择文件"}), 400

    # 获取 data 参数（JSON 字符串）
    data_json = '{"indexing_technique":"high_quality","process_rule":{"rules":{"pre_processing_rules":[{"id":"remove_extra_spaces","enabled":true},{"id":"remove_urls_emails","enabled":true}],"segmentation":{"separator":"###","max_tokens":500}},"mode":"custom"}}'
    if not data_json:
        return jsonify({"result": "缺少 data 参数"}), 400

    # 创建临时目录保存上传的文件
    file_path = os.path.join("D:\\temp_uploads", file.filename)
    file.save(file_path)

    # 构建请求 URL
    url = f"{DIFY_BASE_URL}/v1/datasets/{DATASET_ID}/document/create-by-file"

    # 设置请求头
    headers = {
        "Authorization": f"Bearer {DIFY_KNOEWLEDGE_KEY}"
    }

    # 准备上传数据
    files = {
        'file': open(file_path, 'rb')
    }
    data = {
        'data': data_json
    }

    # 发送请求
    response = requests.post(
        url,
        headers=headers,
        files=files,
        data=data
    )

    # 返回响应结果
    return jsonify({
        "status_code": response.status_code,
        "response": response.json() if response.headers['Content-Type'].startswith(
            'application/json') else response.text
    })
# 本地文件上传dify知识库
def upload_fileUrl_to_dify_web():
    fileInfo = request.get_json().get('fileInfo')

    # 获取 data 参数（JSON 字符串）
    data_json = '{"indexing_technique":"high_quality","process_rule":{"rules":{"pre_processing_rules":[{"id":"remove_extra_spaces","enabled":true},{"id":"remove_urls_emails","enabled":true}],"segmentation":{"separator":"###","max_tokens":500}},"mode":"custom"}}'
    if not data_json:
        return jsonify({"result": "缺少 data 参数"}), 400

    # 构建请求 URL
    url = f"{DIFY_BASE_URL}/v1/datasets/{DATASET_ID}/document/create-by-file"

    # 设置请求头
    headers = {
        "Authorization": f"Bearer {DIFY_KNOEWLEDGE_KEY}"
    }

    # 准备上传数据
    files = {
        'file': open(fileInfo.get("file_path"), 'rb')
    }
    data = {
        'data': data_json
    }

    # 发送请求
    response = requests.post(
        url,
        headers=headers,
        files=files,
        data=data
    )

    # 返回响应结果
    return jsonify({
        "status_code": response.status_code,
        "response": response.json() if response.headers['Content-Type'].startswith(
            'application/json') else response.text
    })
import asyncio
def crawlAI_deal_knowledge_to_dify(input):
    url = input.get("url")
    fileName = input.get("fileName")
    print(f"crawlAI_deal_knowledge_to_dify====url={url},fileName={fileName}")
    asyncio.run(fetch_and_process_content(url, fileName))
    # crawler = AsyncWebCrawler()
    # results = crawler.crawl([url], extract_media=True, extract_links=True)


async def fetch_and_process_content(url, fileName):
    """
    使用 crawl4ai 爬取网页内容并整理成 Markdown。

    :param url: 要爬取的 URL
    :param file_name: 文件名（可选）
    :return: 返回整理后的 Markdown 内容
    """
    # 创建异步爬虫实例
    crawler = AsyncWebCrawler()

    # 爬取网页内容
    results = await crawler.arun(url=url)
    print(f"fetch_and_process_content results={results}")
    print(f"fetch_and_process_content md={results.markdown}")
    upload_txt_to_dify(results.markdown, fileName)

#
# from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
# from crawl4ai.extraction_strategy import LLMExtractionStrategy
# from pydantic import BaseModel, Field
# async def fetch_and_process_content2(url):
#     prompt = f"""
#             你是一个专业的 HTML 到 Markdown 转换器。
#             请将以下 HTML 内容整理为清晰、简洁的 Markdown 格式。要求如下：
#             - 移除所有 HTML 标签
#             - 保留标题、段落和列表结构
#             - 提供简洁明了的内容总结
#             - 输出格式应为标准 Markdown
#             """
#     browser_config = BrowserConfig(verbose=True)
#     run_config = CrawlerRunConfig(
#         word_count_threshold=1,
#         extraction_strategy=LLMExtractionStrategy(
#             # Here you can use any provider that Litellm library supports, for instance: ollama/qwen2
#             # provider="ollama/qwen2", api_token="no-token",
#             llm_config=LLMConfig(provider="openai/deepseek-r1", api_token=ALI_ACCESS_KEY),
#             # schema=OpenAIModelFee.schema(),
#             extraction_type="schema",
#             instruction=prompt
#         ),
#         cache_mode=CacheMode.BYPASS,
#     )
#
#     async with AsyncWebCrawler(config=browser_config) as crawler:
#         result = await crawler.arun(
#             url=url,
#             config=run_config
#         )
#         print(f"fetch_and_process_content2-result={result}")
#         return result




def main(a, b):
    call_upload_api(a, b)
    return {
        "result": {"a": "成功"}
    }

import requests
import json


def call_upload_api(a, b):
    url = "http://localhost:5000/upload_txt_to_dify"

    payload = {
        "fileInfo": {
            "content": a,
            "fileName": b
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, data=json.dumps(payload, ensure_ascii=False), headers=headers)

    return response.json()  # 返回响应结果

import re
def select_KnownLedgeDoc():
    data = request.get_json()
    userQuery = data.get('userQuery', '') if data else ''

    # 使用正则匹配所有《...》之间的内容（支持多个书名）
    book_titles = re.findall(r'《(.*?)》', userQuery)
    if not book_titles:
        print("未在查询中找到书名号内的书籍名称")
        return "", 200

    # Dify 接口配置
    url = f"{DIFY_BASE_URL}/v1/datasets/{DATASET_ID}/documents?page=1&limit=20"
    headers = {
        "Authorization": f"Bearer {DIFY_KNOEWLEDGE_KEY}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查 HTTP 错误
        documents = response.json().get("data", [])
        # 匹配文档 ID
        for title in book_titles:
            for doc in documents:
                if doc.get("name") == title:
                    return doc.get("id")  # 返回第一个匹配的 ID 并退出

        print("未找到匹配的文档")
        return "", 200

        # # 匹配文档 ID
        # matched_ids = []
        # for title in book_titles:
        #     for doc in documents:
        #         if doc.get("name") == title:
        #             matched_ids.append(doc.get("id"))
        #
        # if not matched_ids:
        #     print("未找到匹配的文档")
        #
        #     return "", 404
        #
        # return matched_ids

    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")

        return "", 200


if __name__ == '__main__':
    main("111","123.html")