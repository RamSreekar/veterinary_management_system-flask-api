from flask import Flask, request, render_template, redirect, url_for, jsonify
import pymongo
import datetime
import copy
from flask_cors import CORS, cross_origin
from bson import ObjectId
from bson.json_util import dumps,loads
from werkzeug.security import generate_password_hash, check_password_hash
import os
import dns

app = Flask(__name__)

CORS(app)
cors = CORS(app, resources={
		r"/*" : {
			"origins" : "*"
		}
	})

db_url = os.environ.get('MONGODB_MYCLUSTER_URL')
mongo = pymongo.MongoClient(db_url)

@app.route('/signup', methods=['GET','POST'])
def signup():
	usersDB = mongo.vmsDB.users
	if request.method == 'POST':
		name = request.json['name']
		email = request.json['email']
		pwd = request.json['pwd']
		usertype = request.json['userType']
		hash_pass = generate_password_hash(pwd)
		reg_user = usersDB.find_one({'email':email})
		if not reg_user:
			res = usersDB.insert_one({'name':name, 'email':email, 'pwd':hash_pass, 'userType':usertype})
			x = {
			    "name": name,
			    "email": email,
			    "pwd": pwd,
			    "userType" : usertype,
			    "status" : 200
			}
			if res:
				return jsonify(x)
			else:
				err1 =  {
					"Error" : 'Insert not successful', 
			    	"status" : 202
			    } 

		else:
			err = {
				"Error" : 'User already Registered', 
			    "status" : 202
			    }
			return jsonify(err)

	if request.method == 'GET':
		return '<h1>VMS - Signup route</h1>'
		
@app.route('/signin',methods=['GET','POST'])
def signin():
	usersDB = mongo.vmsDB.users
	if request.method == 'POST':
		email = request.json['email']
		pwd = request.json['pwd']
		reg_user = usersDB.find({'email' : email})
		user = copy.deepcopy(reg_user)
			
		if list(reg_user):
			user2 = list(user)
			dbpwd = str(user2[0]['pwd'])
			matched = check_password_hash(dbpwd, pwd)
		
			if matched:
				ut = user2[0]['userType']
				uname = user2[0]['name']
				uid = str(user2[0]['_id'])

				valid_user = {
					"userId" : uid,
					"email" : email,
					"name" : uname,
					"userType" : ut,
					"status" : 200
				}
				return jsonify(valid_user)
			else:
				login_error = {
				"Error" : 'Incorrect password',
				"status" : 202
			}
			return jsonify(login_error)

		else:
			print(list(reg_user))
			invalid_user = {
				"Error" : 'User not registered',
				"status" : 202
			}
			return jsonify(invalid_user)

	if request.method == 'GET':
		return '<h1>VMS - Signin route</h1>'

@app.route('/book_appointment',methods=['GET','POST'])
def book():
	appDB = mongo.vmsDB
	if request.method == 'POST': 
		uid = request.json['userId']
		fullname = request.json['fullname']
		email = request.json['email']
		date = request.json['date']
		slot = request.json['timeslot']
		phno = request.json['phno']
		animal = request.json['animal']
		petname = request.json['petname']
		symptoms = request.json['symptoms']
		res = appDB.daily_slots.find_one({'date':date})
		if not res:
			slots_dict = {'10:00AM':False, '11:00AM':False, '12:00PM':False, '2:00PM':False,
							'3:00PM':False, '4:00PM':False, '5:00PM':False, '6:00PM':False
						}
			res = appDB.daily_slots.insert_one({'date':date, 'slots':slots_dict})
		
		res_slots = appDB.daily_slots.find({'date':date})
		for i in res_slots:
			req_slot = i['slots']

		if req_slot[slot]:
			err = {
				"status": 202,
				"error": "Timeslot already booked"
			}
			return jsonify(err)
		else:
			data = {'userId':uid, 'date':date, 'timeslot':slot, 'symptoms':symptoms,
					'fullname':fullname, 'phno':phno, 'petname':petname, 'email':email, 
					'appointment_status':0, 'animal':animal}
			app_data = appDB.appointments.insert_one(data)
			app_id = 'app_id'
			app_id = app_data.inserted_id
			slot_str = 'slots.'+slot
			update_slot = appDB.daily_slots.update_one({'date':date},{'$set':{slot_str: str(app_id) }})
			if app_data and update_slot:
				app_user = appDB.users.find({'_id':ObjectId(uid)})
				ok = {
					"status": 200,
				}
				return jsonify(ok)
			else:
				err2 = {
					"status": 202,
					"error": "Error ocuured while making appointment."
				}
				return jsonify(err2)

	if request.method == 'GET':
		return '<h1>VMS - Book Appointment route</h1>'


