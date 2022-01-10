from flask import Flask, render_template, url_for, request, redirect, session, flash, make_response
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase
from templates import render_template_string
from application import app
import re
import csv
from io import StringIO
import pyexcel as pe





cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)

db = firestore.client()


firebaseConfig = {
    'apiKey': "AIzaSyC2XljF65Ac6ybNhoQAmdwD1E_o11xItGw",
    'authDomain': "attendance-management-2296e.firebaseapp.com",
    'projectId': "attendance-management-2296e",
    'storageBucket': "attendance-management-2296e.appspot.com",
    'messagingSenderId': "621691891391",
    'appId': "1:621691891391:web:50107625d23f2b6a94a00a",
    'databaseURL':"https://attendance-management-2296e-default-rtdb.europe-west1.firebasedatabase.app/"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()


@app.route('/')
def index():
    resp = make_response(render_template("home_page.html"))
    return resp





@app.route('/teacher_login',methods = ['GET', 'POST'])
def teacher_login():
    if request.method == 'GET':
        if 'user' not in session:
            return render_template('teacher_login_page.html')
        else:
            return redirect('/logout')

    elif request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        flag_1 = flag_2 = False
        ref = db.collection('teachers')
        refs = ref.stream()
        for teacher in refs:
            
            if teacher.id == email:
                flag_1 = True
                       
                try:
                    st_user = auth.sign_in_with_email_and_password(email, password)
                    flag_2 = True
                    acc_info = auth.get_account_info(st_user['idToken'])

                except:
                    break
                break

        if flag_1 == False or flag_2 == False:
        	flash('Invalid account', 'error')
        	return redirect('/teacher_login')

        session['user'] = email
        session['person_type'] = 'teacher'
        return redirect('/teacher_dashboard')

@app.route('/forgot_password',methods=["GET","POST"])
def forgot_password():
    if request.method == 'GET':
        if 'user' not in session:
            return render_template('forgot_password_page.html')
        else:
            return redirect('/logout')
    elif request.method == 'POST':
        email = request.form['email']
        try:
            auth.send_password_reset_email(email)
        except:
            flash('The email does not exist.', 'error')
            return redirect('/')
        flash('Check your email address.', 'info')
        return redirect('/')

@app.route('/student_dashboard')
def student_dashboard():
    if 'user' in session and session['person_type'] == 'student':
        user_data=db.collection("students").document(session['user']).get()
        name_dict=user_data.to_dict()
        name=name_dict.get("name")
        indexes = []
        attendances_dict = {}
        i = 0
        teachers = db.collection('students').document(session['user']).collections()
        for teacher in teachers:
           for doc in teacher.stream():
              subjectname=doc.id
              teacheremail=teacher.id
              teacher_data=db.collection("teachers").document(teacheremail).get()
              teacher_dict=teacher_data.to_dict()
              teachername=teacher_dict.get("name")
              count=0
              attendances = db.collection('subjects').document(teacheremail).collection(subjectname).document(session['user']).collection('attended').stream()
              for attendance in attendances:
                 count=count+1
              lecture_data=db.collection('subjects').document(teacheremail).collection(subjectname).document('lectures').get()
              lecture_dict=lecture_data.to_dict()
              conducted=lecture_dict.get("conducted")
              count_str=str(count)
              conducted_int=int(conducted)
              if conducted_int != 0:
                 percentage=(count/conducted_int)*100
              else:
                 percentage=100
              percentage_str="{:.2f}".format(percentage)+"%"
              gradeslist=[]
              grades = db.collection('subjects').document(teacheremail).collection(subjectname).document(session['user']).collection('grades').stream()
              for grade in grades:
                 name_dict=grade.to_dict()
                 new_grade=name_dict.get("grade")
                 gradeslist.append(new_grade)
              score=0
              score_str=""
              grades_str=""
              if len(gradeslist)>0:
                 for value in gradeslist:
                    score=score+int(value)
                    grades_str=grades_str+value+" "
                 score_str="{:.2f}".format(score/len(gradeslist))
              else:
                 score_str="0"
              attendances_dict[i]=[subjectname,teachername,count_str,conducted,percentage_str,grades_str,score_str]
              indexes.append(i)
              i=i+1
        return render_template('student_dashboard_page.html', name=name, attendances=attendances_dict,indexes=indexes)
    else:
        return redirect('/logout')


@app.route('/teacher_dashboard',methods = ['GET'])
def teacher_dashboard():
    if 'user' in session and session['person_type'] == 'teacher':
        user_data=db.collection("teachers").document(session['user']).get()
        name_dict=user_data.to_dict()
        name=name_dict.get("name")
        subjects = db.collection('subjects').document(session['user']).collections()
        attendance = {}
        indexes=[]
        i=0
        for subject in subjects:
            subject_name=subject.id
            lecture_data=db.collection('subjects').document(session['user']).collection(subject.id).document('lectures').get()
            lecture_dict=lecture_data.to_dict()
            conducted=lecture_dict.get("conducted")
            attendance[i] = [subject_name,conducted]
            indexes.append(i)
            i=i+1
        return render_template('teacher_dashboard_page.html', attendance=attendance,subject=indexes,username=name)
    else:
        return redirect('/logout')

@app.route('/student_login', methods = ['GET', 'POST'])
def student_login():
    if request.method == 'GET':
        if 'user' not in session:
            return render_template('student_login_page.html')
        else:
            return redirect('/logout')

    elif request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        flag_1 = flag_2 = flag_3 = False
        ref = db.collection('students')
        refs = ref.stream()
        for student in refs:
            
            if student.id == email:
                flag_1 = True
                       
                try:
                    st_user = auth.sign_in_with_email_and_password(email, password)
                    flag_2 = True
                    acc_info = auth.get_account_info(st_user['idToken'])
                    if acc_info['users'][0]['emailVerified'] == True:
                        flag_3 = True
                except:
                    flag_3 = False
                    break
                break

        if flag_1 == False or flag_2 == False or flag_3 == False:
        	flash('Invalid or unverified account', 'error')
        	return redirect('/student_login')

        session['user'] = email
        session['person_type'] = 'student'
        return redirect('/student_dashboard')

    

@app.route('/teacher_manage_attendance',methods = ['GET','POST'])
def teacher_manage_attendance():
    if request.method == 'GET':
        if 'user' in session and session['person_type'] == 'teacher':
            teacher_details = db.collection('teachers').document(session['user']).get()
            students = db.collection('subjects').document(session['user']).collection(session['subject']).stream()
            count = 0
            for student in students:
                count += 1
            if count - 1 == 0:
                flash('No students taking the class', 'info')
                return redirect('/teacher_dashboard')
            names=[]
            emails=[]
            students = db.collection('subjects').document(session['user']).collection(session['subject']).stream()
            for student in students:
                if(student.id!="lectures"):
                   user_data=db.collection("students").document(student.id).get()
                   name_dict=user_data.to_dict()
                   name=name_dict.get("name")
                   names.append(name)
                   emails.append(student.id)
            return render_template('teacher_manage_attendance_page.html',names=names, students = emails, teacher_details = teacher_details.to_dict())
        else:
            return redirect('/logout')

    elif request.method == 'POST':
        date = request.form['date']
        title = request.form['title']
        student_emails = request.form.getlist('check-box')        
        for student_email in student_emails:
           db.collection('subjects').document(session['user']).collection(session['subject']).document(student_email).collection("attended").document(date).set({
              'attended': "1"
           })
        lecture_data=db.collection('subjects').document(session['user']).collection(session['subject']).document('lectures').get()
        lecture_dict=lecture_data.to_dict()
        conducted=int (lecture_dict.get("conducted"))
        conducted=conducted+1
        conducted_str=str(conducted)
        db.collection('subjects').document(session['user']).collection(session['subject']).document('lectures').set({
           'conducted': conducted_str
           })
        db.collection('subjects').document(session['user']).collection(session['subject']).document('lectures').collection(date).document(title).set({
           'conducted': '1'
           })
        return redirect('/teacher_dashboard')


@app.route('/teacher_subject',methods = ['GET'])
def teacher_subject():
    if 'user' in session and session['person_type'] == 'teacher':
        session['studentemail']=None
        subjectname=request.args.get('type')
        session['subject']=subjectname
        attendances_dict = {}
        indexes=[]
        i=0
        students = db.collection('subjects').document(session['user']).collection(session['subject']).stream()

        for student in students:
           if(student.id!="lectures"):
              user_data=db.collection("students").document(student.id).get()
              name_dict=user_data.to_dict()
              name=name_dict.get("name")
              count=0
              attendances = db.collection('subjects').document(session['user']).collection(session['subject']).document(student.id).collection('attended').stream()
              for attendance in attendances:
                 count=count+1
              lecture_data=db.collection('subjects').document(session['user']).collection(session['subject']).document('lectures').get()
              lecture_dict=lecture_data.to_dict()
              conducted=lecture_dict.get("conducted")
              count_str=str(count)
              conducted_int=int(conducted)
              if conducted_int != 0:
                 percentage=(count/conducted_int)*100
              else:
                 percentage=100
              percentage_str="{:.2f}".format(percentage)+"%"
              gradeslist=[]
              grades = db.collection('subjects').document(session['user']).collection(session['subject']).document(student.id).collection('grades').stream()
              for grade in grades:
                 name_dict=grade.to_dict()
                 new_grade=name_dict.get("grade")
                 gradeslist.append(new_grade)
              score=0
              score_str=""
              if len(gradeslist)>0:
                 for value in gradeslist:
                    score=score+int(value)
                 score_str="{:.2f}".format(score/len(gradeslist))
              else:
                 score_str="0"
              
              
              attendances_dict[i]=[name,count_str,percentage_str,student.id,score_str]
              indexes.append(i)
              i=i+1
           
        return render_template('teacher_subject_page.html', subject=subjectname,attendances=attendances_dict,indexes=indexes)
    else:
        return redirect('/logout')

@app.route('/teacher_edit_subject',methods=['GET','POST'])
def teacher_edit_subject():
    if request.method == 'GET':
        if 'user' not in session:
            return redirect('/logout')
        else:
            subjectname=session['subject']
            names=[]
            students = db.collection('subjects').document(session['user']).collection(session['subject']).stream()
            for student in students:
                if(student.id!="lectures"):
                   user_data=db.collection("students").document(student.id).get()
                   name_dict=user_data.to_dict()
                   name=name_dict.get("name")
                   names.append(name)
            return render_template('teacher_edit_subject_page.html',subjectname=subjectname,names=names)
    elif request.method == 'POST':
        email = request.form['email']
        flag_1 = True
        flag_2  = False
        ref = db.collection('students')
        refs = ref.stream()
        for student in refs:
            
            if student.id == email:
                flag_2 = True
                    
        students=db.collection("subjects").document(session['user']).collection(session['subject']).stream()
        for ref in students:
           if ref.id == email:
                flag_1 = False
        if flag_2==True and flag_1==True:
            db.collection("subjects").document(session['user']).collection(session['subject']).document(email).set({
            'attendances' : '0'
            })
            db.collection("students").document(email).collection(session['user']).document(session['subject']).set({
            'attendances' : '0'
            })
        
        return redirect('/teacher_edit_subject')


@app.route('/teacher_create_subject',methods=['GET','POST'])
def teacher_create_subject():
    if request.method == 'GET':
        if 'user' not in session:
            return redirect('/logout')
        else:
            return render_template('teacher_create_subject_page.html')
    elif request.method == 'POST':
        subjectname = request.form['subjectname']
        db.collection('subjects').document(session['user']).collection(subjectname).document('lectures').set({
            'conducted' : '0'
        })


     
        return redirect('/teacher_dashboard')

      
@app.route('/render/', methods=['POST'])
def render():
    data = request.get_json()

    template = data.get("template", "")
    context = data.get("context", {})

    resp = make_response(render_template_string(template, context))
    return resp

@app.route('/student_signup',methods = ['GET', 'POST'])
def student_register():
    if request.method == 'GET':
        if 'user' not in session:
            return render_template('student_signup_page.html')
        else:
            return redirect('/logout')

    elif request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        birthday = request.form['birthday']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['cpassword']
        pattern = re.compile( "^(0[1-9]|1[012])[-/.](0[1-9]|[12][0-9]|3[01])[-/.](19|20)\\d\\d$")

        if (not pattern.match(birthday)):
            flash("Invalid birthday format")
            return redirect('/student_signup')

        if len(firstname) < 1:
            flash('First name required', 'error')
            return redirect('/student_signup')

        if len(lastname) < 1:
            flash('Last name required', 'error')
            return redirect('/student_signup')

        if password != password2:
            flash('Passwords do not match', 'error')
            return redirect('/student_signup')

        if len(password) < 6:
            flash('Password is too short', 'error')
            return redirect('/student_signup')

        try:
            st_user = auth.create_user_with_email_and_password(email, password)
        except:
            flash('Email already used', 'error')
            return redirect('/teacher_signup')
        auth.send_email_verification(st_user['idToken'])
        name=firstname+" "+lastname

        
        db.collection('students').document(email).set({
            'name': name,
	    'birthday' : birthday
        })
        
        flash('Account succesfully created! Please confirm your email address.', 'info')
        return redirect('/student_login')





@app.route('/logout', methods = ['GET'])
def logout():
    if 'user' in session:
        session.pop('user', None)
        session.pop('person_type', None)

        flash('You have been logged out.', 'warning')
        return redirect('/')
    else:
        return redirect('/')



@app.route('/download_report')
def download_report():
    if 'user' in session and session['person_type'] == 'teacher':
       data = []
       headers=[]
       headers.append("Student")
       headers.append("Lectures Attended")
       headers.append("Percentage")
       headers.append("Grades")
       headers.append("Average Score")
       data.append(headers)
       students = db.collection('subjects').document(session['user']).collection(session['subject']).stream()
       for student in students:
          if student.id!="lectures":
             user_data=db.collection("students").document(student.id).get()
             name_dict=user_data.to_dict()
             name=name_dict.get("name")
             count=0
             date_str=""
             attendances = db.collection('subjects').document(session['user']).collection(session['subject']).document(student.id).collection('attended').stream()
             for attendance in attendances:
                count=count+1
                date_str=date_str+attendance.id+" "
             lecture_data=db.collection('subjects').document(session['user']).collection(session['subject']).document('lectures').get()
             lecture_dict=lecture_data.to_dict()
             conducted=lecture_dict.get("conducted")
             count_str=str(count)
             conducted_int=int(conducted)
             if conducted_int != 0:
                percentage=(count/conducted_int)*100
             else:
                percentage=100
             percentage_str="{:.2f}".format(percentage)+"%"
             gradeslist=[]
             grades = db.collection('subjects').document(session['user']).collection(session['subject']).document(student.id).collection('grades').stream()
             for grade in grades:
                name_dict=grade.to_dict()
                new_grade=name_dict.get("grade")
                gradeslist.append(new_grade)
             score=0
             score_str=""
             grades_str=""
             if len(gradeslist)>0:
                for value in gradeslist:
                   score=score+int(value)
                   grades_str=grades_str+value+" "
                score_str="{:.2f}".format(score/len(gradeslist))
             else:
                score_str="0"
             sublist=[]
             sublist.append(name)
             sublist.append(count_str)
             sublist.append(percentage_str)
             sublist.append(grades_str)
             sublist.append(score_str)
             data.append(sublist)
       name_of_file=session['subject']+".csv"
       sheet = pe.Sheet(data)
       io = StringIO()
       sheet.save_to_memory("csv", io)
       output = make_response(io.getvalue())
       output.headers["Content-Disposition"] = "attachment; filename={}".format(name_of_file)
       output.headers["Content-type"] = "text/csv"
       return output
    else:
        return redirect('/')



@app.route('/teacher_manage_grades',methods=['GET','POST'])
def teacher_manage_grades():
    if request.method == 'GET':
        if 'user' not in session:
            return redirect('/logout')
        else:
            studentemail=request.args.get('type')
            if studentemail!=None:    
               session['studentemail']=studentemail
            gradeslist=[]
            dateslist=[]
            grades = db.collection('subjects').document(session['user']).collection(session['subject']).document(session['studentemail']).collection('grades').stream()
            for grade in grades:
                name_dict=grade.to_dict()
                name=name_dict.get("grade")
                gradeslist.append(name)
                dateslist.append(grade.id)
            user_data=db.collection("students").document(session['studentemail']).get()
            user_dict=user_data.to_dict()
            user=user_dict.get("name")
            return render_template('teacher_manage_grades_page.html',username=user,grades=gradeslist,dates=dateslist)
    elif request.method == 'POST':
        grade = request.form['grade']
        date = request.form['date']
        grade_str=str(grade)
        db.collection("subjects").document(session['user']).collection(session['subject']).document(session['studentemail']).collection("grades").document(date).set({
           'grade' : grade_str	
        })
        
        return redirect('/teacher_manage_grades')




@app.route('/download_generated_report')
def download_generated_report():
    if 'user' in session and session['person_type'] == 'teacher':
       data = []
       headers=[]
       headers.append("Students")
       dates_list= []
       lectures = db.collection('subjects').document(session['user']).collection(session['subject']).document("lectures").collections()
       for lecture in lectures:
          dates_list.append(lecture.id)
          for doc in lecture.stream():
             string=doc.id+"("+lecture.id+")"
             headers.append(string)
       data.append(headers)
       students = db.collection('subjects').document(session['user']).collection(session['subject']).stream()
       for student in students:
          if student.id!="lectures":
             user_data=db.collection("students").document(student.id).get()
             name_dict=user_data.to_dict()
             name=name_dict.get("name")
             sublist=[]
             sublist.append(name)
             attendances = db.collection('subjects').document(session['user']).collection(session['subject']).document(student.id).collection('attended').stream()
             attendances_list= []
             for attendance in attendances:
                attendances_list.append(attendance.id)
             for date in dates_list:
                if date in attendances_list:
                   sublist.append("yes")
                else:
                   sublist.append("no")
             data.append(sublist)
       name_of_file=session['subject']+"-report.csv"
       sheet = pe.Sheet(data)
       io = StringIO()
       sheet.save_to_memory("csv", io)
       output = make_response(io.getvalue())
       output.headers["Content-Disposition"] = "attachment; filename={}".format(name_of_file)
       output.headers["Content-type"] = "text/csv"
       return output
    else:
        return redirect('/')