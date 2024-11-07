from flask import Flask, request, jsonify
from api.routes import api_blueprint
from model.main import process_description

"""
file: backend/main.py
"""
app = Flask(__name__)
app.register_blueprint(api_blueprint)

@app.route('/generate_fragrance', methods=['POST'])
def generate_fragrance():
    """ Generate a fragrance based on a description """
    data = request.json
    description = data.get('description')
    if not description:
        return jsonify({'error': 'Description is required'}), 400
    # Process the description with the AI model
    generated_fragrance = process_description(description)
    # generated_fragrance = ai_model.process(description)
    return jsonify({'fragrance': generated_fragrance})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
    