@app.route('/cancel_appointment', methods=['GET','POST'])
def cancel_appointment():
	appDB = mongo.vmsDB
	if request.method == 'POST':
		appId = request.json['appId']
		appId = str(appId)
		found = appDB.appointments.find_one({"_id":ObjectId(appId)})
		print('found : ')
		print(found)
		if not found:
			err = {
				"msg" : "invalid appointment Id",
				"status" : 202
			}
			return jsonify(err)
		else:
			date = found['date']
			slot = found['timeslot']
			appDB.appointments.delete_one({"_id":ObjectId(appId)})
			query = "slots."+slot
			appDB.daily_slots.update_one({"date":date},{'$set' : {query:False}})
			ok = {
				"msg" : "Appointment cancelled",
				"status" : 200
			}
			return jsonify(ok)

	if request.method == 'GET':
		return '<h1>VMS - Cancel Appointment route</h1>'

@app.route('/available_slots',methods=['POST','GET'])
def available_slots():
	slotsDB = mongo.vmsDB
	if request.method == 'POST':
		date = request.json['date']
		res = slotsDB.daily_slots.find({'date':date})
		res2 = copy.deepcopy(res)
		if list(res2):
			for i in res:
				req_slot = i['slots']
			print(req_slot)
		else:
			req_slot = {
			        "10:00AM": False,
			        "11:00AM": False,
			        "12:00PM": False,
			        "2:00PM": False,
			        "3:00PM": False,
			        "4:00PM": False,
			        "5:00PM": False,
			        "6:00PM": False
			    }
		return jsonify({"status":200,"available":req_slot})

	if request.method == 'GET':
		return '<h1>VMS - Available slots route</h1>'

@app.route('/datewise_appointments',methods=['GET','POST'])
def datewise():
	slotsDB = mongo.vmsDB
	if request.method == 'POST':
		date = request.json['date']
		res = slotsDB.appointments.find({'date':date})
		all_appointments = {'appointments':[]}
		res2 = copy.deepcopy(res)
		if list(res2):
			for app in res:
				appId = app.pop('_id')
				app['appId'] = str(appId)
				all_appointments['appointments'].append(app)
				all_appointments["status"] = 200
		else:
			all_appointments["status"] = 202
			all_appointments["msg"] = "No appointments have been made yet"

		return jsonify(all_appointments)

	if request.method == 'GET':
		return '<h1>VMS - Datewise Appointments route</h1>'

@app.route('/user_appointments',methods=['POST','GET'])
def user_appointments():
	appDB = mongo.vmsDB
	if request.method == 'POST':
		uid = request.json['userId']
		res = appDB.appointments.find({'userId':uid})
		res2 = copy.deepcopy(res)
		all_appointments = {'appointments':[]}
		if list(res2):
			for app in res:
				appId = app.pop('_id')
				app['appId'] = str(appId)
				all_appointments['appointments'].append(app)
				all_appointments["status"] = 200
		else:
			all_appointments["status"] = 202
			all_appointments["msg"] = "No appointments have been made yet"

		return jsonify(all_appointments)

	if request.method == 'GET':
		return '<h1>VMS - User Appointments route</h1>'

@app.route('/update_app_status',methods=['POST','GET'])
def update_status():
	appDB = mongo.vmsDB
	if request.method == 'POST':
		appId = request.json['appId']
		find_res = appDB.appointments.find_one({'_id':ObjectId(appId)})
		res = appDB.appointments.update_one({'_id':ObjectId(appId)},{'$set':{'appointment_status':1}})
		if find_res:
			ok = {
				"status" : 200
			}
			return jsonify(ok)
		else:
			err = {
				"error" : "Invalid Appointment-ID",
				"status" : 202
			}
			return jsonify(err)

	if request.method == 'GET':
		return '<h1>VMS - Update Appointment Status route</h1>'


if __name__ == '__main__':
	app.run(debug=True)