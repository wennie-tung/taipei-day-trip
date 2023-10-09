from flask import Flask, render_template, jsonify, request, json
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import mysql.connector
import requests, random, string
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
    user="wennie",
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
@app.route("/test")
def test():
	return render_template("test.html")

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
			data = {'ok': True}
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
		return jsonify(message='error'), 500

	
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
@app.route('/api/booking', methods=['GET'])
@jwt_required()
def getBookingData():
	try:
		current_member = get_jwt_identity()
		member = current_member
		memberId = member['id']

		# 查詢資料庫
		mycursor = mydb.cursor(dictionary=True)
		sql = 'SELECT * FROM orders WHERE memberId = %s AND orderNumber IS NULL'
		mycursor.execute(sql, (memberId,))
		hadBooking = mycursor.fetchall()

		if hadBooking:
			for booking in hadBooking:
				attractionId = booking['attractionId']
				orderDate = booking['date']
				orderTime = booking['time']
				orderPrice = booking['price']
			
			mycursor = mydb.cursor(dictionary=True)
			sql = 'SELECT * FROM attraction WHERE id = %s'
			mycursor.execute(sql, (attractionId,))
			attractionResult = mycursor.fetchall()
			for result in attractionResult:
				attractionName = result['name']
				attractionAddress = result['address']
				attractionImages = json.loads(result['images'])  # 解析 "images" 欄位中的 JSON 字串
				if attractionImages:
					attractionImage = attractionImages[0]  # 取得第一個網址
				else:
					attractionImage = None # 如果沒有圖片，將其設為 None 或其他適當的值

			attraction = {
					"id": attractionId,
					"name": attractionName,
					"address": attractionAddress,
					"image": attractionImage,
				}

			data = {
				"attraction": attraction,
				"date" : orderDate,
				"time" : orderTime,
				"price" : orderPrice,
			}
			response_data = {"data" : data}

			return jsonify(response_data), 200

		else:
			response_data = {"data" : None}
			return jsonify(response_data), 200
	
	except Exception as e:
		return jsonify(message='error')


# 自訂錯誤處理程序
@jwt.invalid_token_loader
def custom_jwt_error(error):
    data = {
	    "error":True, 
		"message": "未登入系統，拒絕存取"
	}
    return jsonify(data), 403


# 建立新的預訂行程
@app.route('/api/booking', methods=['POST'])
@jwt_required()
def createBooking():
	try:
		current_member = get_jwt_identity()
		member = current_member
		attractionId = request.json.get('attractionId')
		date = request.json.get('date')
		time = request.json.get('time')
		price = request.json.get('price')
		status_notPaid = 1
	
		if member:
			try:
				memberId = member['id']
				sql = 'SELECT * FROM orders WHERE memberId = %s AND orderNumber IS NULL'
				mycursor.execute(sql, (memberId,))
				bookedBefore = mycursor.fetchall()

				if bookedBefore:
					sql = 'UPDATE orders SET attractionId = %s, date = %s, time = %s, price = %s, status = %s WHERE memberId = %s'
					val = (attractionId, date, time, price, status_notPaid, memberId)
					mycursor.execute(sql, val)
					mydb.commit()
					data = {'ok': True}
					return jsonify(data), 200
				else:
					sql = 'INSERT INTO orders(memberId, attractionId, date, time, price, status) VALUES(%s, %s, %s, %s, %s, %s)'
					val = (memberId, attractionId, date, time, price, status_notPaid)
					mycursor.execute(sql, val)
					mydb.commit()
					data = {'ok': True}
					return jsonify(data), 200
			
			except mysql.connector.Error as err:
				# 資料庫操作發生異常，處理錯誤
				print(f"資料庫錯誤: {err}")
				# 回復到資料操作之前的狀態
				mydb.rollback() 
				# 回傳錯誤訊息
				data = {
					"error":True, 
					"message": "建立失敗，輸入不正確或其他原因"
					}
				return jsonify(data), 400
	
	except Exception as e:
		data = {
			"error": True,
  			"message": "伺服器內部錯誤"
		}
		return jsonify(message='error'), 500

@app.route('/api/booking', methods=['DELETE'])
@jwt_required()
def deleteBookingData():
	try:
		current_member = get_jwt_identity()
		member = current_member
		memberId = member['id']

		if member:
			try:
				memberId = member['id']
				sql = 'DELETE FROM orders WHERE memberId = %s AND orderNumber IS NULL'
				mycursor.execute(sql, (memberId,))
				mydb.commit()
				data = {'ok': True}
				return jsonify(data), 200

			except Exception as e:
				data = {
					"error": True,
  					"message": "伺服器內部錯誤"
				}
				return jsonify(message='error'), 500

	except Exception as e:
		data = {
			"error": True,
  			"message": "伺服器內部錯誤"
		}
		return jsonify(message='error'), 500
	
