from flask import Flask
from config import Config
from models import db
from routes import bp
from flask_cors import CORS


app = Flask(__name__)
# enables CORS for every route – when we go to production and host the backend/frontend on a VM, we should update this to only allow access from a specific domain
CORS(app)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()  # Create tables if not exist

app.register_blueprint(bp)

if __name__ == '__main__':
    app.run(debug=True)
