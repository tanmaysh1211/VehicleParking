from flask import Flask, render_template, request, redirect ,url_for, flash
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import Column, Integer, String, Boolean
from datetime import datetime
from datetime import timedelta
import matplotlib
matplotlib.use('Agg')
import io
import base64
import matplotlib.pyplot as plt
from flask import Response


app = Flask(__name__)
app.secret_key = 'mysecretkey2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'

db = SQLAlchemy()
db.init_app(app)



class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(30), nullable=False)
    name = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    pin_code = db.Column(db.String(6), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)



class Parking_lot(db.Model):
    __tablename__ = 'parking_lot'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parking_lot_name = db.Column(db.String(100), nullable=False,)
    address = db.Column(db.String(150), nullable=False)
    pin_code = db.Column(db.String(6), nullable=False)
    price_per_hour =db.Column(db.Integer, nullable = False)
    total_capacity = db.Column(db.Integer, nullable = False)
    avilable_capacity = db.Column(db.Integer, nullable = False)
    spots = db.relationship("ParkingSpot", back_populates = 'lot')



class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_number = db.Column(db.String(10), nullable=False)

    is_occupied = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref='occupied_spots')

    vehicle_number = db.Column(db.String(20), nullable=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    

    lot = db.relationship('Parking_lot', back_populates='spots')

    def calculate_duration_hours(self):
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return round(delta.total_seconds() / 3600, 2)
        return 0

    def calculate_cost(self):
        duration = self.calculate_duration_hours()
        if duration and self.lot:
            return round(duration * self.lot.price_per_hour, 2)
        return 0

class History(db.Model):
    __tablename__ = 'history'
    id = db.Column(db.Integer, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='histories')
    
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    spot = db.relationship('ParkingSpot', backref='histories')
    
    vehicle_number = db.Column(db.String(20), nullable=False)
    
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    total_time = db.Column(db.String(50), nullable=True)
    
    total_price = db.Column(db.Float, nullable=True )


with app.app_context():
    db.create_all()


# contolaller part of the app starting from here
         
@app.route('/')
def default():
    return render_template('landing.html')


@app.route('/landing_page', methods=['GET', 'POST'])
def landing_page():
    if request.method == 'GET':
        return render_template('landing.html')
    elif request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if_exists = User.query.filter_by(email=email).first()
        if if_exists:
            if if_exists.password == password:
                if if_exists.is_admin:
                    return redirect('/admin_dashboard')
                else:
                    return redirect(url_for('user_dashboard', user_id=if_exists.id))
            else:
                flash('Incorrect password. Please try again.')
                return render_template('landing.html', error='Incorrect password')
        else:
            flash('No account found with that email. Please sign up.')
            return render_template('landing.html', error='User not found')




@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        user_email = request.form.get('email')
        if_exists = User.query.filter_by(email=user_email).first()
        if if_exists:
            return redirect('/landing_page')
        else:
            user_password = request.form.get('password')
            user_name = request.form.get('name')
            user_address = request.form.get('address')
            user_pin_code = request.form.get('pin_code')
            new_user = User(email=user_email, password=user_password, name=user_name, 
                             address=user_address, pin_code=user_pin_code)
            db.session.add(new_user)
            db.session.commit()
            new_user = User.query.filter_by(email=user_email).first()
            return redirect(url_for('user_dashboard', user_id=new_user.id ))
            
           
@app.route('/user_dashboard/<int:user_id>', methods=['GET', 'POST'])
def user_dashboard(user_id):
    user = User.query.get_or_404(user_id)
    user_history = History.query.filter_by(user_id=user.id).order_by(History.id.desc()).limit(3).all()
    parking_lots = Parking_lot.query.all()
    search_results = []

    pincode = None
    if request.method == "POST":
        pincode = request.form.get("pincode")

    if pincode:  # Only search if pincode exists
        search_results = Parking_lot.query.filter(Parking_lot.address.contains(pincode)).all()
        if not search_results:
            search_results = Parking_lot.query.filter(Parking_lot.parking_lot_name.contains(pincode)).all()
    else:
        search_results = parking_lots  # Show all if no search

    return render_template(
        'user_dashboard.html',
        user=user,
        parking_lots=parking_lots,
        histirys=user_history,
        search_results=search_results
    )

@app.route('/edit_profile/<int:user_id>', methods=['GET', 'POST'])
def edit_profile(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'GET':
        return render_template('edit_user.html' , user=user)
    
    elif request.method == 'POST':
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.password = request.form.get('password')
        user.address = request.form.get('address')
        user.pin_code = request.form.get('pin_code')

        db.session.commit()
        return redirect(url_for('user_dashboard', user_id=user.id))       

@app.route('/book_spot/<int:lot_id>/<int:user_id>', methods=['GET', 'POST'])
def book_spot(lot_id, user_id):
    lot = Parking_lot.query.get_or_404(lot_id)
    user = User.query.get_or_404(user_id)

    if request.method == 'GET':
        return render_template('book_spot.html', lot=lot, user=user)

    if request.method == 'POST':
         existing_spot = ParkingSpot.query.filter_by(user_id=user.id, is_occupied=True).first()
         print(f"DEBUG: existing_spot = {existing_spot}")
         if existing_spot:
             return render_template('book_spot.html', lot=lot, user=user, 
                               error='You already have an active booking. Please release it first.')
            #  print("DEBUG: User already has a booking, blocking!")
            #  flash('You already have an active booking. Please release it before booking a new spot.')             
            #  return redirect(url_for('user_dashboard', user_id=user.id))

         if lot.avilable_capacity <= 0:
            return redirect(url_for('user_dashboard', user_id=user.id))
    
         vehicle_number = request.form.get('vehicle_number')
         if not vehicle_number:
            return redirect(url_for('user_dashboard', user_id=user.id))

         spot = ParkingSpot.query.filter_by(lot_id=lot.id, is_occupied=False).first()
         if not spot:
            return redirect(url_for('user_dashboard', user_id=user.id))

         spot.is_occupied = True
         spot.user_id = user.id
         spot.vehicle_number = vehicle_number
         spot.start_time = datetime.now()
         spot.end_time = None

         lot.avilable_capacity -= 1

         
         new_history = History(
            user_id=user.id,
            spot_id=spot.id,
            vehicle_number=vehicle_number,
            start_time=spot.start_time,
            total_price=0,  # Initially set to 0, will be updated on release
         )
         db.session.add(new_history)

         db.session.commit()
         return redirect(url_for('user_dashboard', user_id=user.id))


@app.route('/release_preview/<int:spot_id>/<int:user_id>', methods=['GET'])
def release_preview(spot_id, user_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    user = User.query.get_or_404(user_id)

    if not spot.is_occupied or spot.user_id != user.id:
        return redirect(url_for('user_dashboard', user_id=user.id))

    fake_end_time = datetime.now()
    time_delta = fake_end_time - spot.start_time
    total_seconds = time_delta.total_seconds()
    
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)

    formatted_duration = f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"

    price = round((total_seconds / 3600) * spot.lot.price_per_hour, 2)

    return render_template(
        'release_spot.html',
        spot=spot,
        user=user,
        price=price,
        formatted_duration=formatted_duration
    )



@app.route('/confirm_release/<int:spot_id>/<int:user_id>', methods=['POST'])
def confirm_release(spot_id, user_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    user = User.query.get_or_404(user_id)

    if not spot.is_occupied or spot.user_id != user.id:
        return redirect(url_for('user_dashboard', user_id=user.id))

    spot.end_time = datetime.now()
    duration = spot.calculate_duration_hours()
    cost = spot.calculate_cost()
    total_time  = spot.end_time - spot.start_time
    total_seconds = total_time.total_seconds()

    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)

    formatted_duration = f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"


    history_entry = History.query.filter_by(user_id=user.id, spot_id=spot.id).order_by(History.id.desc()).first()
    if history_entry:
        history_entry.end_time = spot.end_time
        history_entry.total_price = cost
        history_entry.total_time = formatted_duration

    spot.is_occupied = False
    spot.user_id = None
    spot.vehicle_number = None
    spot.start_time = None
    spot.end_time = None

    spot.lot.avilable_capacity += 1
    db.session.commit()
    return redirect(url_for('user_dashboard', user_id=user.id))


def create_admin():
    if_exists = User.query.filter_by(is_admin=True).first()
    if not if_exists:
        admin = User(email = 'sharma.tanmay*****@gmail.com',password = '********', name = 'tanmay sharma', 
                      address = 'gurgaon', pin_code = '122110', is_admin = True)
        db.session.add(admin)
        db.session.commit()

@app.route('/admin_dashboard', methods=['GET','POST'])
def  admin_dashboard():
    parking_lots = Parking_lot.query.all()
    search_results = None
    if request.method == 'GET':
        return render_template('admin_dashboard.html', parking_lots=parking_lots)

    if request.method == "POST":
        pincode = request.form.get("pincode")
        search_results = Parking_lot.query.filter_by(pin_code=pincode).all()
        if not search_results:
            search_results = Parking_lot.query.filter(Parking_lot.address.contains(pincode)).all()
            if not search_results:
                search_results = Parking_lot.query.filter(Parking_lot.parking_lot_name.contains(pincode)).all()

    
    return  render_template('admin_dashboard.html',parking_lots=parking_lots,search_results=search_results)



@app.route("/add_parking",methods = ["GET","POST"])
def add_parking():
    if request.method =="GET":
        return render_template("add_parking.html")
    elif request.method =="POST":
        name = request.form['lot_name']
        address = request.form['address']
        pin_code = request.form['pin_code']
        price_per_hour = int(request.form['price'])
        total_capacity = int(request.form['capacity'])
        

        new_lot = Parking_lot(
            parking_lot_name=name,
            address=address,
            pin_code=pin_code,
            price_per_hour=price_per_hour,
            total_capacity=total_capacity,
            avilable_capacity=total_capacity
        )
        db.session.add(new_lot)
        db.session.commit()

        for i in range(1, total_capacity + 1):
            spot = ParkingSpot(
                lot_id=new_lot.id,
                spot_number=f"Spot-{i}",
                is_occupied=False
            )
            db.session.add(spot)
        db.session.commit()

    return redirect('/admin_dashboard')        



@app.route('/view_lot/<int:lot_id>')
def view_lot(lot_id):
    lot = Parking_lot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    return render_template('view_parking.html', lot=lot, spots=spots)

@app.route('/invoice/<int:history_id>/<int:user_id>')
def invoice(history_id, user_id):
    h = History.query.get_or_404(history_id)
    user = User.query.get_or_404(user_id)
    return render_template('invoice.html', h=h, user=user)



@app.route("/edit_parking/<int:lot_id>", methods=["GET", "POST"])
def edit_parking(lot_id):
    lot = Parking_lot.query.get_or_404(lot_id)

    if request.method == "GET":
        return render_template("edit_parking.html", lot=lot)
    
    elif request.method == "POST":
        new_name = request.form["lot_name"]
        new_address = request.form["address"]
        new_price = int(request.form["price"])
        new_total_capacity = int(request.form["capacity"])

        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, is_occupied=True).count()
        current_spots = ParkingSpot.query.filter_by(lot_id=lot.id).all()
        current_total_capacity = lot.total_capacity

        if new_total_capacity < occupied_spots:
            return (
                f"{occupied_spots} spots are already occupied.", 400
            )

        lot.parking_lot_name = new_name
        lot.address = new_address
        lot.price_per_hour = new_price
        lot.total_capacity = new_total_capacity
        lot.avilable_capacity = new_total_capacity - occupied_spots

        if new_total_capacity > current_total_capacity:
            for i in range(current_total_capacity + 1, new_total_capacity + 1):
                spot = ParkingSpot(
                    lot_id=lot.id,
                    spot_number=f"Spot-{i}",
                    is_occupied=False
                )
                db.session.add(spot)

        elif new_total_capacity < current_total_capacity:
            spots_desc = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.id.desc()).all()
            count_to_delete = current_total_capacity - new_total_capacity
            deleted_count = 0

            for spot in spots_desc:
                if deleted_count >= count_to_delete:
                    break
                if not spot.is_occupied:
                    db.session.delete(spot)
                    deleted_count += 1
            
            if deleted_count < count_to_delete:
                return (
                    f"Cannot reduce capacity to {new_total_capacity} because not enough free spots to remove.",
                    400
                )
        db.session.commit()
        return redirect(url_for("admin_dashboard"))



