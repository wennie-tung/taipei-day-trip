from flask import Flask, render_template, jsonify, request, json
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import mysql.connector
app = Flask(__name__, static_folder="public", static_url_path="/")
app.config["JSON_AS_ASCII"]=False
app.config["TEMPLATES_AUTO_RELOAD"]=True
app.config['JWT_SECRET_KEY'] = 'wehelp-taipei-day-trip'

# Token 時效性 7 天
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 604800
jwt = JWTManager(app)

# 連接到本機的 MySQL
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="websiteTT"
)
mycursor = mydb.cursor()

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

# 註冊 API
@app.route("/api/user", methods=['POST'])
def signUp():
	name = request.json.get('name')
	email = request.json.get('email')
	password = request.json.get('password')
	sql = 'SELECT * FROM member WHERE email = %s'
	mycursor.execute(sql, (email,))
	existing_account = mycursor.fetchall()

	try:
		if existing_account:
			data = {
				'error' : True,
				'message': '此 email 已存在，請用其他 email 註冊'
				}
			return jsonify(data), 400
		else:
			sql = 'INSERT INTO member(name, email, password) VALUES(%s, %s, %s)'
			val = (name, email, password)
			mycursor.execute(sql, val)
			mydb.commit()
			data = {'ok': 'true'}
			return jsonify(data)
		
	except Exception as e:
		data = {
			'error' : True,
			'message': '伺服器內部錯誤'
		}
		return jsonify(data), 500


# 登入 API
@app.route("/api/user/auth", methods=['PUT'])
def signIn():
	email = request.json.get('email')
	password = request.json.get('password')
	sql = 'SELECT * FROM member WHERE email = %s and password = %s'
	mycursor.execute(sql, (email,password))
	user_data = mycursor.fetchone()

	try:
		if user_data:
			id, name, email, password = user_data
			user_identity = {
				"id" : id,
				"name" : name,
				"email" : email,
			}
			access_token = create_access_token(identity = user_identity)
			data = {
				"token" : access_token
				}
			return jsonify(data), 200
		else:
			data = {
				"error": True,
  				"message": "帳號或密碼錯誤"
				}
			return jsonify(data), 400
		
	except Exception as e:
		data = {
			"error": True,
  			"message": "伺服器內部錯誤"
		}
		return jsonify(message='"error'), 500

	
@app.route('/api/user/auth', methods=['GET'])
@jwt_required()
def verifyToken():
	try:
		# 取得 token 內的資料
		current_user = get_jwt_identity()

		if current_user:
			# 從用戶資訊回傳給前端
			user_id = current_user['id']
			user_name = current_user['name']
			user_email = current_user['email']

			data = {
				'id' : user_id,
				'name' : user_name,
				'email' : user_email,
			}
			response_data = {"data" : data}
			return jsonify(response_data), 200
		
		else:
			data = { data : None }
			return jsonify(data)
		
	except Exception as e:
		return jsonify(message='error'), 401
	

# booking API
# @app.route('/api/booking', methods=['GET'])
# def 

# 建立新的預訂行程
@app.route('/api/booking', methods=['POST'])
@jwt_required()
def creatBooking():
	try:
		current_member = get_jwt_identity()
		member = current_member
	
		if member:
			# 從用戶資訊回傳給前端
			memberId = member['id']
			print(memberId)
		else:
			data = { data : None }
			return jsonify(data)
		
		# print('user_id:' + user_id)
		attractionId = request.json.get('attractionId')
		date = request.json.get('date')
		time = request.json.get('time')
		price = request.json.get('price')
		print(attractionId, date, time, price)
		data = {'ok': 'true'}
		return jsonify(data)
	except Exception as e:
		return jsonify(message='"error'), 500

# @app.route('/api/booking', methods=['DELETE'])

	

app.run(host="0.0.0.0", debug=True, port=3000)