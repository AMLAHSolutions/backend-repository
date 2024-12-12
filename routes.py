from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from models import *
import uuid

bp = Blueprint('app', __name__)

"""
GET:
    /users/agents: returns all agents
    /users/clients: returns all clients
    /users/id?user_id=<id>: returns user specified by user_id
    /houses/id?house_id=<id>: returns information on the house based on the passed id
    /houses/search?: returns houses based on the passed parameters:
        /houses/search?type=[rentals/for_sale]&property_type=[type_of_home]&city=[city_name]&price_min=[min]&price_max=[max]
    /users/saved?user_id=<id>: returns all saved houses by the specified user
    /houses/availability?house_id=<id>: returns availability information about the given house
        Each house has 7 entries in the availability table, one for each day of the week. A GET should return all availability for that house
POST:
    /houses: create a house based on the passed JSON object
        must specify "type" which can be "rentals" or "for_sale" in the passed JSON
    /users: create a user based on the passed JSON object
        must specify "user_type" which can be "client" or "agent" in the passed JSON
    /users/saved: create a saved house based on passed JSON object
        must at least specify a user_id, house_id, and name but more fields present in models.py
    /houses/availability?house_id=<id>
DELETE:
    /houses?house_id=<id>: deletes the house based on passed query parameter
    /user?user_id=<id>: deletes the user based on passed query parameter
    /users/saved?user_id=<id>&house_id=<id>: deletes the house_id from the user's saved collection
"""

# Q For Brian:

"""
Formats: ALL DATES (YYYY-MM-DD). ALL TIMES (HH:MM:SS)

Appointments (/houses/appointment):
    - GET: Takes 1 of 2 query parameters. Pass in 'user_id' to retrieve all appointments for a given user. 
           Pass in 'house_id' to retrieve appointments associated with the given house. Returns all info
           about all appointments.
    - POST: Create an appointment through passed JSON object. Must specify 'user_id', 'house_id', 'date', and 
            'start_time'. Can also optionally pass 'name' and 'description'. 'end_time' will automatically
            be set to 15 minutes after 'start_time'. Will allow creation of appointments outside of available
            hours (i.e. assumes well formed requests)
    - DELETE: Takes in a single query parameter, 'appt_id'. Deletes the appointment associated with the appt_id.
    
Availability (/houses/availability):
    - GET: Takes in 3 query parameters: 'house_id', 'date', 'days'. Returns the availability for the given
           house for the next 'days' days, starting from 'date'. Returns availability in 15 minute increments.
           Cross references appointments table and will indicate whether every available block is free or booked.
    - POST: Takes in JSON object. Required fields are 'is_recurring', 'house_id', 'start_time', and 'end_time'. 
            Allows users to either create recurring or one-time availabilities for the given house. If recurring, 
            the additional fields of 'day_of_the_week' (0-Monday, 1-Tuesday, etc...) are needed. If not, 'available_date'
            is required (YYYY-MM-DD). Will delete any existing appointments which do not fit in the new availability and
            return the user_id's of the affected clients. Returns a list of all user_id's of user's whose appointments
            were canceled. 
    - DELETE: Takes in 'house_id' and 'date' as query parameters. Deletes a non-recurring availability for the given house.
              Upon deletion, will delete any appointments that do not fit in the recurring availability for that day of the week.
              Does not support deletion of recurring availabilities. To "delete" recurring availabilities, set start time and
              end time to the same value. Returns a list of all user_id's of user's whose appointments were canceled. 
              
Saved (/users/saved):
    - GET: Takes in 1 query parameter: 'user_id'. Fetches all saved houses for that user.
    - POST: Takes in JSON object. Required fields are 'user_id', 'house_id', and 'name'. Optional fields include 'notes' and 
            'tag'. Adds the specified house to the user's saved collection under the name 'name'. 
    - DELETE: Takes in 2 query parameters: 'user_id' and 'house_id'. Deletes the specified house from the specified 
              user's saved collection.
              
Houses (/houses)
    - GET: Takes in 1 query parameter: 'house_id'. Retrieves all information about the specified house.
    - POST: Takes in a JSON object. Required fields are 'type' (either "rental" or "for_sale"), 'street', 'city', 'user_id',
            'zipcode', 'country', 'description', 'HOA', and 'name'. Will create a new house with the specified attributes.
            Returns the house_id of the newly created house.
"""

