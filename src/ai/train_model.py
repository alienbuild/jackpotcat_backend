import numpy as np
import pandas as pd
import mysql.connector
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

# Fetch data from the database
def get_database_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# Fetch data from the database (Lottery Results and Numbers)
def fetch_data():
    db_connection = get_database_connection()
    cursor = db_connection.cursor(dictionary=True)

    query = """
        SELECT 
            LotteryResult.drawDate, 
            LotteryResult.jackpot,
            GROUP_CONCAT(LotteryNumber.number ORDER BY LotteryNumber.id) AS numbers
        FROM 
            LotteryResult
        JOIN 
            LotteryNumber ON LotteryResult.id = LotteryNumber.resultId
        GROUP BY 
            LotteryResult.id
        LIMIT 1000;
    """
    cursor.execute(query)
    results = cursor.fetchall()

    # Convert results to DataFrame
    data = pd.DataFrame(results)
    cursor.close()
    db_connection.close()

    return data

# Preprocess Data
def preprocess_data(data):
    # Convert 'drawDate' to Unix timestamp (seconds since epoch)
    data['drawDate'] = pd.to_datetime(data['drawDate'], errors='coerce').astype(np.int64) // 10**9  # Convert to seconds

    # Split the 'numbers' column into individual columns
    data['numbers'] = data['numbers'].apply(lambda x: x.split(','))
    numbers_matrix = np.array(data['numbers'].apply(lambda x: [int(i) for i in x]).tolist())

    # Create columns for each number in the lottery draw
    number_columns = [f'num_{i+1}' for i in range(numbers_matrix.shape[1])]
    numbers_df = pd.DataFrame(numbers_matrix, columns=number_columns)

    # Concatenate the numbers with the original data
    data = pd.concat([data, numbers_df], axis=1)

    # Drop the 'numbers' column (since it's now expanded) and other unnecessary columns
    columns_to_drop = ["numbers", "createdAt", "id"]
    columns_to_drop = [col for col in columns_to_drop if col in data.columns]
    data = data.drop(columns=columns_to_drop)

    # Normalize the data
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data)

    # Split into inputs (X) and targets (y)
    X = data_scaled[:-1]
    y = data_scaled[1:]

    return X, y

# Build Model
def build_model(input_dim):
    model = Sequential([
        Dense(128, activation='relu', input_dim=input_dim),
        Dropout(0.3),
        Dense(128, activation='relu'),
        Dropout(0.3),
        Dense(64, activation='relu'),
        Dense(49, activation='softmax'),
        Dense(input_dim, activation='linear')
    ])
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model

def process_predictions(prediction):
    # Convert predictions to integers (rounding them)
    predicted_numbers = np.round(prediction).astype(int)

    # Ensure numbers are within the valid range [1, 49]
    predicted_numbers = np.clip(predicted_numbers, 1, 49)

    # Ensure uniqueness by converting to a set and then back to a list (may result in fewer than 6 numbers)
    unique_predicted_numbers = list(set(predicted_numbers))

    # If there are not enough unique numbers (in case of collisions), add random numbers until there are 6
    while len(unique_predicted_numbers) < 6:
        new_number = np.random.randint(1, 50)
        if new_number not in unique_predicted_numbers:
            unique_predicted_numbers.append(new_number)

    # If the first predicted number is '1', replace it with a random number from the range [1, 49]
    if unique_predicted_numbers[0] == 1:
        new_random_number = np.random.randint(1, 50)
        while new_random_number in unique_predicted_numbers:
            new_random_number = np.random.randint(1, 50)
        unique_predicted_numbers[0] = new_random_number

    # Sort the numbers (optional, depends on whether order matters)
    unique_predicted_numbers = np.sort(unique_predicted_numbers)

    return unique_predicted_numbers

# Main Training Script
def train_model():
    # Fetch and preprocess data
    data = fetch_data()
    X, y = preprocess_data(data)

    # Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Check the shapes and types before fitting the model
    print(f"X_train shape: {X_train.shape}, type: {X_train.dtype}")
    print(f"y_train shape: {y_train.shape}, type: {y_train.dtype}")

    # Build and Train Model with Early Stopping
    model = build_model(X_train.shape[1])
    early_stopping = EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)

    # Train the model
    history = model.fit(X_train, y_train, epochs=200, batch_size=32, validation_split=0.2, callbacks=[early_stopping])

    # Evaluate the Model
    loss, accuracy = model.evaluate(X_test, y_test)
    print(f"Test Loss: {loss}, Test Accuracy: {accuracy}")

    # Save Model
    model.save('src/ai/lottery_model.keras')
    print("Model saved to ai/lottery_model.keras")

    # Plotting Training and Validation Loss
    plt.plot(history.history['loss'], label='Train Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('Loss during training')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()

    # Predictions
    predictions = model.predict(X_test)
    processed_predictions = np.array([process_predictions(pred) for pred in predictions])

    print(f"First 5 processed predictions: {processed_predictions[:5]}")

if __name__ == "__main__":
    train_model()
