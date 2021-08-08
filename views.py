from flask import Blueprint, json, render_template, request, flash, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from .models import db, Vehicle, Order, Booking, Staff, User
from flask_login import login_required, current_user
import json
from datetime import datetime
from fpdf import FPDF

views = Blueprint('views', __name__)


def __len__(self):
    return len(self.name)


@views.route('/', methods=['POST', 'GET'])
@login_required
def home():

    return render_template('home.html', user=current_user)


@views.route('vehicle_reg', methods=['GET', 'POST'])
@login_required
def vehicle_reg():

    moto = False
    type_selected = request.form.get('type')
    if type_selected == "Motorbike":
        moto = True

    if request.method == 'POST':
        make = request.form.get('make')
        license = request.form.get('license')
        type = request.form.get('type')
        engine = request.form.get('engine')

        new_car = Vehicle(make=make, license_plate=license,
                          engine_type=engine, type=type, user_id=current_user.id)
        db.session.add(new_car)
        db.session.commit()
        flash("Vehicle registred!", category="success")

    return render_template('vehicle_reg.html', user=current_user, vehicles_type_list=vehicles_type_list, bikes=bikes, cars_makes=cars_makes, eng_type=eng_type, moto=moto)


@views.route('booking', methods=['GET', 'POST'])
@login_required
def booking():

    car_list = Vehicle.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        service = request.form.get('service')
        vehicle = Vehicle.query.filter_by(
            license_plate=(request.form.get('vehicle'))).first()
        date = datetime.strptime(request.form.get('date'), "%d-%m-%Y")
        comments = request.form.get('comments')
        price = services[service]

        # getting the day of the week
        #weekday = date.weekday()
        # querying all the bookings to check availability
        check_bookings = Booking.query.filter_by(date=date).all()

        if len(check_bookings) > 3:
            flash(
                "Date not available. All the bookings for this day have been already filled.", category="error")
        # elif weekday == 6:
            # flash(
            # "The garage is closed on Sundays, please select another date.", category="error")
        else:
            # assigning staffs automatically. it assigns the staff with less order
            if Booking.query.all():
                book_id = Booking.query.order_by(
                    Booking.booking_id.desc()).first().booking_id + 1

                # function to count the least frequent element on a list. got from https://stackoverflow.com/questions/47098026/identify-least-common-number-in-a-list-python
                def least_common(lst):
                    return min(lst, key=lambda x: (lst.count(x), lst[::-1].index(x)))
                # querying all the orders
                all_orders = Order.query.all()
                # creating the list
                staffs = []
                # setting the values on the list
                for order in all_orders:
                    staffs.append(order.staff_id)
                # getting the least element of the list
                assigned_staff = least_common(staffs)
            else:
                book_id = 1
                assigned_staff = 1
            # creating the booking
            new_booking = Booking(date=date)
            db.session.add(new_booking)
            db.session.commit()
            # creating the order
            new_order = Order(service=service, vehicle_id=vehicle.vehicle_id,
                              booking_id=book_id, price=price*cars_makes[vehicle.make], parts='none', comments=comments, status='active', staff_id=assigned_staff)
            db.session.add(new_order)
            db.session.commit()

    return render_template('booking.html', user=current_user, cars=car_list, services=services, str=str)


@views.route('staff', methods=['GET', 'POST'])
@login_required
def staff():

    if current_user.id != 1:
        return redirect(url_for("views.home"))

    employee = Staff.query.all()

    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        role = request.form.get('role')

        new_staff = Staff(staff_first_name=name, staff_surname=surname,
                          role=role)
        db.session.add(new_staff)
        db.session.commit()

    return render_template('staff.html', user=current_user, employee=employee, str=str)


@views.route('delete-staff', methods=['POST'])
@login_required
def delete_staff():
    if current_user.id != 1:
        return redirect(url_for("views.home"))

    # getting the staff id number
    staff = json.loads(request.data)
    staffID = staff['staff_id']

    # the employee can only be deleted if is not assigned to an order
    check_staff = Order.query.filter_by(
        staff_id=staffID, status="active").first()
    if check_staff:
        flash("Staff assigned to an active order.", category="error")
    else:
        # deleting the staff
        emp = Staff.query.get(staffID)
        db.session.delete(emp)
        db.session.commit()
        flash("Staff deleted.", category='success')
    return jsonify({})


@views.route('orders', methods=['GET', 'POST'])
@login_required
def orders():
    return render_template("orders.html", user=current_user)


