import requests
from bs4 import BeautifulSoup

url = "https://mis-1102.vercel.app/me"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.find("a")

for i in result:
	print(i.text)
	print()