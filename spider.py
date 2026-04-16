import requests
from bs4 import BeautifulSoup

url = "http://www1.pu.edu.tw/~tcyang/course.html"
Data = requests.get(url)
Data.encoding = "utf-8"http
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select(".team-box a")

for i in result:
	print(i)
	print()