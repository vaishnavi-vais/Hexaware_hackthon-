# Hexaware_hackthon-
#backend

from flask import Flask, request, jsonify
from transformers import pipeline

app = Flask(__name__)

# Load the question generation pipeline
question_generator = pipeline("text2text-generation", model="t5-small")

@app.route('/generate', methods=['POST'])
def generate_questions():
    content = request.json.get("content")
    if not content:
        return jsonify({"error": "No content provided"}), 400
    
    # Generate questions from the provided content
    questions = question_generator(f"generate question: {content}", max_length=50, num_return_sequences=5)
    
    # Extract the generated questions
    generated_questions = [q['generated_text'] for q in questions]
    
    return jsonify({"questions": generated_questions})

if __name__ == "__main__":
    app.run(debug=True)
