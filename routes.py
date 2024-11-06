from flask import Blueprint, jsonify, request
from models import db, User, House, Rental, ForSale
import uuid

bp = Blueprint('app', __name__)

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
    house_id = uuid.uuid4().bytes  # Generate a binary UUID
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


@bp.route('/houses/search', methods=['GET'])
def search_houses():
    # Get query parameters from the request
    house_type = request.args.get('type')  # Can be 'rentals' or 'for_sale'
    property_type = request.args.get('property_type')  # Property type filter
    city = request.args.get('city')  # City filter
    price_min = request.args.get('price_min', type=int)  # Minimum price
    price_max = request.args.get('price_max', type=int)  # Maximum price

    # Validate house_type input
    if house_type not in ['rentals', 'for_sale']:
        return jsonify({
            'success': False,
            'message': 'Invalid house type. Choose either "rentals" or "for_sale".'}), 400

    # Initialize query
    query = House.query

    # Apply filters based on the type of house
    if house_type == 'rentals':
        query = query.join(Rental)
        # Apply filters if provided
        if price_min is not None:
            query = query.filter(Rental.monthly_price >= price_min)
        if price_max is not None:
            query = query.filter(Rental.monthly_price <= price_max)

    elif house_type == 'for_sale':
        query = query.join(ForSale)
        # Apply filters if provided
        if price_min is not None:
            query = query.filter(ForSale.price >= price_min)
        if price_max is not None:
            query = query.filter(ForSale.price <= price_max)

    # Check and apply additional filters if provided
    if property_type:
        query = query.filter(House.property_type == property_type)

    if city:
        query = query.filter(House.city == city)

    # Execute the query and fetch results
    houses = query.all()

    # Check if houses are found
    if not houses:
        return jsonify({
            'success': True,
            'message': 'No houses found matching the criteria.',
            'data': []}), 200

    # Return a list of houses
    return jsonify({
        'success': True,
        'message': "Found houses matching the criteria",
        'data': [{
            'house_id': str(uuid.UUID(bytes=house.house_id)),
            'street': house.street,
            'city': house.city,
            'property_type': house.property_type,
            'price': (house.rentals.monthly_price if house_type=='rentals' else house.for_sale.price),
            'image': house.photos
        } for house in houses]
    }), 200

# URL should be of the type:
# /houses/search?type=[rentals/for_sale]&property_type=[type_of_home]&city=[city_name]&price_min=[min]&price_max=[max]
# city should be space separated by %20 (i.e. Los Angeles --> Los%20Angeles
# always assuming that we are searching for either a rental or a for sale property (i.e. must be specified)
# price min and max should be integers. Refers to monthly rent for rentals and buying price for sale
# property type specifies town house, mansion, etc...
