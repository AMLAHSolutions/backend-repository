from flask import Blueprint, jsonify, request
from models import *
import uuid

bp = Blueprint('app', __name__)

"""
GET:
    /users/agents: returns all agents
    /users/clients: returns all clients
    /users: returns all users
    /users/id?user_id=<id>: returns user specified by user_id
    /houses: returns all houses
    /houses/id?house_id=<id>: returns information on the house based on the passed id
    /houses/search?: returns houses based on the passed parameters:
        /houses/search?type=[rentals/for_sale]&property_type=[type_of_home]&city=[city_name]&price_min=[min]&price_max=[max]
    /users/saved?user_id=<id>: returns all saved houses by the specified user
POST:
    /houses: create a house based on the passed JSON object
        must specify "type" which can be "rentals" or "for_sale" in the passed JSON
    /users: create a user based on the passed JSON object
        must specify "user_type" which can be "client" or "agent" in the passed JSON
DELETE:
    /houses?house_id=<id>: deletes the house based on passed query parameter
    /user?user_id=<id>: deletes the user based on passed query parameter
"""

# GET for users
# should be tied into authentication
# user authentication can be tied back to the user_id and that's how we can query
# when a user creates an account/user logs in, we'll have some session management keeping track
# need to be careful that the UUID is stored within the session

@bp.route('/users/saved', methods=['GET', 'POST', 'DELETE'])
def saved_houses():
    user_id_str = request.args.get('user_id')
    try:
        user_id = uuid.UUID(user_id_str).bytes
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid user_id format.',
            'data': None}), 400

    if request.method=='GET':

        saved = Saved.query.filter_by(user_id=user_id)
        saved_data = []
        for house in saved:
            saved_data.append({
                'house_id': str(uuid.UUID(bytes=house.house_id)),
                'name': house.name,
                'date_created': house.date_created,
                'date_modified': house.date_modified,
                'notes': house.notes,
                'tag': house.tag
            })
        return jsonify({
            'success': True,
            'message': "Returned houses",
            'data': saved_data
        }), 200

    @bp.route('/houses/id', methods=['GET'])
    def house_by_id():
        house_id_str = request.args.get('house_id')
        try:
            house_id = uuid.UUID(house_id_str).bytes
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid house_id format.',
                'data': None}), 400

        houses = House.query.filter_by(house_id=house_id)

        if not houses:
            return jsonify({
                'success': False,
                'message': 'House not found.',
                'data': None}), 404

        # Convert house_id to a string
        for house in houses:
            house_dict = house.__dict__.copy()
            house_dict.pop('_sa_instance_state', None)  # Remove SQLAlchemy-specific state
            house_dict['house_id'] = house_id_str
            house_dict['user_id'] = str(uuid.UUID(bytes=house_dict['user_id']))

            rental = Rental.query.filter_by(house_id=house_id).first()
            for_sale = ForSale.query.filter_by(house_id=house_id).first()

            if rental:
                house_dict['monthly_price'] = rental.monthly_price
                house_dict['available_start'] = rental.available_start
                house_dict['available_end'] = rental.available_end

            if for_sale:
                house_dict['price'] = for_sale.price

        return jsonify({
            'success': True,
            'message': 'House data found',
            'data': house_dict
        }), 200
    # if request.method=='POST':
    #
    # if request.method=='DELETE':