@views.route('close', methods=['POST', 'GET'])
@login_required
def close():
    if current_user.id != 1:
        return redirect(url_for("views.home"))

    order = Order.query.all()
    orders_list = []

    for o in order:
        if o.status == 'active':
            num = o.order_number
            serv = o.service
            v = Vehicle.query.filter_by(vehicle_id=o.vehicle_id).first()
            brand = v.make
            plate = v.license_plate
            orders_list.append(str(num) + " - " + brand +
                               " - " + plate + " - " + serv)

    if request.method == 'POST' and "select_order" in request.form:
        order_num = request.form.get('select_order')
        pick_order = Order.query.filter_by(order_number=order_num).first()
        pick_order.status = 'closed'

        # querying vehicles, users and booking tables
        check_vehicle = Vehicle.query.filter_by(
            vehicle_id=pick_order.vehicle_id).first()
        get_user_details = User.query.filter_by(
            id=check_vehicle.user_id).first()
        get_booking = Booking.query.filter_by(
            booking_id=pick_order.booking_id).first()

        # creating the invoice
        pdf = FPDF('P', 'mm', "A5")
        pdf.add_page()
        pdf.set_font('helvetica', '', 12)
        # adding text
        pdf.cell(40, 10, "Ger's Garage", ln=True)
        pdf.cell(40, 10, "Customer: ")
        pdf.cell(40, 10, get_user_details.first_name +
                 " " + get_user_details.surname, ln=True)
        pdf.cell(40, 10, "Mobile Number: ")
        pdf.cell(40, 10, get_user_details.mobile, ln=True)
        pdf.cell(40, 5, "-----------------------------------------------", ln=True)
        pdf.cell(40, 10, "Vehicle: ")
        pdf.cell(40, 10, check_vehicle.make, ln=True)
        pdf.cell(40, 10, "Licence: ")
        pdf.cell(40, 10, check_vehicle.license_plate, ln=True)
        pdf.cell(40, 5, "-----------------------------------------------", ln=True)
        pdf.cell(40, 10, "Service: ")
        pdf.cell(40, 10, pick_order.service, ln=True)
        pdf.cell(40, 10, "Parts added: ")
        pdf.cell(40, 10, pick_order.parts, ln=True)
        pdf.cell(40, 10, "Order date: ")
        pdf.cell(40, 10, str(pick_order.date), ln=True)
        pdf.cell(40, 10, "Service date: ")
        pdf.cell(40, 10, str(get_booking.date), ln=True)
        pdf.cell(40, 10, "TOTAL DUE: ")
        #euro = chr(8364)
        #pdf.cell(40, 0, euro)
        pdf.cell(40, 10, str(pick_order.price), ln=True)
        # creating file
        pdf.output("invoice_order_"+str(order_num)+".pdf")

        db.session.commit()

        return redirect(url_for('views.orders'))

    return render_template("close.html", user=current_user, orders_list=orders_list, int=int, order=order)


@ views.route('parts', methods=['POST', 'GET'])
@ login_required
def adding_parts():
    if current_user.id != 1:
        return redirect(url_for("views.home"))

    # querying all orders
    order = Order.query.all()
    orders_list = []

    part_value = request.form.get('part1')
    # showing all active orders and their vehicles
    for o in order:
        if o.status == 'active':
            num = o.order_number
            serv = o.service
            v = Vehicle.query.filter_by(vehicle_id=o.vehicle_id).first()
            brand = v.make
            plate = v.license_plate
            orders_list.append(str(num) + " - " + brand +
                               " - " + plate + " - " + serv)

    if request.method == 'POST':
        # getting the order and the part to be added
        order_num = request.form.get('select_order')
        car_system = request.form.get('part1')
        part_added = request.form.get('part2')

        # querying the order selected and the vehicle from the order
        pick_order = Order.query.filter_by(order_number=order_num).first()
        vehicle = Vehicle.query.filter_by(
            vehicle_id=pick_order.vehicle_id).first()

        # updating order parts
        if pick_order.parts == 'none':
            pick_order.parts = part_added
        else:
            pick_order.parts = pick_order.parts + ", " + part_added

        # update order price. the price is set according to the make of the car following the multiplying fcator created
        pick_order.price += parts[car_system][part_added] * \
            cars_makes[vehicle.make]
        db.session.commit()
        return redirect(url_for('views.adding_parts'))

    return render_template("parts.html", user=current_user, orders_list=orders_list, int=int, order=order, parts=parts, part_value=part_value)


