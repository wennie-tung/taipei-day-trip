from flask import Flask, render_template, jsonify, request, json
app=Flask(__name__)
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True

# Session 金鑰匙
app.secret_key = "SecrectKey202308"

# MySQL
import mysql.connector

# 連接到本機的 MySQL
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
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
	offset = (page - 1) * per_page
	if page == 0:
		sql = 'SELECT * FROM attraction WHERE mrt = %s OR name LIKE %s'
		val = ( keyword,'%' + keyword + '%',)
	else:
		sql = 'SELECT * FROM attraction LIMIT %s, %s'
		val = (offset, per_page)
	mycursor = mydb.cursor(dictionary=True)
	mycursor.execute(sql, val)
	searchResult = mycursor.fetchall()

	for result in searchResult:
		result['images'] = json.loads(result['images'])

	myResult = {"nextPage": page+1, "data": searchResult}

	if searchResult:
		response_data = myResult
	else:
		response_data = {"data": None}
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
		return searchResult
	except Exception as e:
		return jsonify({"error": True, "message": "伺服器內部錯誤"}), 500


app.run(host="0.0.0.0", port=3000)