# retrieves all agents
@bp.route('/users/agents', methods=['GET'])
def get_agents():
    agents = Agent.query.all()
    agent_data = []
    for agent in agents:
        user_id = agent.user_id
        user = User.query.filter_by(user_id=user_id).first()
        agent_data.append({
            'user_id': str(uuid.UUID(bytes=user_id)),
            'email': user.email,
            'about_me': user.about_me,
            'address': user.address,
            'birthday': user.birthday,
            'country': user.country,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'gender': user.gender,
            'language': user.language,
            'logout_event': user.logout_event,
            'logout_date': user.logout_date,
            'phone': user.phone,
            'profile_picture': user.profile_picture,
            'rating': user.rating,
            'search_price_min': user.search_price_min,
            'search_price_max': user.search_price_max,
            'search_city': user.search_city,
            'property_type': user.property_type,
            'search_status': user.search_status,
            'search_text': user.search_text,
            'company_name': agent.company_name,
            'num_customers': agent.num_customers,
            'num_properties': agent.num_properties,
            'properties_rented': agent.properties_rented,
            "properties_sold": agent.properties_sold
        })
    return jsonify({
        'success': True,
        'data': agent_data
    }), 200

# retrieves all clients
@bp.route('/users/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    client_data = []
    for client in clients:
        user_id = client.user_id
        user = User.query.filter_by(user_id=user_id).first()
        client_data.append({
            'user_id': str(uuid.UUID(bytes=user_id)),
            'email': user.email,
            'about_me': user.about_me,
            'address': user.address,
            'birthday': user.birthday,
            'country': user.country,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'gender': user.gender,
            'language': user.language,
            'logout_event': user.logout_event,
            'logout_date': user.logout_date,
            'phone': user.phone,
            'profile_picture': user.profile_picture,
            'rating': user.rating,
            'search_price_min': user.search_price_min,
            'search_price_max': user.search_price_max,
            'search_city': user.search_city,
            'property_type': user.property_type,
            'search_status': user.search_status,
            'search_text': user.search_text
        })
    return jsonify({
        'success': True,
        'data': client_data
    }), 200




# retrieves all user information based on user_id. Additionally returns information from the client or agent tables.
# Assumes that users cannot be both agents and users but will function properly as of right now since the client table
# only contains user_id
# query with /users/id?=<id>
@bp.route('/users/id', methods=['GET'])
def user_by_id():
    user_id_str = request.args.get('user_id')
    if not user_id_str:
        return jsonify({
            'success': False,
            'message': 'user_id is required.',
            'data': None}), 400

    try:
        # Convert the string representation of the UUID back to binary
        user_id = uuid.UUID(user_id_str).bytes
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid user_id format.',
            'data': None}), 400

    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found.',
            'data': None}), 404

    user_data = {
        'user_id': str(uuid.UUID(bytes=user.user_id)),
        'email': user.email,
        'about_me': user.about_me,
        'address': user.address,
        'birthday': user.birthday,
        'country': user.country,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'gender': user.gender,
        'language': user.language,
        'logout_event': user.logout_event,
        'logout_date': user.logout_date,
        'phone': user.phone,
        'profile_picture': user.profile_picture,
        'rating': user.rating,
        'search_price_min': user.search_price_min,
        'search_price_max': user.search_price_max,
        'search_city': user.search_city,
        'property_type': user.property_type,
        'search_status': user.search_status,
        'search_text': user.search_text
    }


    # Check in the agents table
    agent = Agent.query.filter_by(user_id=user.user_id).first()
    if agent:
        agent_data = {
            'user_id': str(uuid.UUID(bytes=agent.user_id)),
            'company_name': agent.company_name,
            'num_customers': agent.num_customers,
            'num_properties': agent.num_properties,
            'properties_rented': agent.properties_rented,
            'properties_sold': agent.properties_sold,
        }
        return jsonify({
            'success': True,
            'message': 'Agent data found',
            'data': {
                'user': user_data,
                'agent': agent_data
            }
        }), 200


    # Check in the clients table
    client = Client.query.filter_by(user_id=user.user_id).first()
    if client:
        return jsonify({
            'success': True,
            'message': 'Client data found',
            'data': {
                'user': user_data,
            }
        }), 200

    # If user exists but no corresponding client or agent was found
    return jsonify({
        'success': False,
        'message': 'No associated client or agent found for this user.',
        'data': None
    }), 404



@bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify({
        'success': True,
        'message': "Returning all users UID and email",
        'data': [{'user_id': uuid.UUID(bytes=user.user_id), 'email': user.email} for user in users]}), 200

@bp.route('/houses', methods=['GET'])
def get_houses():
    houses = House.query.all()
    return jsonify({
        'success': True,
        'message': "Returning all houses (rentals and for sale)",
        'data': [{'house_id': uuid.UUID(bytes=house.house_id), 'street': house.street} for house in houses]}), 200

# query with /houses?house_id=<id>
@bp.route('/houses', methods=['DELETE'])
def delete_house():
    house_id_str = request.args.get('house_id')  # The ID as a string

    if not house_id_str:
        return jsonify({
            'success': False,
            'message': 'house_id is required.',
            'data': None}), 400

    try:
        # Convert the string representation of the UUID back to binary
        house_id = uuid.UUID(house_id_str).bytes
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid house_id format.',
            'data': None}), 400

    # Check if the house exists
    house = House.query.filter_by(house_id=house_id).first()
    if not house:
        return jsonify({
            'success': False,
            'message': 'House not found.',
            'data': None}), 404

    # Remove the corresponding entries in the rentals or for_sale table
    Rental.query.filter_by(house_id=house_id).delete(synchronize_session=False)
    ForSale.query.filter_by(house_id=house_id).delete(synchronize_session=False)

    # Finally, delete the house itself
    db.session.delete(house)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'House deleted successfully!',
        'data': None}), 200

# delete users based on query parameter user_id
@bp.route('/users', methods=['DELETE'])
def delete_user():
    user_id_str = request.args.get('user_id')  # The ID as a string

    if not user_id_str:
        return jsonify({
            'success': False,
            'message': 'user_id is required.',
            'data': None
        }), 400

    try:
        # Convert the string representation of the UUID back to binary
        user_id = uuid.UUID(user_id_str).bytes
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid user_id format.',
            'data': None
        }), 400

    # Check if the user exists
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found.',
            'data': None
        }), 404

    # Remove related entries in the agent or client table if exists
    # Delete from the agent table if the user is an agent
    agent = Agent.query.filter_by(user_id=user_id).first()
    if agent:
        db.session.delete(agent)

    # Delete from the client table if the user is a client
    client = Client.query.filter_by(user_id=user_id).first()
    if client:
        db.session.delete(client)

    # Finally, delete the user itself
    db.session.delete(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'User deleted successfully!',
        'data': None
    }), 200

# post for users. Pass in a json object with all relevant information. Must pass additional fields if creating an agent
@bp.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()

    # Ensure that the following attributes are included (not null):
    if ('email' not in data or 'first_name' not in data or 'last_name' not in data or
        'user_type' not in data):
        return jsonify({
            'success': False,
            'message': 'Missing required fields.',
            'data': None
        }), 400

    # Generate a unique user_id
    user_id = uuid.uuid4().bytes  # Generate a binary UUID

    # Check if the email is already taken
    if User.query.filter_by(email=data['email']).first():
        return jsonify({
            'success': False,
            'message': 'Email is already in use.',
            'data': None
        }), 400

    # Create a new User instance
    new_user = User(
        user_id=user_id,
        email=data['email'],
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        about_me=data.get('about_me'),
        address=data.get('address'),
        birthday=data.get('birthday'),
        country=data.get('country'),
        gender=data.get('gender'),
        language=data.get('language'),
        phone=data.get('phone'),
        profile_picture=data.get('profile_picture'),
        rating=data.get('rating'),
        search_price_min=data.get('search_price_min'),
        search_price_max=data.get('search_price_max'),
        search_city=data.get('search_city'),
        property_type=data.get('property_type'),
        search_status=data.get('search_status'),
        search_text=data.get('search_text')
    )

    # Add the new user to the database
    db.session.add(new_user)

    # If the user is an agent, create a corresponding Agent entry
    if data['user_type'].lower() == 'agent':
        new_agent = Agent(
            user_id=user_id,
            company_name=data.get('company_name'),  # Assuming this is coming in the request
            num_customers=data.get('num_customers', 0),  # Default to 0 if not provided
            num_properties=data.get('num_properties', 0),
            properties_rented=data.get('properties_rented', 0),
            properties_sold=data.get('properties_sold', 0)
        )
        db.session.add(new_agent)

    # If the user is a client, create a corresponding Client entry
    elif data['user_type'].lower() == 'client':
        new_client = Client(
            user_id=user_id
            # Add any additional client-specific fields if necessary
        )
        db.session.add(new_client)

    else:
        # If user_type is not recognized
        return jsonify({
            'success': False,
            'message': "Invalid user_type. Must be 'client' or 'agent'.",
            'data': None
        }), 400

    # Commit the session to save all changes
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'User added successfully!',
        'data': str(uuid.UUID(bytes=user_id))
    }), 201

