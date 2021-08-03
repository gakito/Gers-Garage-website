from flask import Blueprint, json, render_template, request, flash, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from .models import db, Vehicle, Order, Booking, Staff, User
from flask_login import login_required, current_user
import json
from datetime import datetime
from fpdf import FPDF
import unicodedata

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
        date = datetime.strptime(request.form.get('date'), "%Y-%m-%d")
        comments = request.form.get('comments')
        price = services[service]

        # getting the day of the week
        weekday = date.weekday()
        # querying all the bookings to check availability
        check_bookings = Booking.query.filter_by(date=date).all()

        if len(check_bookings) > 3:
            flash(
                "Date not available. All the bookings for this day have been already filled.", category="error")
        elif weekday == 6:
            flash(
                "The garage is closed on Sundays, please select another date.", category="error")
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
        pick_order = Order.query.filter_by(order_number=order_num).first()
        # updating order parts
        if pick_order.parts == 'none':
            pick_order.parts = part_added
        else:
            pick_order.parts = pick_order.parts + ", " + part_added
        # update order price
        pick_order.price += parts[car_system][part_added]
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
        'AC Kit': 50, 'AC Condenser': 20, 'AC Compressor': 20, 'AC Evaporator': 10, 'AC Pressure Switch': 10
    },
    'Body': {
        'Bonnet': 40, 'Bumper': 40, 'Door Handle': 0, 'Door Parts': 0, 'Headlights': 0, 'Radiator Grill': 0, 'Rear Lights': 0, 'Tailgate': 0, 'Wing Mirror': 0
    },
    'Brake System': {
        'Brake Kit': 0, 'ABS Sensor': 0, 'Brake Calipers': 0, 'Brake Discs': 0, 'Brake Drum': 0, 'Brake Fluid': 0, 'Brake Fluir Reservoir': 0, 'Brake Hose': 0, 'Brake Pads': 0, 'Brake Vacuum Pump': 0, 'Handbrake': 0
    },
    'Car Battery': {
        '45Ah': 0, '60Ah': 0, '70Ah': 0, '74Ah': 0, '80Ah': 0, '95Ah': 0
    },
    'Clutch': {
        'Clutch Kit': 0, 'Clutch Cable': 0, 'Clutch Flywheel': 0, 'Clutch Master Cylinder': 0, 'Clutch Plate': 0, 'Clutch Pressure Plate': 0, 'Clutch Slave Cylinder': 0,
    },
    'Damping': {
        'Spring Kit': 0, 'Suspension Kit': 0, 'Air Suspension': 0, 'Coil Springs': 0, 'Leaf Spring': 0, 'Shock Absorber': 0, 'Spring Cap': 0, 'Strut Mount': 0, 'Suspension Accumulator': 0
    },
    'Electric System': {
        'Alternator': 0, 'Alternator Regulator': 0, 'Engine Starter': 0, 'Headlight Leveling Motor': 0, 'Horn': 0, 'Starter Solenoid': 0,
    },
    'Engine': {
        'Camshaft': 0, 'Con Rod Bearing': 0, 'Crankcase Breather': 0, 'Crankshaft': 0, 'Crankshaft Bearing': 0, 'Cylinder Head': 0, 'Cylinder Head Bolts': 0, 'Engine Block': 0, 'Engine Mount': 0, 'Engine Oil': 0, 'Exhaust Valve': 0, 'Head Gasket Kit': 0, 'Inlet Valves': 0, 'Intake Manifold': 0, 'Mounting Kit Charger': 0, 'Oil Level Sensor': 0, 'Oil Pump': 0, 'Piston': 0, 'Piston Rings': 0, 'Rocker Arm': 0, 'Rocker Cover': 0, 'Secondary Air Pump': 0, 'Tappet': 0
    },
    'Exhaust System': {
        'Catalytic Converter': 0, 'Catalytic Converter Mounting Kit': 0, 'Diesel Particulate Filter': 0, 'EGR Valve': 0, 'Exhaust Flex Pipe': 0, 'Exhaust Hanger': 0, 'Exhaust Heat Shield': 0, 'Exhaust Manifold': 0, 'Exhaust Manifold Mounting Kit': 0, 'Exhaust Mounting Kit': 0, 'Exhaust Pipe': 0, 'Front Silencer': 0, 'Lambda Sensor': 0, 'Middle Silencer': 0, 'Rear Silencer': 0, 'Silencer Mounting Kit': 0, 'Tailpipe': 0, 'Turbocharger': 0
    },
    'Filters': {
        'Air Filter': 0, 'Fuel Filter': 0, 'Oil Filter': 0, 'Pollen Filter': 0, 'Sports Air Filter': 0
    },
    'Fuel System': {
        'Accelerator Cable': 0, 'Carburetor Parts': 0, 'Fuel Cap': 0, 'Fuel Injectors': 0, 'Fuel Level Sensor': 0, 'Fuel Pressure Regulator': 0, 'Fuel Pressure Sensor': 0, 'Fuel Pump': 0, 'Fuel Tank': 0, 'High Pressure Fuel Pump': 0
    },
    'Heating': {
        'Blower Control Unit': 0, 'Blower Motor Resistor': 0, 'Heater Blower Motor': 0, 'Heater Core': 0
    },
    'Ignition': {
        'Ignition Coil': 0, 'Ignition Leads': 0, 'Ignition Module': 0, 'Knock Sensor': 0, 'Spark Plug': 0
    },
    'Light Bulbs': {
        'Fog Light Bulb': 0, 'Headlight Bulb': 0, 'Interior Lights': 0
    },
    'Pipes and Hoses': {
        'Air Conditioning Pipe': 0, 'Brake Vacuum Hose': 0, 'Coolant Flange': 0, 'Fuel Hose': 0, 'Power Steering Pipe': 0, 'Radiator Hose': 0, 'Turbo Oil Feed Line': 0, 'Turbocharger Hose': 0
    },
    'Sensors': {
        'ESP Sensor': 0, 'Fuel Temperature Sensor': 0, 'Idle Air Control Valve': 0, 'Intake Air Temperature Sensor': 0, 'Map Sensor': 0, 'Mass Air Flow Sensor': 0, 'Oil Temperature Sensor': 0, 'Temperature Sensor': 0, 'Tyre Pressure Sensor': 0
    },
    'Steering': {
        'Hydraulic Oil': 0, 'Power Steering Oil': 0, 'Power Steering Pump': 0, 'Steering Angle Sensor': 0, 'Steering Column + Electric Power Steering': 0, 'Steering Stabilizer': 0
    },
    'Suspension': {
        'Beam Axle': 0, 'Control Arm': 0, 'Control Arm Repair Kit': 0, 'Differential': 0, 'Wheel Bearing': 0, 'Wheel Hub': 0, 'Wheel Spacers': 0
    },
    'Transmission': {
        'Automatic Transmission Filter': 0, 'Automatic Transmission Fluid': 0, 'Gearbox Mount': 0, 'Repair Kit Gear Lever': 0, 'Shifter Cable': 0, 'Speed Sensor': 0, 'Transmission Oil': 0
    },
    'Tyres': {
        'Conventional': 0, 'Off-Road': 0, 'Heavy Vehicles': 0, 'Snow': 0, 'Speeder': 0
    },
}
