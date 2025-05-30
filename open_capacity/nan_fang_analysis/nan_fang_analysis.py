import json
import os

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

    # 对oss_pdf_url的每一页进行切分成图片
    output_dir = os.path.splitext(local_file_path)[0] + "_images"
    image_paths = convert_pdf_to_images(local_file_path, output_dir)

    prompt = f"""
    # 你是专业的文件数据提炼和整理师 
    # 该文件是{AreaName}的{link_name}
    # 任务：解析出文件表格中所有和”可开放容量“相关的信息。
    # 要求如下： 
     * 1、用json格式输出，不允许有```json和```。
     * 2、根据如下场景对输出结果进行区分:
         * 2.1、\"35kV及以上变电站\"输出内容格式如下:[{{"provinceName":"省份名称","cityName":"城市名称","countyName":"呈县/区名称区","township":"所属乡镇","year":"年","month":"月","substationName":"变电站名称\",\"open_capacity\":\"可开放容量（KW）\",\"v\":\"电压等级（kV）\",\"master_change_count\":\"主变数量\",\"master_change_capacity\":\"主变容量（KVA）\"}}] 
           * 2.1.1、35kV及以上变电站需要注意\"单位转化\"：主变容量需要从MVA转成KVA，可开放容量需要从MW转为KW
         * 2.2、\"10kV公用线路\"输出内容格式如下:[{{"provinceName":"省份名称","cityName":"城市名称","countyName":"呈县/区名称区","year":"年","month":"月\",\"substationName\":\"变电站名称\",\"line_name\":\"线路名称\",\"open_capacity\":\"可开放容量（KW）\",\"rated_capacity\":\"额定容量（kW）\",\"max_load\":\"最大负荷（kW）\"}}]
         * 2.3、\"公用配变\"输出内容格式如下:[{{"provinceName":"省份名称","cityName":"城市名称","countyName":"呈县/区名称区","township":"所属乡镇","year":"年","month":"月\",\"substationName\":\"变电站名称或公变名称\",\"line_name\":\"线路名称\",\"open_capacity\":\"可开放容量（KW）\",\"rated_capacity\":\"额定容量（kW）\"}}]
     * 6、要求输出：不要包含其他解释内容，只有json内容
            """

    # 循环每一张图片， 调用qwen-vl-plus模型进行图片识别出json结果
    all_results = []
    for image_path in image_paths:
        result_json = call_qwen_vl_max_latest(prompt, image_path)
        try:
            result = json.loads(result_json)
            # 插入数据库
            if len(result) > 0:
                insert_open_capacity(result)
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误: {e}, 原始内容: {result_json}")
    update_SourceInfo_toDb(sourceInfo.id)
    print(f"ai_parse_document_and_db-oss_url====数据解析并落库完成:{oss_pdf_url}")