# route to dynamically change cars' parts in a dropdown menu. Got it on https://www.youtube.com/watch?v=I2dJuNwlIH0/
@ views.route('parts/<part>', methods=['POST', 'GET'])
@ login_required
def adding_part(part):
    if current_user.id != 1:
        return redirect(url_for("views.home"))

    parts_list = parts[part]

    return jsonify(parts_list)


# lists hard-coded used as variables
services = {
    "Annual Service": 200, "Major Service": 300, "Repair": 150, "Major Repair": 300
}

vehicles_type_list = [
    'Compact', 'Convertible', 'Coupé', 'Hatchback', 'Mini Bus', 'Mini Van', 'Motorbike', 'Pickup Truck', 'Sedan', 'SUV', "Other"
]

bikes = [
    'BMW', 'Harley Davidson', 'Honda',
    'Kawasaki', 'Suzuki', 'Triumph', 'Yamaha', "Other"
]

eng_type = [
    'Diesel',
    'Eletric',
    'Hybrid',
    'Petrol'
]

# each make has a price factor that modifies prices for services and parts for that specific make. estimative based on data from https://lifehacker.com/the-car-brands-with-the-highest-maintenance-costs-over-1781639773
cars_makes = {
    'Acura': 1.8, 'Alpha Romeo': 3.5, 'Aston Martin': 4, 'Audi': 2.3, 'Bentley': 4, 'BMW': 3.2, 'Bugatti': 8, 'Buick': 1.6, 'Cadillac': 2.3, 'Chrysler': 1.9, 'Cintroen': 1.2, 'Daewoo': 1.3, 'Dodge': 1.9, 'Ferrari': 8, 'Fiat': 1.1, 'Ford': 1.7, 'GMC': 1.4, 'Honda': 1.3, 'Hyundai': 1.5, 'Infiniti': 1.7, 'Jac Motors': 1, 'Jaguar': 4, 'Jeep': 1.5, 'KIA': 1.6, 'Lamborghini': 7, 'Land Rover': 1.6, 'Lexus': 1.4, 'Lincoln': 3, 'Maserati': 5, 'Mazda': 1.4, 'McLaren': 8, 'Mercedes-Benz': 2.3, 'Mini': 1.4, 'Mitsubishi': 1.3, 'Nissan': 1.4, 'Opel': 1.6, 'Peugeot': 1, 'Porshe': 4, 'Ram': 1.7, 'Renault': 1.2, 'Skoda': 1.4, 'Smart': 1.4, 'Subaru': 1.5, 'Suzuki': 1.2, 'Tesla': 4, 'Toyota': 1, 'Volkswagen': 1.1, 'Volvo': 2.3, "Other": 1
}

