import os
import sys
import random
import time

from flask import *
import sqlite3, hashlib, os
# from PIL import Image
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt
from image_retreival import *
from flask_jwt_extended.utils import get_jti
from werkzeug.utils import secure_filename
from flask_jwt_extended import (
	JWTManager, create_access_token, create_refresh_token,
	jwt_required, get_jwt_identity, get_jwt, set_access_cookies
)
from colour import main_colour
import pandas as pd
#----------Classes--------------#
class User:
	def __init__(self, email):
		command = "SELECT * FROM user WHERE LOWER(email)=\""+email+"\";"
		db = Database()
		data = db.select(command)[0]
		self.UID = data[0]
		self.name = data[1]
		self.email = email
		self.password = data[3]
		self.company = data[4]
		self.phone = data[5]

class Project:
	def __init__(self, id: int):
		command = f"SELECT * FROM project WHERE PID={id};"
		db = Database()
		data = db.select(command)[0]
		self.PID = data[0]
		self.name = data[1]
		self.UID = data[2]
		self.date = data[3]

class Database:
	def __init__(self):
		self.con = sqlite3.connect('database.db')
		self.cur = self.con.cursor()

	def select(self, command):
		self.cur.execute(command)
		data = self.cur.fetchall()
		return data

	def insert(self, command):
		self.cur.execute(command)
		self.con.commit()
		count = self.cur.rowcount
		return count
	
	def update(self, command):
		self.cur.execute(command)
		self.con.commit()
		count = self.cur.rowcount
		return count
	
	def delete(self, command):
		self.cur.execute(command)
		self.con.commit()
		count = self.cur.rowcount
		return count

#-------------------------------#

#--------Functions--------------#
app = Flask(__name__)
app.secret_key = 'random string'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['JWT_SECRET_KEY'] = 'zephyros'
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access','refresh']

jwt = JWTManager(app)

session = {}
blacklist = []

# @jwt.token_in_blacklist_loader
def token_in_blacklist(decrypted_token):
	jti = get_jti(decrypted_token)
	return jti in blacklist
	# return True

# @jwt.expired_token_loader
# def expired_token_load():
# 	return redirect(url_for('/tokenrefresh'))


@app.route('/')
def home():
	name=""
	loggedIn = False
	if 'email' in session:
		loggedIn = True
		u = User(session['email'])
		name = u.name
	return render_template('index.html', loggedIn=loggedIn, name=name, session=session)

@app.route('/myprojects')
def myProject():
	if 'email' not in session:
		return redirect(url_for('loginForm'))
	print('access:', session['access_token'])
	loggedIn = True
	u = User(session['email'])
	name = u.name
	return render_template('home.html', loggedIn=loggedIn, name=name, session=session)


def dbAccess(com):
	con = sqlite3.connect('database.db')
	cur = con.cursor()
	cur.execute(com)
	con.commit()
	return cur

@app.route('/registrationForm')
def registrationForm():
	if 'email' in session:
		return redirect(url_for('home'))
	loggedIn=False
	name = ""
	return render_template('registration.html', error="", loggedIn=loggedIn, name=name, key="")

@app.route('/registration', methods=['POST'])
def registration():
	if request.method == "POST":
		email = request.form['email']
		password = request.form['password']
		re_password = request.form['re-password']
		username = request.form['username']
		company = request.form['company']
		phone = request.form['phone']
		if password != re_password:
			error = "Passwords must match"
			return render_template('registration.html',error=error)
		key = random.randint(100000, 999999)
		UID = random.randint(0,999999)
		command = f"INSERT into user VALUES({UID}, \"{username}\",\"{email}\",\"{password}\", \"{company}\", \"{phone}\", {key});"
		print(command)
		db = Database()
		db.insert(command)
		return render_template('registration.html', error='',loggedIn=False, name="", key=key)

@app.route("/loginForm")
def loginForm():
	print('in loginForm')
	if 'email' in session:
		return redirect(url_for('home'))
	else:
		print('in else')
		loggedIn=False
		name = ""
		return render_template('login.html', error='',loggedIn=loggedIn,name=name)