# order API
@app.route('/api/orders', methods=['POST'])
@jwt_required()
def createNewOrder():
	try:
		current_member = get_jwt_identity()
		member = current_member
		memberId = member['id']
		newOrderData = request.get_json()
		attractionName = newOrderData['order']['trip']['attraction']['name']
		attractionAddress = newOrderData['order']['trip']['attraction']['address']
		attractionImg = newOrderData['order']['trip']['attraction']['image']
		contactName = newOrderData['order']['contact']['name']
		contactEmail = newOrderData['order']['contact']['email']
		contactPhone = newOrderData['order']['contact']['phone']
		# print(contactName)
		# print(contactEmail)
		# print(contactPhone)
		result = verify_payment(newOrderData)
		orderNumber = result['order_number']
		status = result['status']
		msg = result['msg']
		print(status)
		# status_notPaid = 1
		# print(memberId)
		# print(orderNumber)
		# print(result)

		if result['status'] == 0:
			sql = 'UPDATE orders SET orderNumber = %s, status = %s, attractionName = %s, attractionAddress = %s, attractionImg = %s, contactName = %s, contactEmail = %s, contactPhone = %s WHERE memberId = %s AND orderNumber IS NULL'
			val = (orderNumber, status, attractionName, attractionAddress, attractionImg, contactName, contactEmail, contactPhone, memberId)
			mycursor.execute(sql, val)
			mydb.commit()
			response_data = {
				"number" : orderNumber,
				"payment" : {
					"status" : status,
					"message" : "付款成功"
				}
			}
			data = {
				"data" : response_data,
			}
			return jsonify(data), 200
		
		elif result['status'] == 734:
			sql = 'UPDATE orders SET orderNumber = %s, status = %s, contactName = %s, contactEmail = %s, contactPhone = %s WHERE memberId = %s AND orderNumber IS NULL'
			val = (orderNumber, status, contactName, contactEmail, contactPhone, memberId)
			mycursor.execute(sql, val)
			mydb.commit()
			response_data = {
				"number" : orderNumber,
				"payment" : {
					"status" : status,
					"message" : msg
				}
			}
			data = {
				"data" : response_data,
			}
			return jsonify(data), 200
		
		elif result['status'] == 84:
			sql = 'UPDATE orders SET orderNumber = %s, status = %s, contactName = %s, contactEmail = %s, contactPhone = %s WHERE memberId = %s AND orderNumber IS NULL'
			val = (orderNumber, status, contactName, contactEmail, contactPhone, memberId)
			mycursor.execute(sql, val)
			mydb.commit()
			response_data = {
				"number" : orderNumber,
				"payment" : {
					"status" : status,
					"message" : msg
				}
			}
			data = {
				"data" : response_data,
			}
			return jsonify(data), 200
		
		elif result['status'] == 91:
			sql = 'UPDATE orders SET orderNumber = %s, status = %s, contactName = %s, contactEmail = %s, contactPhone = %s WHERE memberId = %s AND orderNumber IS NULL'
			val = (orderNumber, status, contactName, contactEmail, contactPhone, memberId)
			mycursor.execute(sql, val)
			mydb.commit()
			response_data = {
				"number" : orderNumber,
				"payment" : {
					"status" : status,
					"message" : msg
				}
			}
			data = {
				"data" : response_data,
			}
			return jsonify(data), 200
		
		elif result['status'] == 10039:
			sql = 'UPDATE orders SET orderNumber = %s, status = %s, contactName = %s, contactEmail = %s, contactPhone = %s WHERE memberId = %s AND orderNumber IS NULL'
			val = (orderNumber, status, contactName, contactEmail, contactPhone, memberId)
			mycursor.execute(sql, val)
			mydb.commit()
			response_data = {
				"number" : orderNumber,
				"payment" : {
					"status" : status,
					"message" : msg
				}
			}
			data = {
				"data" : response_data,
			}
			return jsonify(data), 200
		
		else:
			data = {
				"error": True,
  				"message": "訂單建立失敗"
			}
			return jsonify(data), 400

	except Exception as e:
		data = {
			"error": True,
  			"message": "伺服器內部錯誤"
		}
		return jsonify(data), 500

