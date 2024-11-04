from flask import Blueprint, jsonify, request
from models import db, User, House, Rental, ForSale
import uuid

bp = Blueprint('app', __name__)

@bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{'user_id': uuid.UUID(bytes=user.user_id), 'email': user.email} for user in users])

@bp.route('/houses', methods=['GET'])
def get_houses():
    houses = House.query.all()
    return jsonify([{'house_id': uuid.UUID(bytes=house.house_id), 'street': house.street} for house in houses])


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
        return jsonify({'message': 'Invalid house type. Choose either "rentals" or "for_sale".'}), 400

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
        return jsonify({'message': 'No houses found matching the criteria.'}), 404

    # Return a list of houses
    return jsonify([{
        'house_id': str(uuid.UUID(bytes=house.house_id)),
        'street': house.street,
        'city': house.city,
        'property_type': house.property_type,
        # Add other fields as needed
    } for house in houses]), 200

# URL should be of the type:
# /houses/search?type=[rentals/for_sale]&property_type=[type_of_home]&city=[city_name]&price_min=[min]&price_max=[max]
# city should be space separated by %20 (i.e. Los Angeles --> Los%20Angeles
# always assuming that we are searching for either a rental or a for sale property (i.e. must be specified)
# price min and max should be integers. Refers to monthly rent for rentals and buying price for sale
# property type specifies town house
