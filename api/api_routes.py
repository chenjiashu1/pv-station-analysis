from flask import Flask, jsonify, request
import requests
import os

from flask_cors import CORS


from open_capacity.nan_fang_crawl.nan_fang_crawl import open_capacity_nan_fang_crawl

app = Flask(__name__)
CORS(app)  # 全局启用跨域支持

@app.route('/test')
def test():
    return jsonify("test")

@app.route('/open_capacity/nan_fang_crawl')
def open_capacity_nan_fang_crawl_api():
    return open_capacity_nan_fang_crawl()


if __name__ == '__main__':
    app.run(debug=True)