@app.route('/api/order/<int:orderNumber>', methods=['GET'])
# @jwt_required()
def getOrderData(orderNumber):
	try:
		print(orderNumber)
		# current_member = get_jwt_identity()
		# member = current_member
		# memberId = member['id']
		# orderNumber = request.args.get('number')
		mycursor = mydb.cursor(dictionary=True)
		sql = 'SELECT * FROM orders WHERE orderNumber = %s'
		# val = (orderNumber)
		mycursor.execute(sql, (orderNumber,))
		searchResult = mycursor.fetchone()
		# print(searchResult)

		# 找到訂單
		if searchResult:
			# 處理 price 格式
			price_float = searchResult['price']
			# 將浮點數轉換為整數後，再轉為字串
			price_int = int(price_float)
			formatted_price = str(price_int)

			# 處理 phone 格式
			# 將數字轉換為字串，再判斷長度
			phone_number = searchResult['contactPhone']
			phone_str = str(phone_number)
			if len(phone_str) == 9:
    			# 在字串前面加上 "0" 以達到 10 個數字的格式
				formatted_phone = "0" + phone_str
			else:
				formatted_phone = phone_str

			attraction = {
				"id" : searchResult['id'],
				"name" : searchResult['attractionName'],
				"address" : searchResult['attractionAddress'],
				"image" : searchResult['attractionImg']
			}
			# print(attraction)

			trip = {
				"attraction" : attraction,
				"date" : searchResult['date'],
				"time" : searchResult['time']
			}

			contact = {
				"name" : searchResult['contactName'],
				"email" : searchResult['contactEmail'],
				"phone" : formatted_phone
			}

			datas = {
				"number" : searchResult['orderNumber'],
				"price" : formatted_price,
				"trip" : trip,
				"contact" : contact,
				"status" : searchResult['status']
			}

			data = {
				"data" : datas
			}
			return jsonify(data), 200

		else:
			data = {
				"data" : None
			}
			return jsonify(data), 200
		
	except Exception as e:
		return jsonify({"error": True, "message": "伺服器內部錯誤"}), 500
	

def verify_payment(newOrderData):
	# 設置訂單編號
	random_digits = ''.join(random.choice(string.digits) for _ in range(4))
	orderDate = newOrderData['order']['date']
	date = orderDate.replace("-", "")
	order_number = date + random_digits 

    # TapPay 付款 API 
	api_url = 'https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime'

    # partner key
	partner_key = 'partner_opU2Vb6n9jmSyEbNRcLJ9eDN35cUEbIVRpnoj4nu0SwEbqlrdWifbeZP'
	
	# merchant id
	merchant_id = "wehelpwennie_CTBC"

    # 從POST請求中獲取用戶的Prime值 
	prime = newOrderData['prime']

    # 構建請求主體
	payload = {
        "partner_key": partner_key,
        "prime": newOrderData['prime'],
        "amount": newOrderData['order']['price'],
        "merchant_id": merchant_id,
        "details": newOrderData['order']['trip']['attraction']['name'],
		"order_number": order_number,
        "cardholder": {
            "phone_number": newOrderData['order']['contact']['phone'],
            "name": newOrderData['order']['contact']['name'],
            "email": newOrderData['order']['contact']['email'],
        }
    }

    # 設置請求標頭
	headers = {
        'content-type': 'application/json',
        'x-api-key': partner_key
    }

    # 發送POST請求
	response = requests.post(api_url, json=payload, headers=headers)

    # 獲取API的回應
	api_response = response.json()
	print(api_response.get('status'))

    # 根據API回應做相應處理
	if api_response.get('status') == 0:
        # 付款驗證成功
		print('付款驗證成功')
		print(api_response)
		data = {
			"status" : api_response.get('status'),
			"order_number" : api_response.get('order_number'),
			"msg" :  api_response.get('msg')
		}
		return data
	
	elif api_response.get('status') == 734:
        # 付款驗證失敗
		print('付款驗證失敗')
		print(api_response)
		data = {
			"status" : api_response.get('status'),
			"order_number" : api_response.get('order_number'),
			"msg" :  api_response.get('msg')
		}
		return data
	
	elif api_response.get('status') == 84:
		print('付款驗證失敗')
		print(api_response)
		data = {
			"status" : api_response.get('status'),
			"order_number" : api_response.get('order_number'),
			"msg" :  api_response.get('msg')
		}
		return data
	
	elif api_response.get('status') == 91:
		print('付款驗證失敗')
		print(api_response)
		data = {
			"status" : api_response.get('status'),
			"order_number" : api_response.get('order_number'),
			"msg" :  api_response.get('msg')
		}
		return data
	
	elif api_response.get('status') == 10039:
		print('付款驗證失敗')
		print(api_response)
		data = {
			"status" : api_response.get('status'),
			"order_number" : api_response.get('order_number'),
			"msg" :  api_response.get('msg')
		}
		return data
	
	else:
		print('付款驗證失敗')
		print(api_response)
		data = {
			"status" : api_response.get('status'),
			"order_number" : api_response.get('order_number'),
			"msg" :  api_response.get('msg')
		}
		return data

app.run(host="0.0.0.0", debug=True, port=3000)