@app.route("/view_users")
def view_users():
    users = User.query.all()
    return render_template('view_users.html',users=users)

@app.route("/delete_lot/<int:lot_id>", methods=["POST"])
def delete_lot(lot_id):
    lot = Parking_lot.query.get_or_404(lot_id)
    
    occupied_spots = ParkingSpot.query.filter_by(lot_id=lot_id, is_occupied=True).count()
    if occupied_spots > 0:
        return "Cannot delete this parking lot because some spots are still occupied.", 400
    ParkingSpot.query.filter_by(lot_id=lot_id).delete()
    db.session.delete(lot)
    db.session.commit()
    
    return redirect(url_for("admin_dashboard"))




#summary page admin



@app.route('/admin_summary')
def admin_summary():
    parking_lots = Parking_lot.query.all()

    lot_names = []
    occupied_counts = []
    free_counts = []
    total_incomes = []

    for lot in parking_lots:
        lot_names.append(lot.parking_lot_name)
        
        total_spots = ParkingSpot.query.filter_by(lot_id=lot.id).count()
        occupied_spots = ParkingSpot.query.filter_by(lot_id=lot.id, is_occupied=True).count()
        free_spots = total_spots - occupied_spots
        
        # Sum total_price from History for this lot's spots
        histories = History.query.join(ParkingSpot).filter(ParkingSpot.lot_id == lot.id).all()
        total_income = sum(h.total_price or 0 for h in histories)

        occupied_counts.append(occupied_spots)
        free_counts.append(free_spots)
        total_incomes.append(total_income)

    # Plot Occupied vs Free spots bar chart
    fig, ax = plt.subplots(figsize=(10,5))
    ax.bar(lot_names, occupied_counts, label='Occupied', color='red')
    ax.bar(lot_names, free_counts, bottom=occupied_counts, label='Free', color='green')
    ax.set_ylabel('Number of Spots')
    ax.set_title('Occupied vs Free Parking Spots')
    ax.legend()
    plt.xticks(rotation=45, ha='right')

    img = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img, format='png')
    plt.close(fig)
    img.seek(0)
    occupied_free_chart = base64.b64encode(img.getvalue()).decode()

    # Plot Total income bar chart
    fig2, ax2 = plt.subplots(figsize=(10,5))
    ax2.bar(lot_names, total_incomes, color='blue')
    ax2.set_ylabel('Total Income (₹)')
    ax2.set_title('Total Income per Parking Lot')
    plt.xticks(rotation=45, ha='right')

    img2 = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img2, format='png')
    plt.close(fig2)
    img2.seek(0)
    income_chart = base64.b64encode(img2.getvalue()).decode()

    return render_template('admin_summary.html',
                           occupied_free_chart=occupied_free_chart,
                           income_chart=income_chart)


#summary page user

@app.route('/user_summary/<int:user_id>')
def user_summary(user_id):
    user = User.query.get_or_404(user_id)
    today = datetime.today().date()
    last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    day_labels = [d.strftime('%a') for d in last_7_days]

    data = {d: 0 for d in last_7_days}
    histories = History.query.filter_by(user_id=user.id).all()
    for h in histories:
        if h.end_time:
            date = h.end_time.date()
            if date in data:
                data[date] += h.total_price

    fig, ax = plt.subplots()
    ax.bar(day_labels, list(data.values()), color='skyblue')
    ax.set_title('Weekly Parking Spend')
    ax.set_ylabel('₹ per day')

    img = io.BytesIO(); plt.tight_layout(); plt.savefig(img, format='png'); plt.close(); img.seek(0)
    chart = base64.b64encode(img.getvalue()).decode()

    return render_template('user_summary.html', user=user, chart=chart)




if __name__ == '__main__':
    with app.app_context():
         
         create_admin()
    app.run(debug=True)
