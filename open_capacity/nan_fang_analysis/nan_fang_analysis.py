import json
import os

from Scripts import fitz

from database.models import find_not_db_SourceInfo, insert_open_capacity, update_SourceInfo_toDb
from open_capacity.nan_fang_crawl.nan_fang_crawl import findAreaNameByAreaCode
from utils.aiUtil import call_qwen_vl_max_latest
from utils.fileUtil import download_oss_file, convert_pdf_to_images


def open_capacity_nan_fang_parseToDb():
    sourceInfos = find_not_db_SourceInfo()
    if sourceInfos:
        for sourceInfo in sourceInfos:
            ai_parse_nanfang_document_and_db_v2(sourceInfo)
    return "南方电网可开放容量数据解析并落库完成"


# ai解析南方电网文件并落库
def ai_parse_nanfang_document_and_db_v2(sourceInfo):
    oss_pdf_url = sourceInfo.oss_url
    sourceLinkInfo = json.loads(sourceInfo.sourceLinkInfo)

    document_type = sourceLinkInfo['document_type']
    areaCode = sourceLinkInfo['areaCode']
    AreaName = findAreaNameByAreaCode(areaCode)
    link_name = sourceLinkInfo['link_name']

    # 判断document_type是否为pdf，否则提示“不支持该文件解析”
    if document_type.lower() != "pdf":
        raise ValueError("不支持该文件解析，仅支持PDF文件")

    # 下载OSS文件到本地
    local_file_path = download_oss_file(oss_pdf_url)
    
    # 将pdf根据表格进行切分成多个子pdf
    doc = fitz.open(local_file_path)
    sub_pdfs = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        tables = page.find_tables()
        
        if tables.tables:
            # 如果页面有表格，则创建一个新的PDF文档
            sub_doc = fitz.open()
            sub_page = sub_doc.new_page(width=page.rect.width, height=page.rect.height)
            sub_page.show_pdf_page(sub_page.rect, doc, page_num)
            
            # 保存子PDF
            sub_pdf_path = f"{os.path.splitext(local_file_path)[0]}_page_{page_num}.pdf"
            sub_doc.save(sub_pdf_path)
            sub_pdfs.append(sub_pdf_path)
            sub_doc.close()

            # 对子PDF进行切片
            output_dir = os.path.splitext(sub_pdf_path)[0] + "_images"
            image_paths = convert_pdf_to_images(sub_pdf_path, output_dir)

            # 循环每一张图片， 调用qwen-vl-plus模型进行图片识别出json结果
            for image_path in image_paths:
                result_json = call_qwen_vl_max_latest(prompt, image_path)
                try:
                    result = json.loads(result_json)
                    # 插入数据库
                    if len(result) > 0:
                        insert_open_capacity(result)
                except json.JSONDecodeError as e:
                    print(f"JSON 解析错误: {e}, 原始内容: {result_json}")
    doc.close()
    # 更新数据库
    update_SourceInfo_toDb(sourceInfo.id)
    print(f"ai_parse_nanfang_document_and_db_v2-oss_url====数据解析并落库完成:{oss_pdf_url}")
    
    return "数据解析并落库完成："+oss_pdf_url
