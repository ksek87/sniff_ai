from flask import Blueprint, request, jsonify   
from services.generate_fragrance import generate_fragrance_from_description

api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/generate_fragrance', methods=['POST'])
def generate_fragrance():
    data = request.json
    description = data.get('description')
    
    if not description:
        return jsonify({'error': 'Description is required'}), 400
    
    generated_fragrance = generate_fragrance_from_description(description)
    
    return jsonify({'fragrance': generated_fragrance})