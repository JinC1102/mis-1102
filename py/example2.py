def Split(x):
	x = x.split(",")
	school = x[0].replace("我是","")
	print(f"學校:{school}")
	print(f"姓名{x[2]}")

if_name_=="_main_"
	Name = "我是靜宜大學,資管二B,朱晉呈"
	Split(Name)
