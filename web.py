from flask import Flask, render_template, request
from datetime import datetime

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
import requests
from bs4 import BeautifulSoup

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)

app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎來到朱晉呈的網站</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=晉呈&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/account>POST傳值</a><hr>"
    link += "<a href=/math>次方與根號計算</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    link += "<a href=/search_form>教師搜尋系統 (依姓名關鍵字)</a><hr>"
    link += "<a href=/spider1>爬取子青老師本學期課程</a><hr>"
    link += "<a href=/movie>爬取即將上映電影</a><br>"

    return link

@app.route("/movie")
def movie():
    keyword = request.args.get("keyword", "")

    # 1. 搜尋表單 (稍微美化)
    search_form = f"""
        <style>
            .container {{ display: flex; flex-wrap: wrap; gap: 20px; justify-content: flex-start; }}
            .card {{ 
                width: 200px; border: 1px solid #ddd; padding: 10px; 
                border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                display: flex; flex-direction: column; align-items: center;
            }}
            .card img {{ width: 100%; height: 280px; object-fit: cover; border-radius: 4px; }}
            .title {{ 
                height: 3em; line-height: 1.5em; overflow: hidden; 
                text-align: center; font-weight: bold; margin-bottom: 10px;
                display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
            }}
            .link {{ margin-top: auto; font-size: 0.9em; }}
        </style>
        
        <form action="/movie" method="get" style="margin-bottom: 20px;">
            <input type="text" name="keyword" placeholder="輸入電影名稱..." value="{keyword}" style="padding:5px;">
            <button type="submit" style="padding:5px 15px;">搜尋</button>
            <a href="/movie"><button type="button" style="padding:5px 15px;">顯示全部</button></a>
        </form>
        <hr>
    """

    url = "https://www.atmovies.com.tw/movie/next/"
    data = requests.get(url)
    data.encoding = "utf-8"
    sp = BeautifulSoup(data.text, "html.parser")
    result = sp.select(".filmListAllX li")

    movie_results = "<div class='container'>" # 開始 Flex 容器
    found_count = 0

    for i in result:
        title = i.find("img").get("alt")
        
        if keyword == "" or keyword.lower() in title.lower():
            found_count += 1
            introduce = "https://www.atmovies.com.tw" + i.find("a").get("href")
            poster_url = "https://www.atmovies.com.tw" + i.find("img").get("src")
            
            # 使用卡片式佈局
            movie_results += f"""
                <div class="card">
                    <div class="title">{title}</div>
                    <a href="{introduce}" target="_blank">
                        <img src="{poster_url}" alt="海報">
                    </a>
                    <div class="link">
                        <a href="{introduce}" target="_blank">電影資訊介面</a>
                    </div>
                </div>
            """

    movie_results += "</div>" # 結束 Flex 容器

    header = f"<h1>電影查詢結果：{keyword if keyword else '全部'}</h1>"
    if found_count == 0:
        movie_results = f"<p>找不到與「{keyword}」相關的電影。</p>"

    return search_form + header + movie_results
@app.route("/search_form")
def search_form():
    form_html = "<h2>教師搜尋系統</h2>"
    form_html += "<form action='/read2' method='GET'>"
    form_html += "請輸入姓名關鍵字: <input type='text' name='keyword' required> "
    form_html += "<input type='submit' value='開始搜尋'>"
    form_html += "</form><hr>"
    form_html += "<a href='/'>返回首頁</a>"
    return form_html

@app.route("/spider1")
def spider1():
    R = ""
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url, verify=False)
    Data.encoding = "utf-8"
    
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".team-box a")

    for i in result:
        R += i.text + i.get("href")+"<br>"
        
    return R

@app.route("/read2")
def read2():
    Result = ""
    keyword = request.args.get("keyword", "")
    if not keyword:
        return "請輸入關鍵字再進行搜尋！"
    db = firestore.client()
    collection_ref = db.collection("PU")    
    docs = collection_ref.get()    
    for doc in docs: 
        teacher = doc.to_dict()
        if keyword in teacher.get("name", ""):
            Result += str(teacher) + "<br>"
    if Result == "":
        Result = "抱歉,查無此關鍵字姓名之老師資料"
    return Result


@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("PU")    
    docs = collection_ref.get()    
    for doc in docs:         
        Result += "文件內容：{}".format(doc.to_dict()) + "<br>"    
    return Result


@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"
@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime = str(now))
@app.route("/me")
def me():
    now = datetime.now()
    return render_template("mis1102.html")
@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name=user,dep = d,course=c)
@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")
@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        try:
            x = float(request.form["x"])
            y = float(request.form["y"])
            opt = request.form["opt"]
           
            if opt == "pow":
                # 次方計算：x 的 y 次方
                result = x ** y
                msg = f"{x} 的 {y} 次方 = {result}"
            elif opt == "root":
                # 根號計算：x 的 y 次根號 (即 x 的 1/y 次方)
                if x < 0 and y % 2 == 0:
                    msg = "錯誤：負數不能開偶數次方根"
                else:
                    result = x ** (1/y)
                    msg = f"{x} 的 {y} 次方根 = {result}"
            else:
                msg = "無效的運算"
        except Exception as e:
            msg = f"計算出錯：{str(e)}"
           
        return f"<h1>計算結果</h1><p>{msg}</p><a href='/math'>重新計算</a>"
   
    return render_template("math.html")
if __name__ == "__main__":
    app.run(debug = True)