@app.route("/login", methods=['POST', 'GET'])
def login():
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		if request.form['key'] == "":
			error = "Invalid credentials"
			return render_template('login.html',error=error), 402
		key = int(request.form['key'])
		if is_valid(email, password, key):
			session['email'] = email
			session['key'] = key
			session['access_token'] = create_access_token(identity=email, expires_delta=timedelta(minutes=60))
			session['refresh_token'] = create_refresh_token(identity=email, expires_delta=timedelta(days=7))
			print('Success:', session)
			return redirect(url_for('home'))
		else:
			error = 'Invalid UserId / Password'
			return render_template('login.html', error=error), 402

def is_valid(email, password, key):
	print(email, password, key)
	db = Database()
	data = db.select('SELECT email, password, key FROM user')
	for row in data:
		[print(i,type(i), end="\t") for i in row]
		print(row[0].lower() == email.lower() and row[1] == password and row[2] == key)
		if row[0].lower() == email.lower() and row[1] == password and row[2] == key:
			return True
	return False

@app.route("/logout")
def logout():
	if "email" not in session:
		return redirect(url_for("home"))
	blacklist.append(get_jti(session['access_token']))
	session.clear()
	print("session:",session)
	print("Blacklist:",blacklist)
	return redirect(url_for('home'))

@app.route("/getprojects", methods = ['GET'])
@jwt_required()
def getprojects():
	if request.method=='GET':
		print('in getProjects')
		print('access',session['access_token'])
		if 'id' in session:
			session.pop('id')
		u = User(session['email'])
		UID = u.UID
		db = Database()
		data = db.select("SELECT * FROM project WHERE UID="+str(UID))
		ret={}
		for i in range(len(data)):
			count = db.select("SELECT COUNT(*) FROM task WHERE PID="+str(data[i][0])+";")[0][0]
			ret[i] = "{\"count\":\""+str(count)+"\",\"name\":\""+data[i][1]+"\",\"date\":\""+str(data[i][3]+"\",\"PID\":"+str(data[i][0])+"}")
		if ret:
			#print(ret)
			return jsonify(ret)
		return jsonify({'msg':'Empty'})

@app.route('/getimage')
@jwt_required()
def get_image():
	name = request.args.get('name')
	if name == None:
		return {"msg":"Invalid Request"}, 402
	return {"value": f'static/output/{name}.png'}, 200

@app.route("/createProject", methods=['POST'])
def createproject():
	print('in CreateProject')
	if 'email' not in session:
		return redirect(url_for('loginForm'))
	if request.method=='POST':
		name = request.form['name']
		print(name)
		name = name.upper()
		named_tuple = time.localtime() # get struct_time
		time_string = time.strftime("%Y/%m/%d", named_tuple)
		u = User(session['email'])
		db = Database()
		data = db.select('SELECT PID from project;')
		pid = random.randint(0,999999)
		while pid in data:
			pid = random.randint(0,999999)
		command = 'INSERT INTO project VALUES('+str(pid)+',\"'+name+'\",'+str(u.UID)+',\"'+str(time_string)+'\");'
		print(command)
		ret = db.insert(command)
		print(ret)
		return redirect(url_for('myProject'))

@app.route('/project')
def displayProject():
	if 'email' not in session:
		return redirect(url_for('loginForm'))
	print('in DisplayProject')
	PID = request.args.get('id')
	if PID is None:
		if "id" in session:
			PID = session['id']
		else:
			print('No PID:', session)
			return redirect(url_for('home'))
	session['id']=PID
	print("session: ", session)
	db = Database()
	name = db.select('SELECT Name from project where PID='+str(PID))[0][0]
	return render_template('project.html',PName=name, session=session, PID=PID,loggedIn='email' in session,Name=User(session['email']).name)

@app.route('/getTasks',methods=['GET'])
@jwt_required()
def getTasks():
	if request.method=='GET':
		PID = request.args.get('PID')
		print('in GetTasks')
		db = Database()
		data = db.select('SELECT * FROM task WHERE PID='+str(PID))
		ret = {}
		for i in range(len(data)):
			ret[i]="{\"TID\":"+str(data[i][0])+",\"PID\":"+str(data[i][1])+",\"type\":\""+data[i][2]+"\",\"state\":\""+data[i][3]+"\",\"time\":\""+data[i][4]+"\",\"date\":\""+data[i][5]+"\"}"
		if ret:
			#print(ret)
			return jsonify(ret)
		return jsonify({'msg':'Empty'})

