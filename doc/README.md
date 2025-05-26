# pv-station-analysis

## 目录
- [电网数据汇总](#电网数据汇总)
- [电站分析前端服务](#电站分析前端服务)
  - [电网AI分析](#电网AI分析)


## 电网数据汇总

### 南方电网crawl逻辑
 * 调用post接口获取可开放容量html链接资源：https://95598.csg.cn/ucs/ma/wt/searchService/queryInformationList
    * 入参demo如下：{"areaCode":"0501","level":"2","classId":"b524e5cf537f4eefb42c05e2f57a436f","pageNo":1,"pageSize":15,"version":"cn","keyword":"可开放容量信息"}
    * 出参demo如下：{"sta":"00","message":"请求成功","data":{"count":7,"className":"可开放容量信息","infoList":[{"publishTime":"2025-04-08","classId":"b524e5cf537f4eefb42c05e2f57a436f","infoId":"44a632f5e43b43f6b24bf54d5d5b904e","infoTitle":"分布式光伏可开放容量查询指引","infoType":"2","link":"https://95598.csg.cn/ucs/ma/wt/business/downloadFiles?documentId=bmZkd195eF90eWZ3L3Nkay9vc3NGaWxlLzJjYTQwNzMyZTExYzQ0MDdhNjk2NWQzNzVkZGUxNzA2L1BERg==&documentType=pdf&documentName=downloadFile","className":"可开放容量信息","issuedName":"云南电网"}]}}
 * 从上述接口的出参中获取infoTitle包含“月分布式光伏”内容的所有link中的html链接
 * 对“所有link中的html链接”循环遍历进行爬取，获取html中的文档下载链接
  * 下载文档（可能是excel、pdf、doc、docx），并对文档进行解析，生成格式为:{"list":[{"provinceName":"云南省","cityName":"昆明市","countyName":"晋宁区","year":"2024年","month":"8月","substationName":"变电站名称","pv_type":"分布式","v":"电压等级(kw)","master_change_count":"主变数量","master_change_capacity":"主变容量(MVA)","open_capacity":"可开放容(MW)"}]}的数据，每50行数据通过sqlalchemy进行插入到表open_capacity操作
  * 对下载文档的url进行指纹记录，并插入到数据库中

## 电站分析前端服务

### 电网AI分析
 * 接入可视化面板
 * 