# TO DO: What to do when someone wants to delete/change availability of a house that has appointments scheduled?
# TO DO: On a similar note, we need to think about what interactions change with appointment and availability. For example, when a listing is removed, we should get rid of all appointments and all listings. Same when deleting a user.
# TO DO: Switch over data model to prevent deletion. Add a field for "status" which lets us know about active, sold, rented properties

# currently allows for appointments to be made on times that aren't available for the listing
@bp.route('/houses/appointment', methods=['GET', 'POST', 'DELETE'])
def house_appointment():
    # fetches appointments for either a given house/user. Users can specify a house_id or a user_id
    if request.method == 'GET':
        user_id_str = request.args.get('user_id')
        house_id_str = request.args.get('house_id')

        # validate house_id/user_id and convert from string to bytes
        if user_id_str:
            try:
                id = uuid.UUID(user_id_str).bytes
                appointments = Appointment.query.filter_by(user_id=id).all()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid user_id format.',
                    'data': None
                }), 400
        elif house_id_str:
            try:
                id = uuid.UUID(house_id_str).bytes
                appointments = Appointment.query.filter_by(house_id=id).all()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid house_id format.',
                    'data': None
                }), 400
        else:
            # return error if user_id or house_id not specified
            return jsonify({
                'success': False,
                'message': 'Please specify a house_id or a user_id.'
            }), 400

        # go trough all appointments and append them to a list
        appointment_data = []
        for appointment in appointments:
            appointment_data.append({
                'appt_id': str(uuid.UUID(bytes=appointment.appt_id)),
                'house_id': str(uuid.UUID(bytes=appointment.house_id)),
                'user_id': str(uuid.UUID(bytes=appointment.user_id)),
                'date': appointment.date.isoformat(),
                'start_time': appointment.start_time.strftime("%H:%M:%S"),
                'end_time': appointment.end_time.strftime("%H:%M:%S"),
                'description': appointment.description,
                'name': appointment.name
            })

        return jsonify({
            'success': True,
            'message': 'Successfully returned appointment data',
            'data': appointment_data
        }), 200

    # based on the SQL schema this assumes that name < 255 chars and description < 65k chars
    elif request.method == 'POST':
        data = request.get_json()

        # ensure required fields are provided
        if not all(key in data for key in ['user_id', 'house_id', 'date', 'start_time']):
            return jsonify({
                'success': False,
                'message': 'Missing required fields.',
                'data': None
            }), 400

        try:
            user_id = uuid.UUID(data['user_id']).bytes
            house_id = uuid.UUID(data['house_id']).bytes
            appointment_date = datetime.fromisoformat(data['date'])  # Ensure date is valid
            start_time = datetime.strptime(data['start_time'], "%H:%M:%S")  # Format to match input
            name = data.get('name')
            description = data.get('description')
            end_time = start_time + timedelta(minutes=15)

        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid input format.',
            }), 400

        if name and len(name) >= 255:
            return jsonify({
                'success': False,
                'message': 'Name too long.',
            }), 400

        overlaps = Appointment.query.filter(Appointment.start_time < end_time, start_time < Appointment.end_time).first()

        if overlaps:
            return jsonify({
                'success': False,
                'message': 'Overlaps with existing appointment.',
            }), 403

        # create a new appointment instance
        appointment_id = uuid.uuid4().bytes
        new_appointment = Appointment(
            appt_id=appointment_id,
            user_id=user_id,
            house_id=house_id,
            date=appointment_date,
            start_time=start_time.time(),
            end_time=end_time.time(),
            description=description,
            name=name
        )

        # attempt to add new appointment
        try:
            db.session.add(new_appointment)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to create appointment.',
                'data': str(e)
            }), 500

        return jsonify({
            'success': True,
            'message': 'Appointment created successfully!'
        }), 201

    elif request.method == 'DELETE':
        appt_id_str = request.args.get('appt_id')

        try:
            appt_id = uuid.UUID(appt_id_str).bytes

            # Find and delete the appointment
            appointment = Appointment.query.filter_by(appt_id=appt_id).first()

            if not appointment:
                return jsonify({
                    'success': False,
                    'message': 'Appointment not found.',
                    'data': None
                }), 404

            db.session.delete(appointment)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Appointment deleted successfully!'
            }), 200

        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid input format.',
            }), 400



