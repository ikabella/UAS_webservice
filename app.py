import numpy as np
import keras
import datetime 
from datetime import date
from keras.models import Sequential
from keras.layers import Dense,Conv2D,MaxPool2D,Dropout,BatchNormalization,Flatten,Activation
from keras.preprocessing import image 
from keras.preprocessing.image import ImageDataGenerator
# import matplotlib.pyplot as plt
from keras.utils.vis_utils import plot_model
import pickle
from flask import Flask, jsonify,request,flash,redirect,render_template, session,url_for
#from flask_session import Session
from itsdangerous import json
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS
from flask_restful import Resource, Api
import pymongo
import re
from PIL import Image
import datetime
import random
import string

app = Flask(__name__)
#sess = Session()
UPLOAD_FOLDER = 'fotohewan'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = "bp"
#SECRET_KEY = 'xxxxxxxxx'
#app.config['SESSION_TYPE'] = 'filesystem'
MONGO_ADDR = 'mongodb://localhost:27017'
MONGO_DB = "animals"

conn = pymongo.MongoClient(MONGO_ADDR)
db = conn[MONGO_DB]

api = Api(app)
CORS(app)

from tensorflow.keras.models import load_model
MODEL_PATH = 'model.h5'
model = load_model(MODEL_PATH,compile=False)

pickle_inn = open('num_class_hewan.pkl','rb')
num_classes_hewan = pickle.load(pickle_inn)

def allowed_file(filename):     
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class index(Resource):
  def post(self):

    if 'image' not in request.files:
      flash('No file part')
      return jsonify({
            "pesan":"tidak ada form image"
          })
    file = request.files['image']
    if file.filename == '':
      return jsonify({
            "pesan":"tidak ada file image yang dipilih"
          })
    if file and allowed_file(file.filename):
      path_del = r"fotohewan\\"
      for file_name in os.listdir(path_del):
        # construct full file path
        file_del = path_del + file_name
        if os.path.isfile(file_del):
            print('Deleting file:', file_del)
            os.remove(file_del)
            print("file "+file_del+" telah terhapus")
      filename = secure_filename(file.filename)
      file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      path=("fotohewan/"+filename)

      today = date.today()
      db.riwayat.insert_one({'nama_file': filename, 'path': path, 'prediksi':'No predict', 'akurasi':0, 'tanggal':today.strftime("%d/%m/%Y")})

      #def predict(dir):
      img=keras.utils.load_img(path,target_size=(224,224))
      img1=keras.utils.img_to_array(img)
      img1=img1/255
      img1=np.expand_dims(img1,[0])
      # plt.imshow(img)
      predict=model.predict(img1)
      classes=np.argmax(predict,axis=1)
      for key,values in num_classes_hewan.items():
          if classes==values:
            accuracy = float(round(np.max(model.predict(img1))*100,2))
            info = db['DeskripsiHewan'].find_one({'nama': str(key)})
            db.riwayat.update_one({'nama_file': filename}, 
              {"$set": {
                'prediksi': str(key), 
                'akurasi':accuracy
              }
              })
            if accuracy >35:
              print("The predicted image of the animals is: "+str(key)+" with a probability of "+str(accuracy)+"%")
        
              return jsonify({
                "nama":str(key),
                "Accuracy":str(accuracy)+"%",
                "namalain": info['namalain'],
                "deskripsi" : info['deskripsi']
              })
            else :
              print("The predicted image of the flower is: "+str(key)+" with a probability of "+str(accuracy)+"%")
              return jsonify({
                "Message":str("Jenis Hewan belum tersedia "),
                "Accuracy":str(accuracy)+"%"               
                
              })
      
    else:
      return jsonify({
        "Message":"bukan file image"
      })

@app.route('/admin')
def admin():
    return render_template("login.html")
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'] # .encode('utf-8')
        user = db['Admin'].find_one({'username': str(username)})
        print(user)

        if user is not None and len(user) > 0:
            if password == user['password']:
                
                session['username'] = user['username']
                return redirect(url_for('dataHewan'))
            else:
                return redirect(url_for('login'))
        else:
            return redirect(url_for('login'))
    else:
        return render_template('login.html')
    
    return render_template('dashboard.html')
#menampilkan  daftar tamu
@app.route('/dataHewan')
def dataHewan():
    data = db['DeskripsiHewan'].find({})
    print(data)
    return render_template('dataHewan.html',dataHewan  = data)

@app.route('/tambahData')
def tambahData():

    return render_template('tambahData.html')

#roses memasukan data Hewan ke database
@app.route('/daftarHewan', methods=["POST"])
def daftarHewan():
    if request.method == "POST":
        nama = request.form['nama']
        namalain = request.form['namalain']
        deskripsi = request.form['deskripsi']
       
        if not re.match(r'[A-Za-z]+', nama):
            flash("Nama harus pakai huruf Dong!")
        
        else:
            db.DeskripsiHewan.insert_one({'nama': nama, 'namalain': namalain, 'deskripsi':deskripsi})
            flash('Data Hewan berhasil ditambah')
            return redirect(url_for('dataHewan'))

    return render_template("tambahData.html")

@app.route('/editHewan/<nama>', methods = ['POST', 'GET'])
def editHewan(nama):
  
    data = db['DeskripsiHewan'].find_one({'nama': nama})
    print(data)
    return render_template('editHewan.html', editHewan = data)

#melakukan roses edit data
@app.route('/updateHewan/<nama>', methods=['POST'])
def updatHewan(nama):
    if request.method == 'POST':
        nama = request.form['nama']
        namalain = request.form['namalain']
        deskripsi = request.form['deskripsi']
        if not re.match(r'[A-Za-z]+', nama):
            flash("Nama harus pakai huruf Dong!")
        else:
          db.flowers.update_one({'nama': nama}, 
          {"$set": {
            'nama': nama, 
            'namalain': namalain, 
            'deskripsi':deskripsi
            }
            })

          flash('Data Hewan berhasil diupdate')
          return render_template("popUpEdit.html")

    return render_template("dataHewan.html")

#menghaus daftar Hewan
@app.route('/hapusHewan/<nama>', methods = ['POST','GET'])
def hapusHewan(nama):
  
    db.flowers.delete_one({'nama': nama})
    flash('Hewan Berhasil Dihapus!')
    return redirect(url_for('dataHewan'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/riwayat')
def riwayat():
    dataRiwayat = db['riwayat'].find({})
    print(dataRiwayat)
    return render_template('riwayat.html',riwayat  = dataRiwayat)


api.add_resource(index, "/api/image", methods=["POST"])

if __name__ == '__main__':
  

  app.run(debug = True, port=5000, host='0.0.0.0')

