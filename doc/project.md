# pv-station-analysis

## 目录
- [电网数据汇总](#电网数据汇总)
- [电站分析前端服务](#电站分析前端服务)
  - [电网AI分析](#电网AI分析)


## 电网数据汇总

### 南方电网crawl逻辑
 #### 爬南方电网文件定时任务
  * 调用post接口获取可开放容量html链接资源：https://95598.csg.cn/ucs/ma/wt/searchService/queryInformationList
   * 入参demo如下：{"areaCode":"0501","level":"2","classId":"b524e5cf537f4eefb42c05e2f57a436f","pageNo":1,"pageSize":15,"version":"cn","keyword":"可开放容量信息"}
   * 出参demo如下：{"sta":"00","message":"请求成功","data":{"count":7,"className":"可开放容量信息","infoList":[{"publishTime":"2025-04-08","classId":"b524e5cf537f4eefb42c05e2f57a436f","infoId":"44a632f5e43b43f6b24bf54d5d5b904e","infoTitle":"分布式光伏可开放容量查询指引","infoType":"2","link":"https://95598.csg.cn/ucs/ma/wt/business/downloadFiles?documentId=bmZkd195eF90eWZ3L3Nkay9vc3NGaWxlLzJjYTQwNzMyZTExYzQ0MDdhNjk2NWQzNzVkZGUxNzA2L1BERg==&documentType=pdf&documentName=downloadFile","className":"可开放容量信息","issuedName":"云南电网"}]}}
  * 从上述接口的出参中获取infoTitle包含“月分布式光伏”内容的所有link中的html链接
  * 对“所有link中的html链接”循环遍历进行爬取，获取html中的文档下载链接
  * 下载文档（可能是excel、pdf、doc、docx）到oss服务并对下载文档的url进行指纹记录，
 #### ai解析南方电网文件并落库定时任务
  * 并对pdf文档进行分片成多张图片
  * 用VL-Max-Latest模型解析，生成格式为:{"list":[{"provinceName":"云南省","cityName":"昆明市","countyName":"晋宁区","year":"2024年","month":"8月","substationName":"变电站名称","pv_type":"分布式","v":"电压等级(kw)","master_change_count":"主变数量","master_change_capacity":"主变容量(MVA)","open_capacity":"可开放容(MW)"}]}的数据
  * 每50行数据通过sqlalchemy进行插入到表open_capacity操作

### 电站分析前端服务
#### 前端功能说明：
 * 前端系统名称为"TCL智能分析系统"
 * 界面设计要求：整个界面需要高大上。以中国红为主色调。界面需要包含tcl的水印。
 * 首页包含两个模块："可开放容量"和"AI分析记录"
 * "可开放容量"模块，该模块用于查询数据库的可开放容量信息，具有以下功能：
   *  可开放容量列表分页查询：调用post接口：http://localhost:5000/open_capacity/list  。入参demo如下：{"provinceName":"云南省","cityName":"昆明市","countyName":"晋宁区","year":"2024","month":"8","substationName":"变电站名称","pageNo":"1","pageSize":"20"}，出参demo如下：{"code":"0","message":"请求成功","data":{"count":1,"list":[{"provinceName":"云南省","cityName":"昆明市","countyName":"晋宁区","year":"2024","month":"8","substationName":"变电站名称","pv_type":"分布式","v":"电压等级(kw)","master_change_count":"主变数量","master_change_capacity":"主"}]}}
   *  可开放容量列表分页查询：查询条件包括：省、市、县、年、月、变电站名称（模糊）,查询结果列表的列名包括：省、市、县区、年、月、变电站名称、电站类型、电压等级（kV）、主变数量、主变容量（MVA）、可开放容量（MW）、创建时间
   *  右上角有一个浮动的"AI助手",用龙头做图标，点击后弹出一个对话框，对话框中包含一个输入框，用户输入问题，点击"智能分析"按钮，调用post接口：http://localhost:5000/common/ai_sql_analysis_api  。入参demo如下：{"input":{"scene":"open_capacity","user_request":"分析呈贡区各个变电站的可开放容量变化情况"}}，出参demo如下：{"code":"0","message":""}
 * "AI分析记录"模块，该模块用于查看用户自定义AI分析功能生成的结果，具有以下功能：
   *  AI分析记录列表分页查询：调用post接口：http://localhost:5000/common/ai_analysis_record/list  。入参demo如下：{"scene"："场景","pageNo":"1","pageSize":"20"}，出参demo如下：{"code":"0","message":"请求成功","data":{"count":1,"list":[{"id":"1","scene_name":"场景名称","user_request":"用户问题","sql_query":"ai生成的sql","oss_url":"ai生成的HTML文件OSS地址"}]}}
   *  oss_url是个html文件链接，点击可以跳转到新页面并展示

### 电网AI分析切入点
 * 用户自定义AI分析功能接口
  * 入参：场景（值默认为"可开放容量"）、用户要求
  * 出参：html格式的界面
  * 逻辑：
   * 根据场景匹配到具体的表结构
   * 将用户要求和表结构信息拼接到prompt中，prompt包含如下内容：Text-to-SQL任务的说明、数据库表结构信息、用户问题相关的领域知识、提示或其他约束条件、需要生成SQL的用户问题
   * 根据prompt调用call_deepseek()方法生成查询的sql
   * 执行sql，接收sql的查询结果
   * 将查询结果组成prompt2，调用call_deepseek()方法生成html格式的文件
   * 将html文件上传到oss系统中，并返回oss的url
   * 将oss的url、场景、用户要求、创建时间都记录在AI分析记录表中

### 注意的细节
 * 35+KW和10KW的电站，单位不一致
   * 单位MVA和KVA的转换关系为：MVA=KVA*1000
   * MW和KW的换算