from flask import Flask, request, jsonify, render_template, redirect
import pickle
import re
import string
import pandas as pd
import logging 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


try:
    model = pickle.load(open('PhishingProtector.pkl', 'rb'))
    vector = pickle.load(open('vector.pkl', 'rb'))
    logging.info("PhishingProtector.pkl and vector.pkl loaded successfully.")
except FileNotFoundError:
    logging.error("Error: Model or vector file not found. Ensure 'PhishingProtector.pkl' and 'vector.pkl' are in the same directory as app.py.")
    # Exit or raise an exception to prevent the app from starting without models
    exit("Required model files are missing.")
except Exception as e:
    logging.error(f"An unexpected error occurred while loading models: {e}")
    exit("Failed to load models due to an unexpected error.")


app = Flask(__name__)

# --- URL Preprocessing Function ---
def preprocess_url(url):
    """
    Preprocesses a given URL by converting to lowercase, removing protocols,
    special characters, duplicate slashes, and trailing slhes, then tokenizing.
    """
    url = str(url).lower()
    url = re.sub(r'^https?:\/\/', '', url) # Remove http/https protocol
    url = re.sub(r'[^\w\s\-\/]', '', url)  # Keep alphanumeric, space, hyphen, slash
    url = re.sub(r'\/+', '/', url)         # Replace multiple slashes with single
    url = url.rstrip('/')                  # Remove trailing slash
    url = url.split('/')                   # Tokenize by splitting on slash
    return url

# --- Routes ---

@app.route('/')
def home():
    """Renders the home page (index.html)."""
    return render_template('index.html')

@app.route('/check', methods=['GET', 'POST'])
def check():
    """
    Handles the URL checking logic.
    - On POST: Preprocesses the submitted URL, uses the loaded model for prediction,
      and returns either Malicious.html or Safe.html based on the result.
    - On GET: Renders the home page.
    """
    if request.method == 'POST':
        link = request.form.get('link') # Use .get() to avoid KeyError if 'link' is missing

        if not link:
            logging.warning("Empty link submitted.")
            return render_template('index.html', error="Please enter a URL to check.")

        logging.info(f"Received link for checking: {link}")

        testing_link_df = pd.DataFrame({"text": [link]})

        # Apply preprocessing
        testing_link_df['text'] = testing_link_df['text'].apply(preprocess_url)
        logging.debug(f"Preprocessed URL tokens: {testing_link_df['text'].iloc[0]}")

        # Join tokens back into a string for vectorizer
        testing_link_df['text'] = testing_link_df['text'].apply(lambda x: ' '.join(x))

        try:
            # Transform the preprocessed URL using the loaded vectorizer
            df_new_transformed = vector.transform(testing_link_df['text'])
            logging.debug(f"Vectorized data shape: {df_new_transformed.shape}")

            # Make prediction using the loaded model
            prediction_result = model.predict(df_new_transformed)
            logging.info(f"Prediction result for '{link}': {prediction_result[0]}")

            if prediction_result[0] == 1: # Assuming 1 means malicious based on previous discussion
                return render_template('Malicious.html')
            else: 
                return render_template('Safe.html', original_link=link)

        except Exception as e:
            logging.error(f"An error occurred during URL processing or prediction: {e}")
            return render_template('index.html', error="An internal error occurred while checking the URL. Please try again.")

   
    return redirect('/') 


if __name__ == '__main__':
   
    logging.warning("Running in debug mode. This should not be used in production.")
    app.run(debug=True)
