from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.BINARY(16), primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    about_me = db.Column(db.Text)
    address = db.Column(db.Text)
    birthday = db.Column(db.Text)
    country = db.Column(db.Text)
    first_name = db.Column(db.Text)
    last_name = db.Column(db.Text)
    gender = db.Column(db.Text)
    language = db.Column(db.Text)
    logout_event = db.Column(db.Integer)
    logout_date = db.Column(db.Date)
    phone = db.Column(db.String(10))
    profile_picture = db.Column(db.Text)
    rating = db.Column(db.SmallInteger)
    search_price_min = db.Column(db.Integer)
    search_price_max = db.Column(db.Integer)
    search_city = db.Column(db.Text)
    property_type = db.Column(db.Text)
    search_status = db.Column(db.Text)
    search_text = db.Column(db.Text)

    # Relationships
    agent = db.relationship('Agent', backref='user', uselist=False)
    client = db.relationship('Client', backref='user', uselist=False)
    appointments = db.relationship('Appointment', backref='user', lazy=True)
    saved = db.relationship('Saved', backref='user', lazy=True)


class Agent(db.Model):
    __tablename__ = 'agent'

    user_id = db.Column(db.BINARY(16), db.ForeignKey('users.user_id'), primary_key=True)
    company_name = db.Column(db.Text)
    num_customers = db.Column(db.Integer)
    num_properties = db.Column(db.Integer)
    properties_rented = db.Column(db.Integer)
    properties_sold = db.Column(db.Integer)

    houses = db.relationship('House', backref='agent', lazy=True)
    listing_availability = db.relationship('ListingAvailability', backref='agent', lazy=True)


class House(db.Model):
    __tablename__ = 'houses'

    house_id = db.Column(db.BINARY(16), primary_key=True)
    street = db.Column(db.Text, nullable=False)
    floor = db.Column(db.Text)
    zipcode = db.Column(db.Integer, nullable=False)
    unit_num = db.Column(db.Text)
    country = db.Column(db.Text, nullable=False)
    state = db.Column(db.Text)
    city = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.BINARY(16), db.ForeignKey('agent.user_id'))
    appliances = db.Column(db.Text)
    bathrooms = db.Column(db.Integer)
    bathroom_details = db.Column(db.Text)
    bedrooms = db.Column(db.Integer)
    bedroom_details = db.Column(db.Text)
    community = db.Column(db.Text)
    condition = db.Column(db.Text)
    cooling = db.Column(db.Boolean)
    laundry = db.Column(db.Boolean)
    description = db.Column(db.Text, nullable=False)
    exterior_features = db.Column(db.Text)
    garage = db.Column(db.Boolean)
    heating = db.Column(db.Boolean)
    HOA = db.Column(db.Integer, nullable=False)
    photos = db.Column(db.Text)
    living_room = db.Column(db.Text)
    square_feet = db.Column(db.Integer)
    material_info = db.Column(db.Text)
    name = db.Column(db.Text, nullable=False)
    num_views = db.Column(db.Integer)
    notable_dates = db.Column(db.Text)
    amenities = db.Column(db.Text)
    interior_features = db.Column(db.Text)
    property_info = db.Column(db.Text)
    owner_email = db.Column(db.Text)
    owner_first = db.Column(db.Text)
    owner_last = db.Column(db.Text)
    owner_phone = db.Column(db.Text)
    parking_spots = db.Column(db.Integer)
    pet_policy = db.Column(db.Text)
    property_type = db.Column(db.Text)
    publish_status = db.Column(db.Text)
    rating = db.Column(db.SmallInteger)
    terms_conditions = db.Column(db.Text)
    year_built = db.Column(db.Integer)
    create_date = db.Column(db.Date)
    modified_date = db.Column(db.Date)
    pets = db.Column(db.Text)
    target_move_date = db.Column(db.Date)

    rentals = db.relationship('Rental', backref='house', uselist=False)
    for_sale = db.relationship('ForSale', backref='house', uselist=False)
    appointments = db.relationship('Appointment', backref='house', lazy=True)


class ListingAvailability(db.Model):
    __tablename__ = 'listing_availability'

    pattern_id = db.Column(db.BINARY(16), primary_key=True)
    user_id = db.Column(db.BINARY(16), db.ForeignKey('agent.user_id'))
    house_id = db.Column(db.BINARY(16), db.ForeignKey('houses.house_id'))
    day_of_the_week = db.Column(db.Integer)  # 0-Sunday, 1-Monday, etc.
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)


class Appointment(db.Model):
    __tablename__ = 'appointments'

    appt_id = db.Column(db.BINARY(16), primary_key=True)
    house_id = db.Column(db.BINARY(16), db.ForeignKey('houses.house_id'))
    user_id = db.Column(db.BINARY(16), db.ForeignKey('users.user_id'))
    date = db.Column(db.Date)
    day_of_the_week = db.Column(db.Integer)  # 0-Sunday, 1-Monday, etc.
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    name = db.Column(db.Text)
    description = db.Column(db.Text)


class Saved(db.Model):
    __tablename__ = 'saved'

    user_id = db.Column(db.BINARY(16), db.ForeignKey('users.user_id'), primary_key=True)
    house_id = db.Column(db.BINARY(16), db.ForeignKey('houses.house_id'), primary_key=True)
    name = db.Column(db.String(255), primary_key=True)
    date_created = db.Column(db.Date)
    date_modified = db.Column(db.Date)
    notes = db.Column(db.Text)
    tag = db.Column(db.Text)


class Client(db.Model):
    __tablename__ = 'client'

    user_id = db.Column(db.BINARY(16), db.ForeignKey('users.user_id'), primary_key=True)


class ForSale(db.Model):
    __tablename__ = 'for_sale'

    house_id = db.Column(db.BINARY(16), db.ForeignKey('houses.house_id'), primary_key=True)
    price = db.Column(db.Integer)


class Rental(db.Model):
    __tablename__ = 'rentals'

    house_id = db.Column(db.BINARY(16), db.ForeignKey('houses.house_id'), primary_key=True)
    available_start = db.Column(db.Date)
    available_end = db.Column(db.Date)
    monthly_price = db.Column(db.Integer)