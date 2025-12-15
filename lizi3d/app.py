# app.py
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')  # 渲染模板文件

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50000, debug=True)
