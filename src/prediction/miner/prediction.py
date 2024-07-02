import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from prediction.miner.data.binance import get_candlestick_data
from transformers import AutoModelForSequenceClassification, AutoTokenizer

class Prediction:
    def __init__(self, base_currency, quote_currency, time_interval):
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.time_interval = time_interval
        self.model = None
        self.tokenizer = None
        self.scaler = None
        self.model_dir = 'models'
    
    def fetch_data(self):
        candlestick_data = get_candlestick_data(self.base_currency, self.quote_currency, self.time_interval)
        return candlestick_data
    
    def extract_close_prices(self, data):
        close_prices = [trade['close'] for trade in data]
        return close_prices
    
    def extract_open_price_and_volume(self, data):
        open_prices = [trade['open_price'] for trade in data]
        volumes = [trade['quoteAmount'] for trade in data]
        return [open_prices, volumes]

    def scale_data(self, prep_data):
        prep_data = np.array(prep_data).T
        prep_data = prep_data[-50:]  # Last 50 observations
        self.scaler = MinMaxScaler()
        scaled_data = self.scaler.fit_transform(prep_data)
        return scaled_data

    def load_model(self):
        if os.path.exists(self.model_dir) and os.listdir(self.model_dir):
            model_files = os.listdir(self.model_dir)
            model_path = os.path.join(self.model_dir, model_files[0])  # Load the first model found
            print("Loading model from:", model_path)
            self.model = tf.keras.models.load_model(model_path)
        else:
            print("Model directory is empty or not found. Loading from Hugging Face.")
            model_name = "bert-base-uncased"  # Example model
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def moving_average(self, data, window_size):
        return pd.Series(data).rolling(window=window_size).mean().iloc[-1]
    
    def predict(self, window_size=10, steps=8):
        if self.model is None:
            self.load_model()
            
        candlestick_data = self.fetch_data()
        if not candlestick_data:
            print("No data available for prediction.")
            return None
        
        prep_data = self.extract_open_price_and_volume(candlestick_data)
        close_prices = self.extract_close_prices(candlestick_data)
        
        if len(close_prices) < window_size:
            print("Insufficient data for making predictions.")
            return None
        
        if not prep_data or len(prep_data[0]) < 50:  # Check if there's enough data
            print("Insufficient data for making predictions.")
            return None
        
        scaled_data = self.scale_data(prep_data)
        scaled_data = np.expand_dims(scaled_data, axis=0)

        predictions = []
        data = close_prices.copy()
        
        for _ in range(steps):
            next_pred = self.moving_average(data, window_size)
            predictions.append(next_pred)
            data.append(next_pred)  # Append the predicted value for the next iteration

        return predictions