# gets the availability for the next 'days' days. User can specify the number of days to retrieve
@bp.route('/houses/availability', methods=['GET', 'POST', 'DELETE'])
def house_availability():
    if request.method == "GET":
        house_id_str = request.args.get('house_id')
        date_str = request.args.get('date')
        num_days = request.args.get('days')

        if not date_str or not num_days or not house_id_str:
            return jsonify({
                'success': False,
                'message': "Missing required fields"
            }), 400

        try:
            num_days = int(num_days)
        except Exception as e:
            return jsonify({
                'success': False,
                'message': "num_days should be an integer."
            }), 400

        if num_days <= 0:
            return jsonify({
                'success': False,
                'message': 'Please specify a positive number of days.'
            }), 400

        # Validate house_id format
        try:
            house_id = uuid.UUID(house_id_str).bytes
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid house_id format.',
                'data': None
            }), 400

        try:
            start_date = datetime.fromisoformat(date_str).date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD.',
                'data': None
            }), 400

        house_exists = House.query.filter_by(house_id=house_id).first()
        if not house_exists:
            return jsonify({
                'success': False,
                'message': 'House not found.'
            }), 404


        end_date = start_date + timedelta(days=num_days)

        availability_results = {}

        availability = ListingAvailability.query.filter_by(house_id=house_id)
        appointments = Appointment.query.filter_by(house_id=house_id).filter(Appointment.date >= start_date, Appointment.date < end_date)

        for x in range((end_date - start_date).days):
            # calculate the date using the start date and the number of
            cur_date = start_date + timedelta(days=x)
            apts_today = appointments.filter_by(date=cur_date).all()
            apts = []
            for apt in apts_today:
                apts.append(datetime.combine(cur_date, apt.start_time))
            time_blocks = []
            non_recurring = availability.filter_by(available_date=cur_date).first()
            if not non_recurring:

                # if the entry is recurring, calculate the day offset and then use that to find the target_date
                # we call datetime.weekday() here: "Return the day of the week as an integer, where Monday is 0 and Sunday is 6."
                av = availability.filter_by(day_of_the_week=cur_date.weekday()).first()

                start_time = datetime.combine(cur_date, av.start_time)
                end_time = datetime.combine(cur_date, av.end_time)
                while start_time < end_time:
                    time_blocks.append(start_time.strftime("%H:%M Booked" if start_time in apts else "%H:%M Free"))
                    start_time += timedelta(minutes=15)
                availability_results[cur_date.isoformat()] = time_blocks
            else:
                start_time = datetime.combine(cur_date, non_recurring.start_time)
                end_time = datetime.combine(cur_date, non_recurring.end_time)
                while start_time < end_time:
                    time_blocks.append(start_time.strftime("%H:%M Booked" if start_time in apts else "%H:%M Free"))
                    start_time += timedelta(minutes=15)
                availability_results[cur_date.isoformat()] = time_blocks

        # Return the ordered JSON response
        return jsonify({
            'success': True,
            'data': availability_results
        }), 200
    elif request.method == "POST":
        data = request.json

        # Required fields
        house_id_str = data.get('house_id')
        is_recurring = data.get('is_recurring')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if is_recurring is None or not house_id_str or not start_time or not end_time:
            return jsonify({
                'success': False,
                'message': "Missing required fields: is_recurring, house_id, start_time, end_time"
            }), 400

        # Validate house_id format
        try:
            house_id = uuid.UUID(house_id_str).bytes
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid house_id format.',
                'data': None
            }), 400

        # Check if it's recurring or standalone
        if is_recurring:
            # Required for a recurring entry
            day_of_the_week = data.get('day_of_the_week')  # Should be an integer (0-Monday, 1-Tuesday, etc...)

            if not day_of_the_week:
                return jsonify({
                    'success': False,
                    'message': "Missing required fields: day_of_the_week"
                }), 400

            # Find existing recurring availability
            availability = ListingAvailability.query.filter_by(house_id=house_id, is_recurring=True,
                                                               day_of_the_week=day_of_the_week).first()

            if availability:
                # Update existing availability
                availability.start_time = start_time
                availability.end_time = end_time
                deleted_appointment_users = []
                canceled_appointments = Appointment.query.filter_by(house_id=house_id).filter((Appointment.start_time < start_time) |
                                                                                          (Appointment.end_time > end_time)).all()
                for appt in canceled_appointments:
                    deleted_appointment_users.append(str(uuid.UUID(bytes=appt.user_id)))
                    # db.session.delete(appt)
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'Recurring availability updated successfully.',
                    'data': deleted_appointment_users
                }), 200
            else:
                # create new recurring availability
                pattern_id = uuid.uuid4().bytes
                new_availability = ListingAvailability(
                    pattern_id=pattern_id,
                    house_id=house_id,
                    day_of_the_week=day_of_the_week,
                    start_time=start_time,
                    end_time=end_time,
                    is_recurring=True
                )
                db.session.add(new_availability)
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'Recurring availability added successfully.',
                    'data': None
                }), 201

        else:
            # non-recurring availability requires available_date
            available_date_str = data.get('available_date')

            if not available_date_str:
                return jsonify({
                    'success': False,
                    'message': "Missing required fields: available_date_str"
                }), 400

            # Check for existing non-recurring availability
            availability = ListingAvailability.query.filter_by(house_id=house_id,
                                                               available_date=available_date_str,
                                                               is_recurring=False).first()
            deleted_appointment_users = []
            canceled_appointments = Appointment.query.filter_by(house_id=house_id).filter((Appointment.start_time < start_time) |
                                                                                          (Appointment.end_time > end_time)).all()
            for appt in canceled_appointments:
                deleted_appointment_users.append(str(uuid.UUID(bytes=appt.user_id)))
                db.session.delete(appt)

            if availability:
                # Update existing non-recurring availability
                availability.start_time = start_time
                availability.end_time = end_time
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'Non-recurring availability updated successfully.',
                    'data': deleted_appointment_users
                }), 200
            else:
                # Create new non-recurring availability
                pattern_id = uuid.uuid4().bytes
                new_availability = ListingAvailability(
                    pattern_id=pattern_id,
                    house_id=house_id,
                    available_date=available_date_str,
                    start_time=start_time,
                    end_time=end_time,
                    is_recurring=False
                )
                db.session.add(new_availability)
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'Non-recurring availability added successfully.',
                    'data': deleted_appointment_users
                }), 201
    # deletes non recurring listing availability
    elif request.method == 'DELETE':
        house_id_str = request.args.get('house_id')
        date_str = request.args.get('date')

        try:
            house_id = uuid.UUID(house_id_str).bytes
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid house_id format.',
                'data': None
            }), 400

        try:
            date = datetime.fromisoformat(date_str).date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD.',
                'data': None
            }), 400

        dotw = date.weekday()
        # Check if the listing availability exists
        listing = ListingAvailability.query.filter_by(house_id=house_id, available_date=date, is_recurring=False).first()
        if not listing:
            return jsonify({
                'success': False,
                'message': 'No availability found for that date.',
                'data': None
            }), 404
        recurring_availability = ListingAvailability.query.filter_by(house_id=house_id, day_of_the_week=dotw).first()
        start_time = recurring_availability.start_time
        end_time = recurring_availability.end_time

        try:
            db.session.delete(listing)
            deleted_appointment_users = []
            canceled_appointments = Appointment.query.filter_by(house_id=house_id).filter((Appointment.start_time < start_time) |
                                                                                          (Appointment.end_time > end_time)).all()
            for appt in canceled_appointments:
                print(appt.start_time)
                deleted_appointment_users.append(str(uuid.UUID(bytes=appt.user_id)))
                db.session.delete(appt)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Failed to delete availability: {str(e)}',
                'data': None
            }), 500
        return jsonify({
            'success': True,
            'message': 'Availability deleted successfully!',
            'data': deleted_appointment_users
        }), 200





