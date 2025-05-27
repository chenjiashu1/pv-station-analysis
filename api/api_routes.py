from flask import Flask, jsonify, request
import requests
import os

from flask_cors import CORS

from open_capacity.nan_fang_crawl.nan_fang_crawl import open_capacity_nan_fang_crawl, parse_document

app = Flask(__name__)
CORS(app)  # 全局启用跨域支持

@app.route('/test')
def test():
    return jsonify("test")


@app.route('/open_capacity/nan_fang_crawl', methods=['POST'])
def open_capacity_nan_fang_crawl_api():
    return open_capacity_nan_fang_crawl()

@app.route('/parse_document', methods=['POST'])
def parse_document_api():
    input = request.get_json().get('input')
    filepath = input.get("filepath")
    return parse_document(filepath)


if __name__ == '__main__':
    app.run(debug=True)