@app.route('/createTask',methods=['POST'])
def createTask():
	if request.method=='POST':
		if 'id' not in session:
			return redirect(url_for('home'))
		print('PID:',session['id'])
		PID = session['id']
		Ttype = request.form['type']
		print('in CreateTask')
		ref = time.localtime()
		date = time.strftime("%Y/%m/%d", ref)
		time_now = str(ref.tm_hour)+':'+str(ref.tm_min)+':'+str(ref.tm_sec)
		print(time_now+'::'+date)
		db = Database()
		data = db.select('SELECT TID from task;')
		tid = random.randint(0,999999)
		while tid in data:
			tid = random.randint(0,999999)
		command = 'INSERT INTO task VALUES('+str(tid)+','+str(PID)+',\"'+Ttype.upper()+'\",\"NEW\",\"'+time_now+'\",\"'+date+'\");'
		db = Database()
		print(command)
		ret = db.insert(command)
		print('Number of rows affected:',ret)
		return redirect('/project?id='+PID)

@app.route('/task')
def DisplayTask():
	if 'email' not in session:
		return redirect(url_for('home'))
	if 'id' not in session:
		return redirect(url_for('project'))
	loggedIn=True
	tid = request.args.get('tid')
	db = Database()
	det = db.select('SELECT * FROM task WHERE TID='+tid)[0]
	tid,pid,ttype,state,timee,date = det
	print(det)
	u = User(session['email'])
	if ttype=="RETRIEVE":
		return render_template('search.html', Name=u.name, loggedIn=loggedIn)
	if ttype=="STYLE":
		return render_template('style_transfer.html', Name=u.name, loggedIn=loggedIn)
	print(tid,pid,ttype,state,timee,date)
	pname = db.select('SELECT Name from project where PID='+str(pid))[0][0]
	return render_template('task.html',TID=tid,PID=pid,ttype=ttype,state=state,time=timee,date=date,loggedIn=loggedIn,Name=u.name,PName=pname, session=session)

@app.route('/changeState', methods=['POST'])
def changeState():
	if request.method=='POST':
		print('in changeState')
		tid = request.form['tid']
		db = Database()
		command = 'UPDATE task SET state=\"RUNNING\" WHERE TID='+str(tid)
		res = db.update(command)
		print('No. of Rows affected:',res)
		return redirect('/task?tid='+str(tid))

@app.route('/trainTask',methods=['POST'])
def trainTask():
	if request.method=='POST':
		tid = request.args.get('tid')
		files = request.files.getlist('files')
		db = Database()
		DIDs = db.select('SELECT DID from design;')
		print(DIDs)
		PID = session['id']
		key = 40
		pname = db.select('SELECT Name from project where PID='+str(PID))[0][0]
		print('pname:',pname)
		for file in files:
			iDID = random.randint(0,999999)
			while iDID in DIDs:
				iDID = random.randint(0,999999)
			DIDs.append(iDID)
			file_path = os.path.join(app.config['UPLOAD_FOLDER'], pname)
			image_path = os.path.join(file_path, file.filename)
			print(image_path)
			if not os.path.exists(file_path):
				os.makedirs(file_path)
			file.save(image_path)
			fp = open(image_path, 'rb')
			image = fp.read()
			fp.close()
			image = bytearray(image)
			for index, values in enumerate(image):
				image[index] = values ^ key
			f_out = open(image_path, 'wb')
			f_out.write(image)
			f_out.close()
			command = 'INSERT INTO design VALUES('+str(iDID)+',\"'+image_path+'\",'+str(tid)+');'
			res = 1#db.insert(command)
			print(command)
			print('No. of rows affected:',res)
		print(tid,files)
		ret={}
		ret['tid']=tid
		ret['files']=str(files)
		db.update('UPDATE task set state="FINISHED" where TID='+str(tid))
		#print(ret)
		return redirect('/task?tid='+str(tid))

# @app.route('/tokenrefresh')
# @jwt_required(refresh=True)
# def token_refresh():
# 	email = session['email']
# 	session["access_token"] = create_access_token(identity=email)

@app.after_request
def token_refresh(response):
	try:
		exp_timestamp = get_jwt()["exp"]
		now = datetime.now(timezone.utc)
		print('checking refresh')
		target_timestamp = datetime.timestamp(now + timedelta(minutes=5))
		if target_timestamp > exp_timestamp:
			print('refreshing')
			email = session['email']
			access_token = create_access_token(identity=email, expires_delta=timedelta(minutes=20))
			set_access_cookies(response, access_token)
			print('access token Refreshed')
		return response
	except (RuntimeError, KeyError):
		# Case where there is not a valid JWT. Just return the original respone
		return response