@bp.route('/users/saved', methods=['GET', 'POST', 'DELETE'])
def saved_houses():
    if request.method == 'GET':
        user_id_str = request.args.get('user_id')
        try:
            user_id = uuid.UUID(user_id_str).bytes
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid user_id format.',
                'data': None}), 400
        saved = Saved.query.filter_by(user_id=user_id).all()
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

    elif request.method == 'POST':
        data = request.get_json()

        # ensure that the following attributes are included:
        if ('user_id' not in data or 'house_id' not in data or 'name' not in data):
            return jsonify({
                'success': False,
                'message': 'Missing required fields.',
                'data': None
            }), 400

        try:
            user_id = uuid.UUID(data['user_id']).bytes
            house_id = uuid.UUID(data['house_id']).bytes
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid user_id format.',
                'data': None}), 400

        if Saved.query.filter_by(user_id=user_id, house_id=house_id).first():
            return jsonify({
                'success': False,
                'message': 'House is already saved',
                'data': None
            }), 400

        new_saved = Saved(
            user_id=user_id,
            house_id=house_id,
            name=data['name'],
            date_created=datetime.now(),
            date_modified=datetime.now(),
            notes=data.get('notes'),
            tag=data.get('tag')
        )

        try:
            db.session.add(new_saved)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Unknown house_id or user_id.',
                'data': None
            }), 500

        return jsonify({
            'success': True,
            'message': 'House successfully saved!',
            'data': None
        }), 201


    elif request.method == 'DELETE':
        user_id_str = request.args.get('user_id')
        house_id_str = request.args.get('house_id')

        if not user_id_str or not house_id_str:
            return jsonify({
                'success': False,
                'message': 'user_id and house_id are required.',
                'data': None
            }), 400

        try:
            user_id = uuid.UUID(user_id_str).bytes
            house_id = uuid.UUID(house_id_str).bytes
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid user_id or house_id format.',
                'data': None
            }), 400

        # Check if the saved entry exists
        saved_entry = Saved.query.filter_by(user_id=user_id, house_id=house_id).first()
        if not saved_entry:
            return jsonify({
                'success': False,
                'message': 'No saved house entry found for this user and house.',
                'data': None
            }), 404

        try:
            db.session.delete(saved_entry)
            db.session.commit()
        except:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Failed to delete saved house entry.',
                'data': None
            }), 500
        return jsonify({
            'success': True,
            'message': 'Saved house entry deleted successfully!',
            'data': None
        }), 200


