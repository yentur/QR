from flask import Flask, render_template,request,redirect,url_for
import json
import os
import json
import openpyxl
import hashlib
import random
import string
import qrcode
import datetime

qr_url=" https://qr-deneme.onrender.com/doc/"


app = Flask(__name__,static_folder="./static",template_folder="./templates")


UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


with open("./static/.excel/ref.json","r") as file:
    ref_json=json.load(file)


def karsilastir_ve_olustur(dict1, dict2):
    yeni_dict = {}
    
    for anahtar in dict1:
        if anahtar in dict2:
            yeni_dict[dict1[anahtar]] = dict2[anahtar]
    
    return yeni_dict


def random_unique_filename(length=100):
    
    characters = string.ascii_letters + string.digits

    random_string = ''.join(random.choice(characters) for _ in range(length))

    sha1 = hashlib.sha1()
    sha1.update(random_string.encode('utf-8'))
    hash_value = sha1.hexdigest()

    filename = hash_value 

    return filename


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
    qr_img.save("./qr/"+veri+ ".png")
    qr_img.save("./static/qr/"+veri+ ".png")
    


def read_excell(file_name):
    workbook = openpyxl.load_workbook(f'excel/{file_name}.xlsx')
    sheet = workbook.active
    cell=list(ref_json.values())
    values={}
    for i in range(len(cell)):
        deger=sheet[cell[i]].value
        if deger==None:
            values[list(ref_json.keys())[i]]=""
        else:
            values[list(ref_json.keys())[i]]=deger
    return values







kaynak_excel = "./static/.excel/ref.xlsx"




if not os.path.exists("./excel"):
    os.mkdir("./excel")
if not os.path.exists("./qr"):
    os.mkdir("./qr")



if not os.path.exists("./static/qr"):
    os.mkdir("./static/qr")



@app.route('/')
@app.route('/main')
def index():
    return render_template('mainpage.html')



@app.route('/belge')
def belge():
    return render_template('doc.html')




@app.route('/list')
def doc_list():
    data=[]
    for i in os.listdir("./excel/"):
        data.append({"name":i.split(".")[0],"tarih":datetime.datetime.fromtimestamp(os.path.getctime("./excel/"+i)).strftime("%d/%m/%Y")})
    return render_template('list.html', data=data)




@app.route('/doc/<file_name>',methods=['GET','POST'])
def doc(file_name):
    tarih=datetime.datetime.fromtimestamp(os.path.getctime("./excel/"+file_name+".xlsx")).strftime("%d/%m/%Y")
    return render_template('belge.html',data=read_excell(file_name),doc_name=file_name,doc_tarih=tarih)




@app.route('/data',methods=['GET','POST'])
def data():

    request_data=request.form
    if list(dict(request_data).values()).count('')<113:
        kaynak_wb = openpyxl.load_workbook(kaynak_excel)
        kaynak_ws = kaynak_wb.active
        excel_data=karsilastir_ve_olustur(ref_json,request_data)
        for i in excel_data:
            kaynak_ws[i]=excel_data[i]

        file_name=random_unique_filename()
        file_names=os.listdir("./excel")
        while (file_name in file_names):
            file_name=random_unique_filename()

        kaynak_wb.save("./excel/"+file_name+ ".xlsx")
        kaynak_wb.close()
        qr_code_olustur(file_name)
        return redirect(url_for("doc",file_name=file_name))
    else:
        return render_template('doc.html',data=None,doc_name=None,doc_tarih=None)
    


# @app.route('/upload', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         print(request.files)
#         if 'file' not in request.files:
#             return "No file part"
#         file = request.files['file']
#         if file.filename == '':
#             return "No selected file"
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             print(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             image =cv2.cvtColor(cv2.imread(os.path.join(app.config['UPLOAD_FOLDER'], filename)),cv2.COLOR_BGR2RGB)
#             # decoded_text = qreader.detect_and_decode(image=image)
#             return redirect(url_for("doc",file_name="decoded_text[0]"))



@app.route('/qr', methods=['GET', 'POST'])
def qr_print():
    return render_template('qr.html',qr_path="qr/"+request.form.get('qr_code')+".png")







