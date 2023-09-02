import json, re
import mysql.connector

# MySQL 連線
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="websiteTT"
)
mycursor = mydb.cursor()

# 建立 MySQL TABLE
careate_table_query = '''
    CREATE TABLE attraction(
        id BIGINT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        category VARCHAR(255) NOT NULL,
        description TEXT(16383) NOT NULL,
        address VARCHAR(255) NOT NULL,
        transport TEXT(16383) NOT NULL,
        mrt VARCHAR(255),
        lat DOUBLE NOT NULL,
        lng DOUBLE NOT NULL,
        images JSON NOT NULL
    )
'''
mycursor.execute(careate_table_query)

# 讀取 json 
with open("data/taipei-attractions.json", "r") as file:
    data = json.load(file)

# 建立空列表，儲存自訂字典資料
mySpots = []

# 找出 .png & .jpg 的 圖片 url
images_pattern = re.compile(r'https?://[^\n]+?\.(?:png|jpg|JPG|PNG)')

# 印出每一筆景點
for spot in data['result']['results'] :
    custom_dict = {
        'id' : spot['_id'],
        'name' : spot['name'],
        'category' : spot['CAT'],
        'description' : spot['description'],
        'address' : spot['address'],
        'transport' : spot['direction'],
        'mrt' : spot['MRT'],
        'lat' : spot['latitude'],
        'lng' : spot['longitude'],
    }

    # 找出每一個景點的圖片們
    images = re.findall(images_pattern, spot['file'])
    custom_dict['images'] = json.dumps(images)

    # 把資料存進 mySpot 列表中
    mySpots.append(custom_dict)

# 在 SQL TABLE 插入資料
for spot in mySpots : 
    sql = 'INSERT INTO attraction(id, name, category, description, address, transport, mrt, lat, lng, images) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    val = (spot['id'], spot['name'], spot['category'], spot['description'], spot['address'], spot['transport'], spot['mrt'], spot['lat'], spot['lng'], spot['images'],)
    mycursor.execute(sql, val)
    mydb.commit()