parts = {
    'Air Conditioning': {
        'AC Kit': 400, 'AC Condenser': 160, 'AC Compressor': 260, 'AC Evaporator': 100, 'AC Pressure Switch': 20
    },
    'Body': {
        'Bonnet': 100, 'Bumper': 140, 'Door Handle': 20, 'Door Parts': 100, 'Headlights': 100, 'Radiator Grill': 20, 'Rear Lights': 60, 'Tailgate': 200, 'Wing Mirror': 15
    },
    'Brake System': {
        'Brake Kit': 400, 'ABS Sensor': 15, 'Brake Calipers': 80, 'Brake Discs': 18, 'Brake Drum': 40, 'Brake Fluid': 10, 'Brake Fluir Reservoir': 10, 'Brake Hose': 20, 'Brake Pads': 14, 'Brake Vacuum Pump': 300, 'Handbrake': 40
    },
    'Car Battery': {
        '45Ah': 70, '60Ah': 80, '70Ah': 85, '74Ah': 89, '80Ah': 100, '95Ah': 120
    },
    'Clutch': {
        'Clutch Kit': 250, 'Clutch Cable': 20, 'Clutch Flywheel': 98, 'Clutch Master Cylinder': 40, 'Clutch Plate': 40, 'Clutch Pressure Plate': 110, 'Clutch Slave Cylinder': 25
    },
    'Damping': {
        'Spring Kit': 140, 'Suspension Kit': 300, 'Air Suspension': 1500, 'Coil Springs': 60, 'Leaf Spring': 180, 'Shock Absorber': 80, 'Spring Cap': 10, 'Strut Mount': 30
    },
    'Electric System': {
        'Alternator': 110, 'Alternator Regulator': 30, 'Engine Starter': 80, 'Headlight Leveling Motor': 40, 'Horn': 10, 'Starter Solenoid': 70
    },
    'Engine': {
        'Camshaft': 2000, 'Con Rod Bearing': 30, 'Crankcase Breather': 10, 'Crankshaft': 100, 'Crankshaft Bearing': 10, 'Cylinder Head': 250, 'Cylinder Head Bolts': 50, 'Engine Block': 2000, 'Engine Mount': 40, 'Engine Oil': 10, 'Exhaust Valve': 120, 'Head Gasket Kit': 100, 'Inlet Valves': 180, 'Intake Manifold': 380, 'Mounting Kit Charger': 0, 'Oil Level Sensor': 5, 'Oil Pump': 15, 'Piston': 100, 'Piston Rings': 20, 'Rocker Arm': 10, 'Rocker Cover': 10, 'Secondary Air Pump': 15, 'Tappet': 30
    },
    'Exhaust System': {
        'Catalytic Converter': 175, 'Catalytic Converter Mounting Kit': 300, 'Diesel Particulate Filter': 900, 'EGR Valve': 300, 'Exhaust Flex Pipe': 80, 'Exhaust Hanger': 20, 'Exhaust Heat Shield': 70, 'Exhaust Manifold': 150, 'Exhaust Manifold Mounting Kit': 280, 'Exhaust Mounting Kit': 300, 'Exhaust Pipe': 25, 'Front Silencer': 20, 'Lambda Sensor': 20, 'Middle Silencer': 20, 'Rear Silencer': 20, 'Silencer Mounting Kit': 50, 'Tailpipe': 25, 'Turbocharger': 60
    },
    'Filters': {
        'Air Filter': 10, 'Fuel Filter': 30, 'Oil Filter': 25, 'Pollen Filter': 20, 'Sports Air Filter': 15
    },
    'Fuel System': {
        'Accelerator Cable': 10, 'Carburetor Parts': 200, 'Fuel Cap': 5, 'Fuel Injectors': 90, 'Fuel Level Sensor': 20, 'Fuel Pressure Regulator': 45, 'Fuel Pressure Sensor': 28, 'Fuel Pump': 30, 'Fuel Tank': 20, 'High Pressure Fuel Pump': 50
    },
    'Heating': {
        'Blower Control Unit': 100, 'Blower Motor Resistor': 30, 'Heater Blower Motor': 40, 'Heater Core': 80
    },
    'Ignition': {
        'Ignition Coil': 30, 'Ignition Leads': 30, 'Ignition Module': 60, 'Knock Sensor': 20, 'Spark Plug': 15
    },
    'Light Bulbs': {
        'Fog Light Bulb': 16, 'Headlight Bulb': 12, 'Interior Lights': 5
    },
    'Pipes and Hoses': {
        'Air Conditioning Pipe': 10, 'Brake Vacuum Hose': 15, 'Coolant Flange': 20, 'Fuel Hose': 20, 'Power Steering Pipe': 25, 'Radiator Hose': 30, 'Turbo Oil Feed Line': 20, 'Turbocharger Hose': 20
    },
    'Sensors': {
        'ESP Sensor': 20, 'Fuel Temperature Sensor': 20, 'Idle Air Control Valve': 40, 'Intake Air Temperature Sensor': 20, 'Map Sensor': 20, 'Mass Air Flow Sensor': 20, 'Oil Temperature Sensor': 30, 'Temperature Sensor': 20, 'Tyre Pressure Sensor': 10
    },
    'Steering': {
        'Hydraulic Oil': 10, 'Power Steering Oil': 10, 'Power Steering Pump': 30, 'Steering Angle Sensor': 12, 'Steering Column + Electric Power Steering': 50, 'Steering Stabilizer': 30
    },
    'Suspension': {
        'Beam Axle': 400, 'Control Arm': 200, 'Control Arm Repair Kit': 300, 'Differential': 0, 'Wheel Bearing': 90, 'Wheel Hub': 50, 'Wheel Spacers': 40
    },
    'Transmission': {
        'Automatic Transmission Filter': 13, 'Automatic Transmission Fluid': 15, 'Gearbox Mount': 600, 'Repair Kit Gear Lever': 300, 'Shifter Cable': 80, 'Speed Sensor': 50, 'Transmission Oil': 15
    },
    'Tyres': {
        'Conventional': 40, 'Off-Road': 60, 'Heavy Vehicles': 90, 'Snow': 150, 'Speeder': 200
    },
}
