from flask import Flask,render_template,request,redirect,session,jsonify
from pymongo import MongoClient
import smtplib
import boto3
import random

s3 = boto3.client('s3')

reko = boto3.client('rekognition')

server = smtplib.SMTP("smtp.gmail.com",587)
cluster  = MongoClient('mongodb://127.0.0.1:27017/')

db = cluster['emotion']
users = db['users']

app = Flask(__name__)
app.secret_key="7890kfnkln"

@app.route('/',methods=['get'])
def home():
    return render_template('index.html')

@app.route('/signup',methods=['get'])
def loadsign():
    return render_template('signup.html')

@app.route('/forget',methods=['get'])
def forg():
    return render_template('Forgot.html')

@app.route('/webcam',methods=['get'])
def web():
    return render_template('webcam.html',higest={"Type":None,"Confidence":None})

@app.route('/forget',methods=['post'])
def sendpass():
    email = request.form['email']
    user = users.find_one({"email":email})
    if not user:
        return render_template('Forgot.html',status='User not found with this email id')
    user = dict(user)
    password = user['password']
    server.starttls()
    server.login('damarlanandini@gmail.com','kaeepcicagdvylyo')
    server.sendmail('damarlanandini@gmail.com',email,"please click on the follo link change you password \n http://127.0.0.1:3000/change/"+email)
    return render_template('Forgot.html',status="Mail sent")

@app.route('/login',methods=['get'])
def loadlog():
    return render_template('login.html')
@app.route('/dashboard',methods=['get'])
def dash():
    return render_template('Main.html')

@app.route('/signup',methods=['post'])
def reg():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    user = users.find_one({"email":email})
    if user:
        return render_template('signup.html',status="User already exist with this email id ")
    users.insert_one({"name":name,"email":email,"password":password,"imguri":"avatar1.png"})
    return redirect('/login')

@app.route('/login',methods=['post'])
def log():
    email = request.form['email']
    password = request.form['password']
    user = users.find_one({"email":email,"password":password})
    if user:
        session['email'] = email
        return redirect('/dashboard')
    return render_template('login.html',status="User fetails incorrect")

@app.route('/profile',methods=['get'])
def pro():
    email = session['email']
    user = users.find_one({'email':email})
    user = dict(user)
    return render_template('profile.html',data=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/change',methods=['get'])
def change():
    return render_template('change.html')

@app.route('/change/<email>',methods=['post'])
def ch(email):
    npass = request.form['npass']
    cpass = request.form['cpass']
    if npass != cpass:
        return render_template('change.html',ack="Password miss match")
    users.update_one({'email':email},{'$set':{"password":npass}})
    return redirect('/login')


@app.route('/changepass',methods=['post'])
def chang():
    email = session.get('email')
    password = request.form['password']
    npass = request.form['npass']
    cpass = request.form['cpass']
    user = users.find_one({'email':email,'password':password})
    if not user:
        return render_template('profile.html',data=user,ack="Incorrect password...")
    if npass !=cpass:
        return render_template('profile.html',data=user,ack="poassword missmatch...")
    users.update_one({"email":email},{'$set':{"password":npass}})
    return render_template('profile.html',data=user,ack="Your password is updated...")

@app.route('/imageanalysis',methods=['post'])
def detect():
    face = request.files['face']
    if not face :
        return render_template('webcame.html',vack="Please upload file")
    res = reko.detect_faces(Image={'Bytes':face.read()},Attributes=['ALL'])
    emotions = res['FaceDetails'][0]['Emotions']
    max = 0.0
    t = None
    for i in emotions:
        if i['Confidence'] > max:
            max= i['Confidence']
            t = i['Type']
    return render_template('webcam.html',data= emotions,higest={'Type':t,"Confidence":max})

@app.route('/videoanalysis',methods=['post'])
def ana():
    video = request.files['video']
    if not video:
        return render_template('webcame.html',ack="Please upload file")
    e = str(random.randint(1000,100000))
    s3.upload_fileobj(video,'emotion.cdn.app','videos/'+e+video.filename)
    res = reko.start_face_detection(Video={'S3Object':{'Bucket':"emotion.cdn.app","Name":'videos/'+e+video.filename}},FaceAttributes='ALL')
    response = reko.get_face_detection(JobId=res['JobId'])
    while response['JobStatus']=='IN_PROGRESS':
        response = reko.get_face_detection(JobId=res['JobId'])
    
    max = 0.0
    t = None
    ts = None
    data  = []
    for i in response['Faces']:
        ts = i['Timestamp']
        for j in i['Face']['Emotions']:
            if j['Confidence'] > max:
                max= j['Confidence']
                t = j['Type']
        data.append({'Timestamp':ts,"Type":t,"Confidence":max})
        t=None
        max=0.0
    
    return render_template('webcam.html',vdata=response['Faces'],higest = {"Type":None,"Confidence":None},mdata=data)

@app.route('/d',methods=['get'])
def detctee():
    return render_template('face.html')


@app.route('/uploaddp',methods=['post'])
def dp():
    email = session.get('email')
    dp = request.files['dp']
    s3.upload_fileobj(dp,'emotion.cdn.app',email+dp.filename )
    users.update_one({'email':email},{'$set':{"imguri":email+dp.filename}})
    user = users.find_one({'email':email})
    return render_template('profile.html',ack="Dp uploaded...",data=user)

if __name__=="__main__":
    app.run(port=3000,host='0.0.0.0')