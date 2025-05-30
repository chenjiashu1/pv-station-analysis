from datetime import datetime

from flask import Flask, jsonify, request

from utils.aiUtil import call_deepseek

from database.models import table_structure_map, execute_sql, table_name_map, insert_ai_analysis_record
from utils.fileUtil import upload_content_to_oss


def ai_sql_analysis(scene, user_request):
    # 1. 根据场景匹配表结构
    # 实际使用时应根据具体业务逻辑动态选择表结构
    table_structure = table_structure_map.get(scene)
    if not table_structure:
        return jsonify({"error": "Invalid scene"}), 400
    generalSqlPrompt = f"""
    请根据以下信息生成SQL查询语句：

    - 需要生成SQL的用户问题：{user_request}
    - 数据库表结构：{table_structure}
    - Text-to-SQL任务说明：根据用户问题和数据库表结构，返回一个SQL查询语句。
    - 要求输出：仅返回有效的SQL语句，不要包含其他解释内容。
    - 输出结果不能包含```sql和```
    - 遵循sql_mode为ONLY_FULL_GROUP_BY的模式
    - 查询结果不能超过5000行数据
    """

    print(f"ai_sql_analysis-generalSqlPrompt===={generalSqlPrompt}")
    # 2. 构造 Prompt 生成 SQL
    sql_query = call_deepseek(generalSqlPrompt)
    print(f"ai_sql_analysis-sql_query===={sql_query}")
    # 3. 执行 SQL 查询（此处为伪代码，实际需连接数据库）
    query_result = execute_sql(sql_query)
    # query_result = [{"provinceName": "广东省", "cityName": "广州市", "open_capacity": "100MW"}]
    table_name = table_name_map.get(scene)
    # 4. 构造 Prompt2 生成 HTML
    ai_sql_analysis_prompt = f"""
    # 您是专业的数据分析专家
    # 请分析以下数据：{query_result}，着重关注：{table_name}
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