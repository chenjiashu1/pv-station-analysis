from flask import Flask, jsonify, request
import requests
import os

from flask_cors import CORS

from ai.ai_analysis import ai_sql_analysis, ai_parse_nanfang_document_and_db_v2
from database.models import insert_open_capacity
from open_capacity.nan_fang_crawl.nan_fang_crawl import open_capacity_nan_fang_crawl, open_capacity_nan_fang_parseToDb
from utils.fileUtil import uploadToHuaweiyunOssBySource_url, uploadLocalFileToOss

app = Flask(__name__)
CORS(app)  # 全局启用跨域支持


@app.route('/test')
def test():
    return jsonify("test")


# ai语义化sql分析
@app.route('/common/ai_sql_analysis_api', methods=['POST'])
def ai_sql_analysis_api():
    input = request.get_json().get('input')
    scene = input.get('scene')
    user_request = input.get('user_request')
    return ai_sql_analysis(scene, user_request)


@app.route('/common/uploadLocalFile_api', methods=['POST'])
def uploadLocalFile_api():
    input = request.get_json().get('input')
    filePath = input.get("filePath")
    fileName = input.get("fileName")
    return uploadLocalFileToOss(filePath, fileName)


# 爬南方电网文件
@app.route('/open_capacity/nan_fang_crawl_api', methods=['POST'])
def open_capacity_nan_fang_crawl_api():
    input = request.get_json().get('input')
    areaCode = input.get("areaCode")
    return open_capacity_nan_fang_crawl(areaCode)


@app.route('/open_capacity/test/uploadToHuaweiyunOssBySource_url_api', methods=['POST'])
def uploadToHuaweiyunOssBySource_url_api():
    input = request.get_json().get('input')
    url = input.get("url")
    fileName = input.get("fileName")
    return uploadToHuaweiyunOssBySource_url(url, fileName)


@app.route('/open_capacity/nan_fang_parseToDb_api', methods=['POST'])
def open_capacity_nan_fang_parseToDb_api():
    return open_capacity_nan_fang_parseToDb()


@app.route('/open_capacity/test/ai_parse_document_and_db_api', methods=['POST'])
def ai_parse_document_api():
    input = request.get_json().get('input')
    url = input.get("url")
    return ai_parse_nanfang_document_and_db_v2(url)


@app.route('/open_capacity/test/insert_open_capacity_api', methods=['POST'])
def insert_open_capacity_api():
    input = request.get_json().get('input')
    return insert_open_capacity(input)


if __name__ == '__main__':
    app.run(debug=True)
