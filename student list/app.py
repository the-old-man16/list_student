from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt  # เพิ่มการนำเข้า Bcrypt

app = Flask(__name__)

# เชื่อมต่อกับฐานข้อมูล MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:yourwassword@localhost/student_db'  # แก้ไขตรงนี้
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # ใช้สำหรับ flash message
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)  # สร้างอ็อบเจกต์ Bcrypt

# 🔹 **Model สำหรับตาราง students**
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    course = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)  


# 🔹 **สร้างฐานข้อมูลเมื่อเริ่มต้นโปรเจค**
with app.app_context():
    db.create_all()  # สร้างฐานข้อมูลใหม่


@app.route('/')
def home():
    return render_template('home.html')

# 🔹 **หน้าแรก (สมัครเรียน)**
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        course = request.form['course']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # ตรวจสอบว่ารหัสผ่านกับยืนยันรหัสผ่านตรงกันหรือไม่
        if password != confirm_password:
            flash('รหัสผ่านและยืนยันรหัสผ่านไม่ตรงกัน', 'danger')
            return redirect(url_for('index'))

        # เข้ารหัสรหัสผ่าน
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        new_student = Student(name=name, email=email, course=course, password_hash=password_hash)  # ใช้ password_hash
        db.session.add(new_student)
        db.session.commit()

        flash('สมัครเรียนสำเร็จ!', 'success')
        return redirect(url_for('success'))

    return render_template('index.html')


# 🔹 **แสดงรายชื่อผู้สมัคร**
@app.route('/checklist')
def checklist():
    students = Student.query.all()
    return render_template('checklist.html', students=students)

# 🔹 **หน้าสำเร็จ**
@app.route('/success')
def success():
    return render_template('success.html')

# 🔹 **ลบข้อมูลนักศึกษา**
@app.route('/delete_student/<int:student_id>', methods=['GET'])
def delete_student(student_id):
    student = Student.query.get(student_id)
    if student:
        db.session.delete(student)
        db.session.commit()
        flash('ลบข้อมูลสำเร็จ!', 'success')

    return redirect(url_for('checklist'))

# 🔹 **แก้ไขข้อมูลนักศึกษา**
@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student = Student.query.get(student_id)

    if request.method == 'POST':
        student.name = request.form['name']
        student.email = request.form['email']
        student.course = request.form['course']
        db.session.commit()

        flash('อัปเดตข้อมูลสำเร็จ!', 'success')
        return redirect(url_for('checklist'))

    return render_template('edit_student.html', student=student)

@app.route('/profile')
def profile():
    # ตรวจสอบการเข้าสู่ระบบ
    if 'user_id' not in session:
        flash('กรุณาล็อกอินก่อนที่จะเข้าถึงหน้าข้อมูลส่วนตัว', 'danger')
        return redirect(url_for('login'))  # ถ้ายังไม่ได้ล็อกอิน ให้ไปที่หน้า login

    student = Student.query.filter_by(id=session.get('user_id')).first()
    return render_template('profile.html', student=student)


# 🔹 **แก้ไขข้อมูลนักศึกษา**
@app.route('/update_student', methods=['GET', 'POST'])
def update_student():
    if 'user_id' not in session:  # ตรวจสอบว่าได้ล็อกอินหรือยัง
        flash('กรุณาล็อกอินก่อนที่จะเข้าถึงหน้าข้อมูลส่วนตัว', 'danger')
        return redirect(url_for('login'))  # ถ้ายังไม่ได้ล็อกอิน ให้ไปที่หน้า login

    student = Student.query.filter_by(id=session.get('user_id')).first()  # ดึงข้อมูลของผู้ใช้จาก session

    if request.method == 'POST':
        password = request.form['password']

        # ตรวจสอบรหัสผ่านที่กรอก
        if not bcrypt.check_password_hash(student.password_hash, password):  # ตรวจสอบรหัสผ่าน
            flash('รหัสผ่านไม่ถูกต้อง', 'danger')
            return redirect(url_for('update_student'))

        # อัปเดตข้อมูลส่วนตัว
        student.name = request.form['name']
        student.email = request.form['email']
        student.course = request.form['course']

        # หากมีการเปลี่ยนรหัสผ่าน
        new_password = request.form.get('new_password')
        if new_password:
            password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            student.password_hash = password_hash  # อัปเดตรหัสผ่านใหม่

        db.session.commit()

        flash('อัปเดตข้อมูลสำเร็จ!', 'success')
        return redirect(url_for('profile'))  # ไปที่หน้าโปรไฟล์ของผู้ใช้

    return render_template('update_student.html', student=student)
  # หน้าโปรไฟล์ของผู้ใช้

    return render_template('update_student.html', student=student)


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contract')
def contract():
    return render_template('contract.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']

        # กำหนดรหัสผ่านของแอดมิน
        admin_password = 'oasis69'  # ตั้งรหัสผ่านของแอดมิน

        # ตรวจสอบรหัสผ่าน
        if password == admin_password:
            session['is_admin'] = True  # บันทึกสถานะเข้าสู่ระบบ
            flash('เข้าสู่ระบบแอดมินสำเร็จ!', 'success')
            return redirect(url_for('admin_dashboard'))  # ส่งไปหน้าแสดงข้อมูลแอดมิน
        else:
            flash('รหัสผ่านไม่ถูกต้อง!', 'danger')

    return render_template('admin_login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # ตรวจสอบอีเมลในฐานข้อมูล
        student = Student.query.filter_by(email=email).first()

        if student and bcrypt.check_password_hash(student.password_hash, password):
            # ถ้ารหัสผ่านถูกต้อง ให้ตั้ง session สำหรับการล็อกอิน
            session['user_id'] = student.id
            flash('เข้าสู่ระบบสำเร็จ!', 'success')
            return redirect(url_for('update_student'))  # ไปที่หน้า update_student
        else:
            flash('อีเมลหรือรหัสผ่านไม่ถูกต้อง', 'danger')

    return render_template('login.html')


# หน้าแสดงข้อมูลแอดมิน (แสดงรายชื่อนักศึกษา)
@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    # ตรวจสอบว่าเป็นแอดมินหรือไม่
    if not session.get('is_admin'):
        flash('คุณต้องเข้าสู่ระบบแอดมินก่อน!', 'danger')
        return redirect(url_for('admin_login'))  # ถ้าไม่ได้เข้าสู่ระบบแอดมิน จะไปหน้า login

    students = Student.query.all()  # ดึงข้อมูลนักศึกษาทั้งหมดจากฐานข้อมูล
    return render_template('admin_dashboard.html', students=students)  # แสดงข้อมูล

@app.route('/logout')
def logout():
    session.pop('is_admin', None)  # ลบ session
    session.pop('user_id', None)  # ลบ session ของผู้ใช้
    flash('ออกจากระบบแล้ว', 'success')
    return redirect(url_for('home'))  # กลับไปหน้า home


if __name__ == '__main__':
    app.run(debug=True)