# must send a JSON Object when querying. Must include additional field "type" which is either "rentals" or "for_sale".
# if adding a rental, make sure to include rental specific attributes like available_start and available_end
# include a price field to represent either the monthly price or buying price. Returns a JSON object with success, message,
# and data field. If success is True, data will contain the house_id of the newly added house
@bp.route('/houses', methods=['POST'])
def add_house():
    data = request.get_json()

    # Ensure that the following attributes are included (not null):
    # type, street, city, user_id, zipcode, country, description, HOA, and name
    if ('type' not in data or 'street' not in data or 'city' not in data or 'user_id' not in data or 'zipcode' not in data
            or 'country' not in data or 'description' not in data or 'HOA' not in data or 'name' not in data):
        return jsonify({
            'success': False,
            'message': 'Missing required fields or type.',
            'data': None}), 400

    # Generate a unique house_id
    house_id = uuid.uuid4().bytes
    try:
        user_id_binary = uuid.UUID(data['user_id']).bytes
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid user_id format.',
            'data': None}), 400


    # Check if user_id exists in users table
    if not User.query.filter_by(user_id=user_id_binary).first():
        return jsonify({
            'success': False,
            'message': 'Invalid user_id. User does not exist.',
            'data': None}), 400

    # Create a new House instance
    new_house = House(
        house_id=house_id,
        street=data.get('street'),
        floor=data.get('floor'),
        zipcode=data.get('zipcode'),
        unit_num=data.get('unit_num'),
        country=data.get('country'),
        state=data.get('state'),
        city=data.get('city'),
        user_id=user_id_binary,
        appliances=data.get('appliances'),
        bathrooms=data.get('bathrooms'),
        bathroom_details=data.get('bathroom_details'),
        bedrooms=data.get('bedrooms'),
        bedroom_details=data.get('bedroom_details'),
        community=data.get('community'),
        condition=data.get('condition'),
        cooling=data.get('cooling'),
        laundry=data.get('laundry'),
        description=data.get('description'),
        exterior_features=data.get('exterior_features'),
        garage=data.get('garage'),
        heating=data.get('heating'),
        HOA=data.get('HOA', 0),  # Default to 0 if not provided
        photos=data.get('photos'),
        living_room=data.get('living_room'),
        square_feet=data.get('square_feet'),
        material_info=data.get('material_info'),
        name=data.get('name'),
        num_views=data.get('num_views', 0),  # Default to 0 if not provided
        notable_dates=data.get('notable_dates'),
        amenities=data.get('amenities'),
        interior_features=data.get('interior_features'),
        property_info=data.get('property_info'),
        owner_email=data.get('owner_email'),
        owner_first=data.get('owner_first'),
        owner_last=data.get('owner_last'),
        owner_phone=data.get('owner_phone'),
        parking_spots=data.get('parking_spots', 0),  # Default to 0 if not provided
        pet_policy=data.get('pet_policy'),
        property_type=data.get('property_type'),
        publish_status=data.get('publish_status'),
        rating=data.get('rating', 0),  # Default to 0 if not provided
        terms_conditions=data.get('terms_conditions'),
        year_built=data.get('year_built'),
        create_date=data.get('create_date'),  # Handle date format
        modified_date=data.get('modified_date'),  # Handle date format
        pets=data.get('pets'),
        target_move_date=data.get('target_move_date')  # Handle date format
    )

    # Add house to the appropriate table based on the type
    if data['type'] == 'rentals':
        new_rental = Rental(
            house_id=house_id,
            available_start=data.get('available_start'),  # Optional field
            available_end=data.get('available_end'),  # Optional field
            monthly_price=data['price']  # Required field
        )
        db.session.add(new_rental)

    elif data['type'] == 'for_sale':
        new_sale = ForSale(
            house_id=house_id,
            price=data['price']  # Required field
        )
        db.session.add(new_sale)

    db.session.add(new_house)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'House added successfully!',
        'data': str(uuid.UUID(bytes=house_id))}), 201


