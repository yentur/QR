from flask import Flask, render_template,request,redirect,url_for,send_file
import json
import os
import qrcode
import datetime
import sqlite3
import uuid
import re
import shutil
from functools import wraps
from flask import make_response, current_app

import hashlib

username="saygibakim"
password="3de21a8567767bdff63e7f42ec6bdd292b8b228456899a09971b8e97f10cec1a"

qr_url="http://saygibakim.com:8000/doc/"

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and auth.username == username:
            hashed_password = hashlib.sha256(auth.password.encode()).hexdigest()
            if hashed_password == password:
                return f(*args, **kwargs)
        return make_response("<h1>Access denied!</h1>", 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
    return decorated



app = Flask(__name__,static_folder="./static",template_folder="./templates")

UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

if not os.path.exists("./static/qr"):
    os.mkdir("./static/qr")


if not os.path.exists("./static/uploads"):
    os.mkdir("./static/uploads")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def database_olustur():
    if not "database.db" in os.listdir():
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS veri (
                        id TEXT PRIMARY KEY,
                        data TEXT,
                        datetime TEXT
                    )
                ''')
        conn.commit()
        conn.close()
    



def veri_ekle(_id, data):
    date_time=str(datetime.datetime.now().strftime("%d/%m/%Y"))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    
    existing_ids = [row[0] for row in cursor.execute("SELECT id FROM veri").fetchall()]
    while _id in existing_ids:
        _id += '_' + str(uuid.uuid4().hex)[:6]

    cursor.execute("INSERT INTO veri (id, data, datetime) VALUES (?, ?, ?)", (_id, data, date_time))
    conn.commit()
    conn.close()

    return _id

def veri_oku(_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM veri WHERE id = ?",(_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def veri_guncelle(_id, data):
    date_time=str(datetime.datetime.now().strftime("%d/%m/%Y"))
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE veri SET data = ?, datetime = ?  WHERE id = ?", (data,date_time,_id))
    conn.commit()
    conn.close()

def colum_listele(name="id"):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT {name} FROM veri")
    id_listesi = [row for row in cursor.fetchall()]

    conn.close()
    return id_listesi


def veri_sil(_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM veri WHERE id = ?", (_id,))
    conn.commit()
    conn.close()


def qr_code_olustur(veri):

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url+veri)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img.save("./static/qr/"+veri+ ".png")



@app.route('/')
@app.route('/main')
@auth_required
def index():
    return render_template('mainpage.html')


@app.route('/belge')
@auth_required
def belge():
    return render_template('doc.html')



@app.route('/list')
@auth_required
def doc_list():
    q=colum_listele("id,datetime")
    q.reverse()
    data=[]
    for (_id,date_time) in q:
        data.append({"name":_id,"tarih":date_time})
    return render_template('list.html', data=data)



@app.route('/doc/<file_name>',methods=['GET','POST'])
def doc(file_name):
    data=veri_oku(file_name)[0]
    tarih=data[2]
    json_data=json.loads(str(data[1]).replace("\'","\""))
    return render_template('belge.html',data=json_data,doc_name=file_name,doc_tarih=tarih)



@app.route('/data',methods=['GET','POST'])
@auth_required
def data():
    request_data=request.form
    print("--------------"*10,request_data)
    tersane=request_data.get("tersane")
    motor=request_data.get("motor_name")
    gemi=request_data.get("gemi")
    is_no=request_data.get("is_no")
    if is_no==None:
        is_no=""
    file_name=f"{tersane}_{gemi}_{motor}_{is_no}"
    file_name=uygun_url(file_name)
    _id=veri_ekle(_id=file_name,data=str(dict(request_data)))
    qr_code_olustur(_id)
    return redirect(url_for(f"doc_upload",file_name=file_name))



@app.route('/qr', methods=['GET', 'POST'])
def qr_print():
    data=veri_oku(request.form.get('qr_code'))[0][1]
    data=json.loads(str(data).replace("\'","\""))
    return render_template('qr.html',qr_path="qr/"+request.form.get('qr_code')+".png",data=data)


def uygun_url(string):
    temizlenmis_string = re.sub(r'[^a-zA-Z0-9-_\.]', '', string)
    return temizlenmis_string


@app.route('/upload', methods=['POST'])
@auth_required
def upload():
    _id=request.form.get("_id")
    path_name=f"static/uploads/{_id}"
    print(os.listdir("static/uploads"))
    if not _id in os.listdir("static/uploads") :
        os.mkdir(path_name)
    if 'file' not in request.files:
        return 'No file part'
    
    file = request.files['file']

    if file.filename == '':
        return 'No selected file'

    file.save(path_name + "/" +uygun_url(file.filename))
    return 'File uploaded successfully'



@app.route('/doc_upload/<file_name>',methods=['GET','POST'])
def doc_upload(file_name):
    return render_template('doc_upload.html',_id=file_name)



@app.route('/doc_show/<file_name>',methods=['GET','POST'])
def doc_show(file_name):
    path_id=f"static/uploads/{file_name}"
    if not os.path.exists(path_id):
         return render_template('doc_show.html', doc_list=[],_id=file_name)
    doc_lists=[]
    for i in os.listdir(path_id):
        path_file=f"uploads/{file_name}"+"/"+i
        doc_lists.append(path_file)
    return render_template('doc_show.html', doc_list=doc_lists,_id=file_name)



@app.route('/download',methods=['GET','POST'])
def download():
    file_name=list(request.form)[0]
    _id=file_name.split("/")[-2]
    _file=file_name.split("/")[-1]
    file_path=f"static\\uploads\\{_id}\\{_file}"
    return send_file(file_path, as_attachment=True)




@app.route('/delete/<file_name>',methods=['GET','POST'])
@auth_required
def delete(file_name):
    path_id=f"static/uploads/{file_name}"
    try:
        veri_sil(file_name)
        try:
            if os.path.exists(path_id):
                shutil.rmtree(path=path_id)
            
        except:
            pass
        try: 
            os.remove(f"static/qr/{file_name}.png")
            
        except:
            pass
    except Exception as e:
        print(e)
        return "HATA OLUŞTU"
    return redirect(url_for("doc_list"))


@app.route('/edit/<file_name>',methods=['GET','POST'])
@auth_required
def edit(file_name):
    data=veri_oku(file_name)[0]
    json_data=json.loads(str(data[1]).replace("\'","\""))
    print(json_data)
    return render_template('doc_edit.html',data=json_data,doc_name=file_name)


@app.route('/editdoc/<file_name>',methods=['GET','POST'])
@auth_required
def editdoc(file_name):
    if request.method=="POST":
        request_data=request.form
        print("*******"*10,request_data)
        try:
            veri_sil(file_name)
            os.remove(f"static/qr/{file_name}.png")
            tersane=request_data.get("tersane")
            motor=request_data.get("motor_name")
            gemi=request_data.get("gemi")
            is_no=request_data.get("is_no")
            if is_no==None:
                is_no=""
            file_name=f"{tersane}_{gemi}_{motor}_{is_no}"
            file_name=uygun_url(file_name)
            _id=veri_ekle(_id=file_name,data=str(dict(request_data)))
            qr_code_olustur(_id)
        except Exception as e:
            print(e)
            return "Düzenleme sırasında hata oluştu"

    path_id=f"static/uploads/{file_name}"
    if not os.path.exists(path_id):
         return render_template('doc_show_edit.html', doc_list=[],_id=file_name)
    doc_lists=[]
    for i in os.listdir(path_id):
        path_file=f"uploads/{file_name}"+"/"+i
        doc_lists.append(path_file)
    return render_template('doc_show_edit.html', doc_list=doc_lists,_id=file_name)


@app.route('/deletefile',methods=['GET','POST'])
@auth_required
def deletefile():
    try:
        file_path= request.form.get("path")
        if file_path:
            os.remove(file_path[1:])
        
    except Exception as e:
        print(e)
        return "Dosya Silinemedi"
    file_name=request.form.get("file_name")
    return redirect(url_for("editdoc",file_name=file_name))

if __name__=="__main__":
    database_olustur()
    app.run(debug=True,host="0.0.0.0",port=8000)


