from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from sentence_transformers import SentenceTransformer, util
from huggingface_hub import InferenceClient  
import torch
import pandas as pd
from decode import find_top_n_similar, extract_price_from_query, filter_products_by_price
from Intent_Identification import intent_response
from encode_suggestions import suggest_similar_suggestions
from llm_model_2 import generate_response
import logging
import re
import json


logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)


app.secret_key = 'f8d52e0d9c55d7b26c9a8c34d5f4a50fdbc7d8519b5d9fda1f7a0bf43d89e3e6'


model = SentenceTransformer('fine_tuned_bert_model_unsupervised')


def load_suggestions(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            suggestions = [line.strip() for line in f if line.strip()]
        print(f"Loaded {len(suggestions)} suggestions.")
        return suggestions
    except FileNotFoundError:
        print(f"Error: '{file_path}' not found.")
        return []

suggestions = load_suggestions('suggestions_list.txt')

try:
    suggestion_embeddings = torch.load('suggestion_embeddings.pt', weights_only=True)
    print(f"Loaded 'suggestion_embeddings.pt' successfully.")
except FileNotFoundError:
    print("Error: 'suggestion_embeddings.pt' not found. Please run 'encode_suggestions.py' to generate it.")
    suggestion_embeddings = torch.empty(0)  

csv_file = 'embeddings.csv'


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/suggest', methods=['POST'])
def suggest():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        print(f"Received query: '{query}'")

        if not query:
            print("Empty query received.")
            return jsonify({'suggestions': []})

        if suggestion_embeddings.numel() == 0:
            print("No suggestion embeddings available.")
            return jsonify({'suggestions': []})

       
        default_limit = 5  
        similarity_threshold = 0.95  
        suggestions_result = suggest_similar_suggestions(query, suggestions, suggestion_embeddings, default_limit, similarity_threshold)

        return jsonify({'suggestions': suggestions_result})

    except Exception as e:
        print(f"An error occurred in /suggest endpoint: {e}")
        return jsonify({'suggestions': []})


@app.route('/retrieve', methods=['GET', 'POST'])
def retrieve():
    """
    Endpoint to retrieve and filter products based on user query and price range.

    - Supports both GET and POST methods.
    """
    try:
        # Handle GET request
        if request.method == 'GET':
            query = request.args.get("query", "")
            n_results = int(request.args.get("n_results", 5))
            csv_file = request.args.get("csv_file", "embeddings.csv")

        # Handle POST request
        elif request.method == 'POST':
            data = request.json
            query = data.get("query", "")
            n_results = data.get("n_results", 5)
            csv_file = data.get("csv_file", "embeddings.csv")

        # Validate input
        if not query or not csv_file:
            return jsonify({"error": "Invalid input. 'query' and 'csv_file' are required."}), 400

        # Retrieve the top N similar products
        top_results = find_top_n_similar(query, csv_file, n=n_results)

        if not top_results:
            return jsonify({"message": "No similar products found."}), 404

        # Prepare results JSON
        results_json = {
            "query": query,
            "top_results": [
                {"rank": i, "product": text, "similarity": round(score, 2)}
                for i, (text, score) in enumerate(top_results, start=1)
            ],
        }

        # Extract price range from query
        price_range = extract_price_from_query(query)

        # Filter products by price range if applicable
        if price_range:
            filtered_products = filter_products_by_price(results_json, price_range)
            results_json["top_results"] = filtered_products
        product_details = []
        for result in results_json["top_results"]:
            product = result["product"]
            details = {
                "title": re.search(r"Title:\s*([^|]+)", product).group(1).strip() if re.search(r"Title:\s*([^|]+)", product) else None,
                "brand": re.search(r"Brand:\s*([^|]+)", product).group(1).strip() if re.search(r"Brand:\s*([^|]+)", product) else None,
                "description": re.search(r"Description:\s*([^|]+)", product).group(1).strip() if re.search(r"Description:\s*([^|]+)", product) else None,
                "price": re.search(r"Price:\s*([\d.]+)", product).group(1).strip() if re.search(r"Price:\s*([\d.]+)", product) else None,
                "availability": re.search(r"Availability:\s*([^|]+)", product).group(1).strip() if re.search(r"Availability:\s*([^|]+)", product) else None,
    }
            product_details.append(details)

        return render_template('results.html', products=product_details)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chat", methods=['POST'])
def chat():
    try:
        # Parse the JSON request body
        request_data = request.get_json()
        print(request_data)
        print('----------------------------------------------------------------------------------------------------------------------------------------')

        # Ensure request_data is not None
        if request_data is None:
            return jsonify({"error": "Invalid request. No data received."}), 400
        # Parse the JSON request body
        #request_data = request.get_json()
        user_input = request_data.get("message", "").strip()
        print("User Input", user_input)
        print('----------------------------------------------------------------------------------------------------------------------------------------')
        chat_history = request_data.get("chat_history", [])
        print(len(chat_history))
        print('----------------------------------------------------------------------------------------------------------------------------------------')

        product_data = request_data.get("product_data", [])
        print("Product Data",product_data)
        #csv_file = request_data.get("csv_file", "")  # Assuming CSV file path is part of the request

        # Validate input
        if not user_input:
            return jsonify({"error": "Query (message) is required"}), 400
        if not product_data:
            return jsonify({"error": "Product data is required"}), 400

        # Handle the first query
        if len(chat_history) == 0:
            chatbot_response = generate_response(
                user_input=user_input,
                data=str(product_data).strip()
            )
            # Update chat history
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": chatbot_response})
            return jsonify({
                "response": chatbot_response,
                "chat_history": chat_history
            })

        else:
            # Determine intent for subsequent queries
            intent = intent_response(
                user_input=user_input,
                chat_history=chat_history,
                data=product_data
            )
            print("Product Data",product_data)
            print(intent)

            if intent.strip() == 'Follow Up':
                chatbot_response = generate_response(
                    user_input=user_input,
                    chat_history=chat_history,
                    data=str(product_data).strip()
                )
                # Update chat history
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": chatbot_response})
                return jsonify({
                    "response": chatbot_response,
                    "intent": intent,
                    "chat_history": chat_history
                })

            elif intent.strip() == 'New Query':
                csv_file = 'embeddings.csv'
                # Retrieve products from embeddings if it's a new query
                product_data = find_top_n_similar(
                    query=user_input,
                    csv_file=csv_file,
                    n=3
                )
                print("Unfiltered", product_data)
                # Extract price range and filter products
                results_json = {
                "query": user_input,
                "top_results": [
                    {"rank": i, "product": text, "similarity": round(score, 2)}
                    for i, (text, score) in enumerate(product_data, start=1)
                ],
            }


                print(type(results_json))
            # Convert to JSON string and print
                results_json_str = json.dumps(results_json, indent=4)

                product_data = json.loads(results_json_str)


                price_range = extract_price_from_query(user_input)
                print("Price range:", price_range)
                if len(price_range)!=0:
                    product_data = filter_products_by_price(product_data, price_range)
                print("product filtered", product_data)

                chatbot_response = generate_response(
                    user_input=user_input,
                    chat_history=chat_history,
                    data=str(product_data).strip()
                )
                # Update chat history
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": chatbot_response})
                return jsonify({
                    "response": chatbot_response,
                    "intent": intent,
                    "chat_history": chat_history
                })

            else:
                return jsonify({"error": "Unable to identify intent"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

            





if __name__ == '__main__':
    app.run(debug=True)
        

    