@bp.route('/houses', methods=['GET', 'POST', 'DELETE'])
def house_by_id():
    if request.method == 'GET':
        house_id_str = request.args.get('house_id')
        try:
            house_id = uuid.UUID(house_id_str).bytes
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid house_id format.',
                'data': None}), 400

        house = House.query.filter_by(house_id=house_id).first()

        if not house:
            return jsonify({
                'success': False,
                'message': 'House not found.',
                'data': None}), 404

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

    # must send a JSON Object when POSTing. Must include additional field "type" which is either "rentals" or "for_sale".
    # if adding a rental, make sure to include rental specific attributes like available_start and available_end
    # include a price field to represent either the monthly price or buying price. Returns a JSON object with success, message,
    # and data field. If success is True, data will contain the house_id of the newly added house
    elif request.method=='POST':
        data = request.get_json()

        # Ensure that the following attributes are included (not null):
        # type, street, city, user_id, zipcode, country, description, HOA, and name
        if (
                'type' not in data or 'street' not in data or 'city' not in data or 'user_id' not in data or 'zipcode' not in data
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

    elif request.method=='DELETE':
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
@bp.route('/users', methods=['GET', 'POST', 'DELETE'])
def user_by_id():
    if request.method == 'GET':
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

    elif request.method == 'POST':

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

    elif request.method == 'DELETE':
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
        temp = jsonify({
            'success': True,
            'message': 'No houses found matching the criteria.',
            'data': []}), 200
        print(temp)
        return temp

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
    temp = jsonify({
        'success': True,
        'message': "Found houses matching the criteria",
        'data': house_data_list
    }), 200
    print(temp)
    return temp