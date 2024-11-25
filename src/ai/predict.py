import sys
import numpy as np
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model
import mysql.connector
import pandas as pd
import os

# Force UTF-8 encoding for stdout
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Load Model (if not already cached)
model = None

def get_model():
    global model
    if model is None:
        model = load_model('src/ai/lottery_model.keras')
    return model

# Fetch data from the database
def get_database_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def fetch_data(limit=100):
    db_connection = get_database_connection()
    cursor = db_connection.cursor(dictionary=True)

    # Fetch the most recent lottery results (limit to the last X rows)
    query = f"""
        SELECT drawDate, jackpot, GROUP_CONCAT(number ORDER BY number) AS numbers
        FROM LotteryResult
        JOIN LotteryNumber ON LotteryResult.id = LotteryNumber.resultId
        GROUP BY drawDate
        ORDER BY drawDate DESC
        LIMIT {limit}; 
    """
    cursor.execute(query)
    results = cursor.fetchall()
    db_connection.close()

    return pd.DataFrame(results)

# Preprocess the data for prediction
def preprocess_data(data):
    data['drawDate'] = pd.to_datetime(data['drawDate'], errors='coerce').astype(np.int64)
    data['numbers'] = data['numbers'].apply(lambda x: x.split(','))
    numbers_matrix = np.array(data['numbers'].apply(lambda x: [int(i) for i in x]).tolist())

    number_columns = [f'num_{i+1}' for i in range(numbers_matrix.shape[1])]
    numbers_df = pd.DataFrame(numbers_matrix, columns=number_columns)

    data = pd.concat([data, numbers_df], axis=1)
    columns_to_drop = ["numbers", "createdAt", "id"]
    columns_to_drop = [col for col in columns_to_drop if col in data.columns]
    data = data.drop(columns=columns_to_drop)

    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data)
    X = data_scaled[:-1]
    return X

def process_predictions(prediction):
    # Convert predictions to integers (rounding them)
    predicted_numbers = np.round(prediction).astype(int)

    # Ensure numbers are within the valid range [1, 49]
    predicted_numbers = np.clip(predicted_numbers, 1, 49)

    # Ensure uniqueness by converting to a set and then back to a list (may result in fewer than 7 numbers)
    unique_predicted_numbers = list(set(predicted_numbers))

    # If there are not enough unique numbers (in case of collisions), add random numbers until there are 7
    while len(unique_predicted_numbers) < 7:
        new_number = np.random.randint(1, 50)
        if new_number not in unique_predicted_numbers:
            unique_predicted_numbers.append(new_number)

    # Ensure we have exactly 7 numbers
    unique_predicted_numbers = unique_predicted_numbers[:7]

    # If the first predicted number is '1', replace it with a random number from the range [1, 49]
    if unique_predicted_numbers[0] == 1:
        new_random_number = np.random.randint(2, 50)
        while new_random_number in unique_predicted_numbers:
            new_random_number = np.random.randint(2, 50)
        unique_predicted_numbers[0] = new_random_number

    # Sort the numbers (optional, depends on whether order matters)
    unique_predicted_numbers = np.sort(unique_predicted_numbers)

    return unique_predicted_numbers

def predict_next_draw():
    # Fetch data from the database (limit the number of recent rows)
    data = fetch_data(limit=100)

    if 'numbers' not in data.columns:
        print("Error: Missing 'numbers' column in the data")
        return []

    # Preprocess the data
    X = preprocess_data(data)

    # Predict the next draw
    model = get_model()
    prediction = model.predict(X[-1].reshape(1, -1))

    processed_prediction = process_predictions(prediction[0])
    print(f"Predicted Numbers: {processed_prediction}")
    return processed_prediction

if __name__ == "__main__":
    predict_next_draw()
