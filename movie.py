import requests
from bs4 import BeautifulSoup

url = "https://www.atmovies.com.tw/movie/next/"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select(".filmListAllX li")
for i in result:
	print(i.find("img").get("alt"))
	print("https://www.atmovies.com.tw" + i.find("a").get("href"))
	print("https://www.atmovies.com.tw" + i.find("img").get("src"))
	print()