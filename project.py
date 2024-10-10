# app.py

import os
from flask import Flask, request, jsonify
import pandas as pd
import requests
import time
API_KEY = os.getenv('API_KEY', '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')




# Initialize the Flask application
app = Flask(__name__)

# Load the GPT-2 model from Hugging Face
# generator = pipeline('text-generation', model='gpt2')

# Global variable to hold sales data
sales_data = ""

# Endpoint to upload sales data
@app.route('/upload_data', methods=['POST'])
def upload_data():
    global sales_data  # Using the global variable to hold the sales data
    file = request.files.get('file')  # Get the uploaded file from the request

    if not file:
        return jsonify({'error': 'No file provided.'}), 400

    try:
        # Check the file type and read the data accordingly
        if file.filename.endswith('.csv'):
            sales_data = pd.read_csv(file)  # Load CSV data into a DataFrame
            # print(sales_data.head())  # Print the first few rows for debugging
            return jsonify({'message': 'CSV data uploaded successfully.'}), 200
        elif file.filename.endswith('.json'):
            sales_data = pd.read_json(file)  # Load JSON data into a DataFrame
            print(sales_data.head())  # Print the first few rows for debugging
            return jsonify({'message': 'JSON data uploaded successfully.'}), 200
        else:
            return jsonify({'error': 'Unsupported file format. Please upload a CSV or JSON file.'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Handle any errors that occur during file reading


# Function to analyze sales data using GPT-2
def analyze_sales_data(prompt):
    max_input_length = 500  # Adjust as necessary

    # Truncate the prompt if it exceeds the max length
    if len(prompt) > max_input_length:
        prompt = prompt[:max_input_length] + "..."

    api_url = "https://api-inference.huggingface.co/models/gpt2"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {"inputs": prompt}

    for _ in range(3):  # Try up to 3 times
        response = requests.post(api_url, headers=headers, json=data)
        
        # Check if the response is successful
        if response.status_code == 200:
            return response.json()[0]['generated_text']
        elif response.status_code == 503:
            print("Model is loading, retrying...")
            time.sleep(5)  # Wait for 5 seconds before retrying
        else:
            # Handle other potential errors
            return response.json()
    
    return {"error": "Failed to get a response from the model after multiple attempts."}
   


# Endpoint to query performance feedback for a specific sales representative
@app.route('/sales/representative', methods=['POST'])
def sales_representative_performance():
    if sales_data is None:
        return jsonify({'error': 'No sales data available. Please upload data first.'}), 400

    # Parse the incoming request JSON
    data = request.get_json()
    print("Sales rep request data: ", data)
    
    # Extract the sales representative's name from the request
    sales_rep = data.get('sales_rep')
    print("Sales Representative: ", sales_rep)

    # If the sales representative name is missing, return an error
    if not sales_rep:
        return jsonify({'error': 'Please provide "sales_rep" in the request body.'}), 400
    
    # Filter the data for the specific sales representative
    rep_data = sales_data[sales_data['employee_name'] == sales_rep]
    
    # If no data is found, return an error
    if rep_data.empty:
        return jsonify({'error': f'No data found for sales representative "{sales_rep}".'}), 404
    
    # Convert the filtered data into a CSV string
    rep_data_str = rep_data.to_csv(index=False)

    # Create the prompt for the LLM to analyze the sales representative's performance
    prompt = f"""Analyze the following sales data for the sales representative named '{sales_rep}'. 
    Provide performance feedback, including key performance metrics such as:
    - Leads taken
    - Tours booked
    - Applications submitted
    - Revenue confirmed and pending
    Here is the data:\n\n{rep_data_str}"""

    # Call the function to analyze the data with the LLM
    feedback = analyze_sales_data(prompt)
   
    # Return the feedback as a JSON response
    return jsonify({'feedback': feedback}), 200
# Endpoint to assess overall team performance 
@app.route('/sales/team', methods=['GET'])
def team_performance():
    if sales_data is None:
        return jsonify({'error': 'No sales data available. Please upload data first.'}), 400
    # Convert the entire data to a string for the LLM
    data_str = sales_data.to_csv(index=False)
    prompt = f"Analyze the following sales data for the entire sales team and provide performance feedback:\n\n{data_str}"
    print("slaes data." ,data_str)
    feedback = analyze_sales_data(prompt)
    return jsonify({'feedback': feedback}), 200

# Endpoint for sales performance trends and forecasting
@app.route('/sales/trends', methods=['GET'])
def sales_trends():
    if sales_data is None:
        return jsonify({'error': 'No sales data available. Please upload data first.'}), 400
    # Convert the data to a string for the LLM
    data_str = sales_data.to_csv(index=False)
    prompt = f"Analyze the sales performance data for all. Provide detailed feedback including key performance indicators such as total tours booked, applications submitted, revenue confirmed, and any trends or insights from the data. Here is the data:\n\n{data_str}"
    forecast = analyze_sales_data(prompt)
    return jsonify({'forecast': forecast}), 200

if __name__ == '__main__':  
    app.run(debug=True)