path='image_desc.csv'
df=pd.read_csv(path)
"""
for i in df.index:
  df['description'][i]=df['description'][i].split("|")
  df['description'][i]= [i for i in df['description'][i] if i]
  print(i)

#creation of inverted index
inverted_index={}

for row in df.index:
  for tag in df['description'][row]:
    if('no' not in tag):
      tag=lemmatize_sentence(tag)
      if(tag not in inverted_index.keys()):
        inverted_index[tag]=[]
      inverted_index[tag].append(row)
  print(row)
#Document Frequency
idf={}
for doc in inverted_index.keys():
  idf[doc]=1/len(inverted_index[doc])


with open("inverted_index.json", "w") as outfile:
    json.dump(inverted_index, outfile)

with open("idf.json", "w") as outfile:
    json.dump(idf, outfile)
"""
f = open('inverted_index.json',)
inverted_index= json.load(f)
f = open('idf.json',)
idf= json.load(f)
image_name=[df['image'][i] for i in df.index]

@app.route('/getimages', methods=['GET'])
@jwt_required()
def getimages():
	if "email" not in session:
		return redirect(url_for('home'))
	book = session['book']
	res = input_query(book, inverted_index, idf)
	res0 = [i for i in res if i[1] > 0.8]
	# ref = [i for i in res if i[1] < 0.5]
	res1 = [image_name[i[0]] for i in res0]
	res2 = [url_for('static', filename='MasterShirt/'+i) for i in res1]
	return jsonify({"res":res2})


@app.route('/result',methods = ['POST', 'GET'])
def result():
	if 'email' not in session:
		return redirect(url_for('home'))
	if request.method == 'POST':
		book = request.form['book']
		session['book'] = book
		res=input_query(book,inverted_index,idf)
		name=User(session['email']).name
		return render_template("result.html", res=res,image_name=image_name, loggedIn='email' in session, Name=name, session=session)
		
		
@app.route('/getcolabs', methods=['GET'])
@jwt_required()
def getColabs():
	if 'email' not in session:
		redirect(url_for('home'))
	db = Database()
	company = User(session['email']).company
	command = 'SELECT UID, Name, email FROM user WHERE company=\"' + str(company) + '\" and key!='+str(session['key'])+';'
	data = db.select(command)
	print(data)
	ret = {}
	if data:
		for i in range(len(data)):
			ret[i] = "{\"UID\":"+str(data[i][0])+", \"Name\":\""+str(data[i][1])+"\", \"email\":\""+str(data[i][2])+"\"}"
		print(ret)
		return jsonify(ret)
	return jsonify({"msg":"Empty"})


@app.route('/share', methods=['GET'])
def shareProject():
	UID = request.args.get('UID')
	db = Database()
	ids = db.select('SELECT SID FROM share;')
	id = random.randint(0,999999)
	if id in ids:
		id = random.randint(0,999999)
	check = db.select('SELECT * FROM share where PID='+str(session['id'])+' AND UID='+str(UID)+";")
	if len(check)>0:
		print('check failed. User already added to project')
		return render_template('project.html',PName=Project(session['id']).name, session=session, PID=session['id'], loggedIn='email' in session, Name=User(session['email']).name)
	check = db.select('SELECT * FROM project where PID='+str(session['id'])+' AND UID='+str(UID)+";")
	if len(check)>0:
		print('check failed. User already added to project')
		return render_template('project.html',PName=Project(session['id']).name, session=session, PID=session['id'], loggedIn='email' in session, Name=User(session['email']).name)
	command = 'INSERT INTO share VALUES('+str(id)+','+str(session['id'])+','+str(UID)+');'
	print(command)
	ret = db.insert(command)
	print('Number of rows affected:', ret)
	return render_template('project.html',PName=Project(session['id']).name, session=session, PID=session['id'], loggedIn='email' in session, Name=User(session['email']).name)


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
 return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/pattern', methods= ["GET", "POST"])
def pattern():
    return render_template('pattern.html', Name=User(session['email']).name, loggedIn="email" in session)


