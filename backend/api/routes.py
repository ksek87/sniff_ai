from flask import Blueprint, request, jsonify   
from services.generate_fragrance import generate_fragrance_from_description
    
""" API routes for the application """

api_blueprint = Blueprint('api', __name__)

@api_blueprint.route('/generate_fragrance', methods=['POST'])
def generate_fragrance():
    """ Generate a fragrance based on a description """
    data = request.json
    description = data.get('description')
    
    if not description:
        return jsonify({'error': 'Description is required'}), 400
    
    generated_fragrance = generate_fragrance_from_description(description)
    
    return jsonify({'fragrance': generated_fragrance})
