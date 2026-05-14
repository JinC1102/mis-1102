from flask import Flask, render_template, request, make_response, jsonify
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
    link += "<a href=/movie>爬取即將上映電影</a><hr>"
    link += "<a href=/spidermovie>讀取開眼電影即將上映影片，寫入Firestore</a><hr>"
    link += "<a href=/searchMovie>從資料庫搜尋電影</a><hr>"
    link += "<a href=/road>台中市十大肇事路口</a><hr>"
    link += "<a href=/weather>查詢縣市天氣預報</a><hr>"
    link += "<a href=/rate>本週新片進DB</a><hr>"

    return link

@app.route("/webhook", methods=["POST"])
def webhook():
    # build a request object
    req = request.get_json(force=True)
    # fetch queryResult from json
    action = req["queryResult"]["action"]
    #msg = req["queryResult"]["queryText"]
    #info = "我是朱晉呈的機器人,動作：" + action + "； 查詢內容：" + msg
    if (action == "rateChoice"):
        rate = req["queryResult"]["parameters"]["rate"]
        info = "我是朱晉呈的設計機器人,您選擇的電影分級是：" + rate + "，相關電影：\n"
    db = firestore.client()

    collection_ref = db.collection("電影含分級")
    docs = collection_ref.get()
    result = ""
    for doc in docs:
    dict = doc.to_dict()
    if rate in dict["rate"]:
        result += "片名：" + dict["title"] + "\n"
        result += "介紹：" + dict["hyperlink"] + "\n\n"
    info += result
    
    return make_response(jsonify({"fulfillmentText": info}))

@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate

@app.route("/weather", methods=["GET", "POST"])
def weather():
    R = "<h2>縣市天氣查詢</h2>"
    R += """
        <form action="/weather" method="post">
            請輸入欲查詢縣市(如: 宜蘭縣): <input type="text" name="city">
            <input type="submit" value="查詢">
        </form><hr>
    """
   
    if request.method == "POST":
        city = request.form.get("city").strip().replace("台", "臺")
        # 注意：請確保這是有效的授權碼，或是從氣象署申請自己的 key
        auth_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
        params = {
            "Authorization": "rdec-key-123-45678-011121314", # 請替換為正確的 Key
            "locationName": city,
            "format": "JSON"
        }
       
        try:
            response = requests.get(auth_url, params=params)
            json_data = response.json()
           
            # 檢查是否有抓到對應縣市的資料
            if "records" in json_data and json_data["records"]["location"]:
                loc_data = json_data["records"]["location"][0]
               
                # 取得縣市名稱
                location_name = loc_data["locationName"]
               
                # 取得天氣現象 (Wx) - 通常在第 0 個 element
                weather_desc = loc_data["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
               
                # 取得降雨機率 (PoP) - 通常在第 1 個 element
                rain_prob = loc_data["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
               
                R += f"<h3>{location_name} 最新天氣預報</h3>"
                R += f"目前狀況：{weather_desc}<br>"
                R += f"降雨機率：{rain_prob}%<br>"
            else:
                R += f"<p style='color:red'>找不到「{city}」的資料。請確認輸入正確（例如：宜蘭縣）。</p>"
               
        except Exception as e:
            R += f"查詢出錯：{str(e)}"
           
    R += "<br><a href='/'>返回首頁</a>"
    return R

@app.route("/road")
def road():
    R = "<h1>台中市十大肇事路口(113年10月)作者:朱晉呈</h1><br>"

    url = "https://newdatacenter.taichung.gov.tw/api/v1/no-auth/resource.download?rid=a1b899c0-511f-4e3d-b22b-814982a97e41"
    headers = {'User-Agent': 'Mozilla/5.0'}
    Data = requests.get(url, headers=headers)
    #print(Data.text)
    JsonData = json.loads(Data.text)
    for item in JsonData:
        R += item["路口名稱"] + ",原因:"+ item["主要肇因"] + ",件數:"+ item["總件數"] +"<br>"

    return R

@app.route("/searchMovie")
def searchMovie():
    # 獲取使用者輸入的關鍵字 (預設為空字串)
    keyword = request.args.get("keyword", "")
   
    # 建立搜尋表單 UI
    R = "<h2>從資料庫搜尋電影</h2>"
    R += "<form action='/searchMovie' method='GET'>"
    R += f"<input type='text' name='keyword' placeholder='輸入片名關鍵字'' value='{keyword}'> "
    R += "<input type='submit' value='開始查詢'>"
    R += "</form><hr>"

    # 如果沒有輸入關鍵字，就先只顯示表單
    if not keyword:
        R += "<p>請在上方輸入關鍵字查詢資料庫中的電影。</p>"
        R += "<br><a href='/'>返回首頁</a>"
        return R

    R += f"<h3>關鍵字「{keyword}」的查詢結果：</h3>"

    # 連線到 Firestore 資料庫
    db = firestore.client()
    collection_ref = db.collection("電影2B")  # 對應你 /spidermovie 寫入的集合
    docs = collection_ref.stream()

    found_count = 0
    for doc in docs:
        movie = doc.to_dict()
        title = movie.get("title", "")
       
        # 關鍵字篩選邏輯 (轉成小寫比對，避免大小寫差異找不到)
        if keyword.lower() in title.lower():
            found_count += 1
            movie_id = doc.id
            picture = movie.get("picture", "")
            hyperlink = movie.get("hyperlink", "")
            showDate = movie.get("showDate", "")
           
            # 組合回傳的 HTML 內容，包含編號、片名、上映日期、介紹頁與海報
            R += "<div>"
            R += f"<h4>編號: {movie_id}</h4>"
            R += f"<h4>片名: {title}</h4>"
            R += f"<p>上映日期: {showDate}</p>"
            R += f"<p><a href='{hyperlink}' target='_blank'>電影資訊頁</a></p>"
            R += f"<img src='{picture}' width='200'><br>"
            R += "</div><hr>"

    # 如果沒找到符合的電影
    if found_count == 0:
        R += "<p>抱歉，資料庫中找不到符合條件的電影，請嘗試其他關鍵字或先執行爬蟲寫入資料。</p>"

    R += "<br><a href='/'>返回首頁</a>"
    return R

@app.route("/spidermovie")
def spidermovie():
    R = ""
    db = firestore.client()

    import requests
    from bs4 import BeautifulSoup
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text.replace("更新時間：","")

    result=sp.select(".filmListAllX li")
    info = ""
    total = 0
    for item in result:
      total += 1
      movie_id = item.find("a").get("href").replace("/movie/", "").replace("/", "")
      title = item.find(class_="filmtitle").text
      picture = "http://www.atmovies.com.tw" + item.find("img").get("src")
      hyperlink = "http://www.atmovies.com.tw" + item.find("a").get("href")

      showDate = item.find(class_="runtime").text[5:15]
      info += movie_id + "\n" + title + "\n" + picture + "\n" + hyperlink + "\n" + showDate +"\n\n"

      doc = {
        "title": title,
        "picture": picture,
        "hyperlink": hyperlink,
        "showDate": showDate,
        "lastUpdate": lastUpdate
    }
     
      doc_ref = db.collection("電影2B").document(movie_id)
      doc_ref.set(doc)

    #print(info)
    print(lastUpdate)
    R += "網站最新更新日期:" + lastUpdate + "<br>"
    R += "總共爬取"+ str(total) + "部電影到資料庫"
    R += "<br><a href='/'>返回首頁</a>"
    return R

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
            <a href='/'><button type="button" style="padding:5px 15px;">返回首頁</button></a>
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
                        <a href="{introduce}" target="_blank">電影資訊頁</a>
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