@app.route('/pattern_model',methods=[ "GET",'POST'])
def pattern_model():
    if request.method == 'POST':
        img1= request.files['img1']
        img2 = request.files['img2']
        print(img1)
        print(img2)
        secure_img1 = secure_filename(img1.filename)
        secure_img2 = secure_filename(img2.filename)
        img1.save(os.path.join("static/style_transfer/pattern/style", secure_img1))
        print('File successfully uploaded ' + secure_img1 + ' to the database!')
        img2.save(os.path.join("static/style_transfer/pattern/content", secure_img2))
        print('File successfully uploaded ' + secure_img2 + ' to the database!')

        os.system('python pattern.py --content_img_dir ./static/style_transfer/pattern/content/ \
                               --content_img '+ secure_img2+' \
                               --style_imgs_dir ./static/style_transfer/pattern/style/ \
                               --style_imgs '+ secure_img1 + '\
                               --style_imgs_weights 1  \
                               --max_iterations 100 \
                               --max_size 600 \
                               --img_name '+ secure_img1.split(".")[0]+secure_img2.split(".")[0] + '\
                               --content_weight 1 \
                               --device /cpu:0 \
                               --original_colors \
                               --img_output_dir ./static/style_transfer/pattern/ \
                               --verbose')
        result="./static/style_transfer/pattern/"+secure_img1.split(".")[0]+secure_img2.split(".")[0]+"/"+ secure_img1.split(".")[0]+secure_img2.split(".")[0] +".png"
    return jsonify(result)

@app.route('/texture', methods= ["GET", "POST"])
def texture():
    return render_template('texture.html', name=User(session['email']).name, loggedIn="email" in session)


@app.route('/texture_model',methods=[ "GET",'POST'])
def texture_model():
    if request.method == 'POST':
        img1= request.files['img1']
        img2 = request.files['img2']
        print(img1)
        print(img2)
        secure_img1 = secure_filename(img1.filename)
        secure_img2 = secure_filename(img2.filename)
        img1.save(os.path.join("static/style_transfer/texture/style", secure_img1))
        print('File successfully uploaded ' + secure_img1 + ' to the database!')
        img2.save(os.path.join("static/style_transfer/texture/content", secure_img2))
        print('File successfully uploaded ' + secure_img2 + ' to the database!')

        os.system('python pattern.py --content_img_dir ./static/style_transfer/texture/content/ \
                               --content_img '+ secure_img2+' \
                               --style_imgs_dir ./static/style_transfer/texture/style/ \
                               --style_imgs '+ secure_img1 + '\
                               --style_imgs_weights 1  \
                               --max_iterations 100 \
                               --max_size 600 \
                               --img_name '+ secure_img1.split(".")[0]+secure_img2.split(".")[0] + '\
                               --content_weight 1 \
                               --device /cpu:0 \
                               --original_colors \
                               --img_output_dir ./static/style_transfer/texture/ \
                               --verbose')
        result="./static/style_transfer/texture/"+secure_img1.split(".")[0]+secure_img2.split(".")[0]+"/"+ secure_img1.split(".")[0]+secure_img2.split(".")[0] +".png"
    return jsonify(result)


@app.route('/colour', methods= ["GET", "POST"])
def colour():
    return render_template('colour.html', name=User(session['email']).name, loggedIn="email" in session)

@app.route('/colour_model',methods=[ "GET",'POST'])
def colour_model():
    if request.method == 'POST':
        img1= request.files['img1']
        img2 = request.files['img2']
        print(img1)
        print(img2)
        secure_img1 = secure_filename(img1.filename)
        secure_img2 = secure_filename(img2.filename)
        img1.save(os.path.join("static/style_transfer/colour/style", secure_img1))
        print('File successfully uploaded ' + secure_img1 + ' to the database!')
        img2.save(os.path.join("static/style_transfer/colour/content", secure_img2))
        print('File successfully uploaded ' + secure_img2 + ' to the database!')
        main_colour(secure_img1,secure_img2)
        result = "./static/style_transfer/colour/output/"+secure_img1.split(".")[0]+secure_img2.split(".")[0]+".jpg"
    return jsonify(result)

@app.route("/get_access_token", methods=['GET'])
def give_access_token():
	print(session)
	if 'access' in session:
		return jsonify({"access": session['access']})
	else:
		return jsonify({"msg":"Empty"})



@app.route('/elements',methods = ['GET'])
def elements():
	return render_template('elements.html')

@app.route('/leftsidebar', methods=['GET'])
def leftsidebar():
	return render_template('left-sidebar.html')


print('open')
app.debug = True
app.run()
print('close')