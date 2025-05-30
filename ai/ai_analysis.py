import json
from datetime import datetime

from flask import jsonify

from database.models import execute_sql, insert_ai_analysis_record, findSceneInfoByScene, insert_open_capacity, \
    update_SourceInfo_toDb  # 新增插入南方数据方法
from utils.aiUtil import call_deepseek, urlConvertToAliFileObject, call_qwen_long  # 新增调用qwen-vl-plus方法
from utils.fileUtil import upload_content_to_oss, download_oss_file  # 新增pdf转图片方法


def ai_sql_analysis(scene, user_request):
    # 1. 根据场景匹配表结构
    # 实际使用时应根据具体业务逻辑动态选择表结构
    table_structure = findSceneInfoByScene(scene).table_structure
    if not table_structure:
        return jsonify({"error": "Invalid scene"}), 400
    general_sql_prompt = f"""
    请根据以下信息生成SQL查询语句：

    - 需要生成SQL的用户问题：{user_request}
    - 数据库表结构：{table_structure}
    - Text-to-SQL任务说明：根据用户问题和数据库表结构，返回一个SQL查询语句。
    - 要求输出：仅返回有效的SQL语句，不要包含其他解释内容。
    - 输出结果不能包含```sql和```
    - 遵循sql_mode为ONLY_FULL_GROUP_BY的模式
    - 查询结果不能超过5000行数据
    """

    print(f"ai_sql_analysis-general_sql_prompt===={general_sql_prompt}")
    # 2. 构造 Prompt 生成 SQL
    sql_query = call_deepseek(general_sql_prompt)
    print(f"ai_sql_analysis-sql_query===={sql_query}")
    # 3. 执行 SQL 查询（此处为伪代码，实际需连接数据库）
    query_result = execute_sql(sql_query)
    # query_result = [{"provinceName": "广东省", "cityName": "广州市", "open_capacity": "100MW"}]
    scene_name = findSceneInfoByScene(scene).scene_name
    # 4. 构造 Prompt2 生成 HTML
    ai_sql_analysis_prompt = f"""
    # 您是专业的数据分析专家
    # 请分析以下数据：{query_result}，着重关注：{scene_name}
    # 要求
        - 使用简洁清晰美观的图形和表格的方式呈现
        - 包含中文标题和单位
        - 以HTML格式输出结果。
        - 输出结果仅返回有效的html内容，不要包含其他解释内容，不能包含```html和```
    """
    print(f"ai_sql_analysis-ai_sql_analysis_prompt===={ai_sql_analysis_prompt}")
    html_content = call_deepseek(ai_sql_analysis_prompt)
    print(f"ai_sql_analysis-html_content===={html_content}")
    fileName = f"{scene}-{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
    # 5. 保存 HTML 文件并上传至 OSS（此处为伪代码）
    html_url = upload_content_to_oss(html_content, fileName)
    # html_url = "https://oss.example.com/ai-result/123.html"
    print(f"ai_sql_analysis-html_url===={html_url}")

    # 6. 记录分析结果到数据库
    insert_ai_analysis_record(scene, user_request, sql_query, html_url)
    return jsonify({"html_url": html_url})


def call_qwen_long_parse_document(local_file_path):
    prompt = """
    # 你是专业的数据提炼和整理师
    ## 任务：从文件的所有表格中解析出所有和可开放容量相关的信息。
    ## 要求如下：
        * 1、用json格式输出，不允许有```json和```，格式如下:[{"id":10,"provinceName":"云南","cityName":"昆明","countyName":"呈贡区","year":"2024","month":"9","substationName":"110kV 吴家营变 #1 主变","pv_type":"分布式","v":"110","master_change_count":"1","master_change_capacity":"50","open_capacity":"19","create_time":""}]
        * 2、要求输出：不要包含其他解释内容，只有json内容
            """

    file_object = urlConvertToAliFileObject(local_file_path)
    return call_qwen_long(prompt, file_object)


def ai_parse_document_and_db(sourceInfo):
    oss_url = sourceInfo.oss_url
    local_file_path = download_oss_file(oss_url)
    # 解析文档
    parsed_data_string = call_qwen_long_parse_document(local_file_path)

    if not parsed_data_string:
        print(f"解析文档失败: {oss_url}")
        return ""
    try:
        parsed_data = json.loads(parsed_data_string)
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
        return ""
    print(f"ai_parse_document====成功解析出{len(parsed_data)}条可开放容量的数据")

    # 每50行数据插入一次数据库
    batch_size = 50
    for i in range(0, len(parsed_data), batch_size):
        batch_data = parsed_data[i:i + batch_size]
        insert_open_capacity(batch_data)
    update_SourceInfo_toDb(sourceInfo.id)
    print(f"ai_parse_document_and_db-oss_url====数据解析并落库完成:{oss_url}")