# look into search APIs to use here for more complicated search queries
@bp.route('/houses/search', methods=['GET'])
def search_houses():
    # Get query parameters from the request
    house_type = request.args.get('type')  # Can be 'rentals' or 'for_sale'
    property_type = request.args.get('property_type')  # Property type filter
    city = request.args.get('city')  # City filter
    price_min = request.args.get('price_min', type=int)  # Minimum price
    price_max = request.args.get('price_max', type=int)  # Maximum price

    # Validate house_type input
    if house_type not in ['rental', 'for_sale']:
        return jsonify({
            'success': False,
            'message': "Invalid house type. Choose either 'rental' or 'for_sale'."}), 400

    query = House.query

    # Apply filters based on the type of house
    if house_type == 'rental':
        query = query.join(Rental)
        if price_min is not None:
            query = query.filter(Rental.monthly_price >= price_min)
        if price_max is not None:
            query = query.filter(Rental.monthly_price <= price_max)

    elif house_type == 'for_sale':
        query = query.join(ForSale)
        if price_min is not None:
            query = query.filter(ForSale.price >= price_min)
        if price_max is not None:
            query = query.filter(ForSale.price <= price_max)

    if property_type:
        query = query.filter(House.property_type == property_type)

    if city:
        query = query.filter(House.city == city)

    houses = query.all()

    # Check if houses are found
    if not houses:
        return jsonify({
            'success': True,
            'message': 'No houses found matching the criteria.',
            'data': []}), 200

    # Transform each house object into a dictionary and return the attributes
    house_data_list = []
    for house in houses:
        house_dict = house.__dict__.copy()
        house_dict.pop('_sa_instance_state', None)  # Remove SQLAlchemy-specific state

        # Convert house_id to a string
        house_dict['house_id'] = str(uuid.UUID(bytes=house_dict['house_id']))
        house_dict['user_id'] = str(uuid.UUID(bytes=house_dict['user_id']))

        # If the house is for rent, include rental attributes directly
        if house_type == 'rental':
            house_dict['monthly_price'] = house.rentals.monthly_price
            house_dict['available_start'] = house.rentals.available_start
            house_dict['available_end'] = house.rentals.available_end

        if house_type == 'for_sale':
            house_dict['price'] = house.for_sale.price

        house_data_list.append(house_dict)

    # Return the list of houses
    return jsonify({
        'success': True,
        'message': "Found houses matching the criteria",
        'data': house_data_list
    }), 200

# URL should be of the type:
# /houses/search?type=[rentals/for_sale]&property_type=[type_of_home]&city=[city_name]&price_min=[min]&price_max=[max]
# city should be space separated by %20 (i.e. Los Angeles --> Los%20Angeles
# always assuming that we are searching for either a rental or a for sale property (i.e. must be specified)
# price min and max should be integers. Refers to monthly rent for rentals and buying price for sale
# property type specifies town house, mansion, etc...
