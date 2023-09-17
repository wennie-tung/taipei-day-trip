from flask import Flask, render_template, jsonify, request, json
app = Flask(__name__, static_folder="public", static_url_path="/")
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True

# MySQL
import mysql.connector

# 連接到本機的 MySQL
mydb = mysql.connector.connect(
    host="localhost",
    user="wennie",
    password="password",
    database="websiteTT"
)
# mycursor = mydb.cursor()

# Pages
@app.route("/")
def index():
	return render_template("index.html")
@app.route("/attraction/<id>")
def attraction(id):
	return render_template("attraction.html")
@app.route("/booking")
def booking():
	return render_template("booking.html")
@app.route("/thankyou")
def thankyou():
	return render_template("thankyou.html")

# API
@app.route("/api/attractions", methods=['GET'])
def getAttraction():
	page = int(request.args.get("page", 0))
	keyword = request.args.get("keyword", None)
	per_page = 12
	offset = page * per_page

	# SQL 查询
	sql = 'SELECT * FROM attraction'
	where_filter = ''
	val = ()

	if keyword:
		where_filter = 'WHERE (mrt = %s OR name LIKE %s)'
		keyword_pattern = f'%{keyword}%'
		val = (keyword, keyword_pattern)

	# 完整指令
	sql += ' ' + where_filter + ' LIMIT %s OFFSET %s'
	val += (per_page, offset)

	mycursor = mydb.cursor(dictionary=True)
	mycursor.execute(sql, val)
	searchResult = mycursor.fetchall()

	for result in searchResult:
		result['images'] = json.loads(result['images'])

	# 如果有下一頁，回傳 nextPage = page+1，否則為 null
	has_nextPage = (len(searchResult) >= per_page)
	has_result = (len(searchResult) > 0)

	if has_nextPage and has_result:
		response_data = {"nextPage":page+1, "data":searchResult}
	elif not has_nextPage and has_result:
		response_data = {"nextPage":None, "data":searchResult}
	else:
		response_data = {"nextPage":None, "data":None}
	return jsonify(response_data)


@app.route("/api/attraction/<int:attractionId>", methods=['GET'])
def getAttractionById(attractionId):
	try:
		mycursor = mydb.cursor(dictionary=True)
		sql = 'SELECT * FROM attraction WHERE id = %s'
		val = (attractionId,)
		mycursor.execute(sql, val)
		searchResult = mycursor.fetchone()

		# attractionId 錯誤
		if not searchResult:
			return jsonify({"error": True, "message": "景點編號不正確"}), 400

		# 使用 json.loads() 將 images 字串轉成 list
		searchResult['images'] = json.loads(searchResult['images'])

		data = {
			"data":searchResult
		}

		if searchResult:
			return jsonify(data)
		
	except Exception as e:
		return jsonify({"error": True, "message": "伺服器內部錯誤"}), 500


@app.route("/api/mrts", methods=['GET'])
def getMrt():
	try:
		mycursor = mydb.cursor()
		sql = 'SELECT mrt_counts.mrt FROM (SELECT mrt, COUNT(*) AS mrt_count FROM attraction WHERE mrt IS NOT NULL GROUP BY mrt) AS mrt_counts ORDER BY mrt_counts.mrt_count DESC'
		mycursor.execute(sql)
		searchResult = mycursor.fetchall()
		# 把查詢結果撈出裝在 list 內
		mrt_list = [result[0] for result in searchResult]
		return jsonify({"data": mrt_list})
	except Exception as e:
		return jsonify({"error": True, "message": "伺服器內部錯誤"}), 500


app.run(host="0.0.0.0", port=3000)