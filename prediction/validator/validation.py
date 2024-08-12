"""
Prediction Validator Module

This module provides an example TextValidator class for validating text generated by modules in subnets.
The TextValidator retrieves module addresses from the subnet, prompts the modules to generate answers to a given question,
and scores the generated answers against the validator's own answers.

Classes:
    TextValidator: A class for validating text generated by modules in a subnet.

Functions:
    set_weights: Blockchain call to set weights for miners based on their scores.
    cut_to_max_allowed_weights: Cut the scores to the maximum allowed weights.
    extract_address: Extract an address from a string.
    get_subnet_netuid: Retrieve the network UID of the subnet.
    get_ip_port: Get the IP and port information from module addresses.

Constants:
    IP_REGEX: A regular expression pattern for matching IP addresses.
"""
import sqlite3
import asyncio
import re
import time
import math
from functools import partial
import numpy as np
import requests
from datetime import datetime
from collections import defaultdict

from communex.client import CommuneClient
from communex.module.client import ModuleClient
from communex.module.module import Module
from communex.types import Ss58Address
from substrateinterface import Keypair

from prediction.validator._config import ValidatorSettings
from prediction.utils import get_random_future_timestamp, log, update_repository

IP_REGEX = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+")


def _set_weights(
    settings: ValidatorSettings,
    score_dict: dict[
        int, float
    ],  # implemented as a float score from 0 to 1, one being the best
    netuid: int,
    client: CommuneClient,
    key: Keypair,
) -> None:
    """
    Set weights for miners based on their scores.

    Args:
        score_dict: A dictionary mapping miner UIDs to their scores.
        netuid: The network UID.
        client: The CommuneX client.
        key: The keypair for signing transactions.
    """

    # Create a new dictionary to store the weighted scores
    weighted_scores: dict[int, int] = {}

    # Iterate over the items in the score_dict
    for uid, score in score_dict.items():
        weighted_scores[uid] = int(score)

    # filter out 0 weights
    weighted_scores = {k: v for k, v in score_dict.items() if v != 0}

    uids = list(weighted_scores.keys())
    weights = list(weighted_scores.values())
    # send the blockchain call
    print(f"uids=============: {uids}")
    print(f"weights=============: {weights}")

    client.vote(key=key, uids=uids, weights=weights, netuid=netuid)
    print("Setting miner weights done")

def extract_address(string: str):
    """
    Extracts an address from a string.
    """
    return re.search(IP_REGEX, string)


def get_subnet_netuid(clinet: CommuneClient, subnet_name: str = "prediction"):
    """
    Retrieve the network UID of the subnet.

    Args:
        client: The CommuneX client.
        subnet_name: The name of the subnet (default: "foo").

    Returns:
        The network UID of the subnet.

    Raises:
        ValueError: If the subnet is not found.
    """

    subnets = clinet.query_map_subnet_names()
    for netuid, name in subnets.items():
        if name == subnet_name:
            return netuid
    raise ValueError(f"Subnet {subnet_name} not found")


def get_ip_port(modules_adresses: dict[int, str]):
    """
    Get the IP and port information from module addresses.

    Args:
        modules_addresses: A dictionary mapping module IDs to their addresses.

    Returns:
        A dictionary mapping module IDs to their IP and port information.
    """

    filtered_addr = {id: extract_address(addr) for id, addr in modules_adresses.items()}
    ip_port = {
        id: x.group(0).split(":") for id, x in filtered_addr.items() if x is not None
    }
    return ip_port


class Validation(Module):
    """
    A class for validating time series prediction generated by modules in a subnet.

    Attributes:
        client: The CommuneClient instance used to interact with the subnet.
        key: The keypair used for authentication.
        netuid: The unique identifier of the subnet.
        val_model: The validation model used for scoring answers.
        call_timeout: The timeout value for module calls in seconds (default: 60).

    Methods:
        get_modules: Retrieve all module addresses from the subnet.
        _get_miner_prediction: Prompt a miner module to generate an answer to the given question.
        _score_miner: Score the generated answer against the validator's own answer.
        get_miner_prompt: Generate a prompt for the miner modules.
        validate_step: Perform a validation step by generating questions, prompting modules, and scoring answers.
        validation_loop: Run the validation loop continuously based on the provided settings.
    """

    def __init__(
        self,
        key: Keypair,
        netuid: int,
        client: CommuneClient,
        call_timeout: int = 60,
    ) -> None:
        super().__init__()
        self.client = client
        self.key = key
        self.netuid = netuid
        self.val_model = "foo"
        self.call_timeout = call_timeout
        self.initialize_database()

    def initialize_database(self):
        self.conn = sqlite3.connect('predictions.db')
        c = self.conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS predictions
                     (timestamp, miner_key, prediction REAL, category, pair)''')
        c.execute('''CREATE TABLE IF NOT EXISTS prices
                 (timestamp, category, pair, price REAL)''')

    def insert_prediction(self, timestamp, miner_key, prediction, category, pair):
        c = self.conn.cursor()
        if prediction is None or prediction == 'None' or prediction == "":
            prediction = -1
            
        c.execute("INSERT INTO predictions VALUES (?,?,?,?,?)", (timestamp, miner_key, prediction, category, pair))

        self.conn.commit()
    
    def insert_into_prices(self, timestamp, category, pair):
        c = self.conn.cursor()
        c.execute("INSERT INTO prices (timestamp, category, pair) VALUES (?,?,?)", (timestamp, category, pair))
        self.conn.commit()

    def schedule_tasks(self, category, pair):
        """Schedules validation tasks to run every 8 hours."""
        asyncio.create_task(self.validation_loop(category, pair))
        
    def get_addresses(self, client: CommuneClient, netuid: int) -> dict[int, str]:
        """
        Retrieve all module addresses from the subnet.

        Args:
            client: The CommuneClient instance used to query the subnet.
            netuid: The unique identifier of the subnet.

        Returns:
            A dictionary mapping module IDs to their addresses.
        """

        # Makes a blockchain query for the miner addresses
        module_addreses = client.query_map_address(netuid)
        return module_addreses

    async def _get_miner_prediction(
        self,
        category: str,
        pair: str,
        timestamp: str,
        miner_id: int, 
        miner_info: tuple[list[str], Ss58Address],
    ) -> tuple[str, str | None]:
        """
        Prompt a miner module to generate an answer to the given question.

        Args:
            question: The question to ask the miner module.
            miner_info: A tuple containing the miner's connection information and key.

        Returns:
            The generated answer from the miner module, or None if the miner fails to generate an answer.
        """
        connection, miner_key = miner_info
        module_ip, module_port = connection
        client = ModuleClient(module_ip, int(module_port), self.key)

        try:
            # handles the communication with the miner
            miner_answer = await client.call(
                    "generate",
                    miner_key,
                    {"category": category, "pair": pair, "timestamp": timestamp},
                    timeout=self.call_timeout,
                )
            miner_answer = miner_answer["answer"]

        except Exception as e:
            # log(f"Miner {module_ip}:{module_port} failed to generate an answer")
            # print(e)
            miner_answer = None
        
        return miner_id, miner_key, miner_answer

    async def fetch_real_data(self, category, pair, unix_timestamp):
        # url = 'https://api.binance.com/api/v3/klines'
        url = 'https://api.kraken.com/0/public/OHLC'

        # Define the symbol and interval
        interval = '1'  # 1 minute interval

        # Convert the UNIX timestamp to a datetime object
        target_time = datetime.utcfromtimestamp(unix_timestamp)

        # Round down to the nearest minute
        target_time = target_time.replace(second=0, microsecond=0)

        # # For binance
        # start_time_ms = int(target_time.timestamp() * 1000)
        # end_time_ms = start_time_ms + 60000  # 60000 milliseconds = 1 minute

        # # Prepare parameters for the API request
        # params = {
        #     'symbol': symbol,
        #     'interval': interval,
        #     'startTime': start_time_ms,
        #     'endTime': end_time_ms,
        #     'limit': 1  # We want exactly 1 data point
        # }
        
        # For kraken
        since_timestamp = int(target_time.timestamp()) * 1000  # Kraken uses milliseconds

        if pair == 'BTCUSDT':
            pair = "XXBTZUSD"
            
        params = {
            'pair': pair,
            'interval': interval,
            'since': since_timestamp  # Fetch data since this timestamp
        }

        # Make the HTTP request
        response = requests.get(url, params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            if data.get('error'):
                print("Error in API response:", data['error'])
                return None
            
            # # Each data point includes [Open time, Open, High, Low, Close, Volume, Close time, ...]
            # if data:
            #     candle = data[0]
            #     open_time = datetime.utcfromtimestamp(candle[0] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            #     close_price = candle[4]
                
            #     print(f"close_price:----{close_price}")
            #     return {'time': open_time, 'close_price': close_price}
            # else:
            #     print("No data available for the given timestamp.")
            #     return None
            
            if data['result']:
                pair_key = list(data['result'].keys())[0]
                last_data_point = data['result'][pair_key][-1]
                open_time = datetime.utcfromtimestamp(last_data_point[0]).strftime('%Y-%m-%d %H:%M:%S')
                close_price = last_data_point[4]
                
                return close_price
            else:
                print("No data available.")
                return None
        else:
            print("Failed to fetch data:", response.status_code)
            return None

    def get_miner_prompt(self):
        """
        Generate a prompt for the miner modules.

        Returns:
            The generated prompt for the miner modules.
        """

        # filename = 'predictionList.json'
        # categories = self.load_categories(filename)
        # category, pair = self.random_category_selection(categories)
        category = "crypto"
        pair = "BTCUSDT"
        timestamp = get_random_future_timestamp()
        
        # save prompt data in prices table in DB.
        self.insert_into_prices(timestamp, category, pair)

        return {"category": category, "pair": pair, "timestamp": timestamp}

    def sigmoid(self, x, steepness=10):
        """Apply a steep sigmoid function to x."""
        return 1 - 1 / (1 + np.exp(-steepness * x))

    async def send_request(
        self, netuid: int
    ) -> None:
        """
        Perform a validation step.

        Generates questions based on the provided settings, prompts modules to generate answers,
        and scores the generated answers against the validator's own answers.

        Args:
            netuid: The network UID of the subnet.
        """
        # retrive the miner information
        modules_adresses = self.get_addresses(self.client, netuid)
        modules_keys = self.client.query_map_key(netuid)
        val_ss58 = self.key.ss58_address
        if val_ss58 not in modules_keys.values():
            raise RuntimeError(f"validator key {val_ss58} is not registered in subnet")

        modules_info: dict[int, tuple[list[str], Ss58Address]] = {}

        modules_filtered_address = get_ip_port(modules_adresses)
        
        for module_id in modules_keys.keys():
            module_addr = modules_filtered_address.get(module_id, None)
            if not module_addr:
                continue
            modules_info[module_id] = (module_addr, modules_keys[module_id])

        key_string = str(self.key)  # Convert object to string
        key_address = key_string.split('=')[1].strip(')>')
        modules_info = {k: v for k, v in modules_info.items() if v[1] != key_address}
        category, pair, future_timestamp  = self.get_miner_prompt().values()
        print(f"category: {category}, pair: {pair}, future_timestamp: {future_timestamp}")
        
        tasks = [self._get_miner_prediction(category, pair, future_timestamp, id, info) for id, info in modules_info.items()]
        tasks = [task for task in tasks if task is not None]
        predictions = await asyncio.gather(*tasks, return_exceptions=True)
        
        # store prediction values in DB
        for prediction in predictions:
            if isinstance(prediction, Exception):
                continue
            miner_id, miner_key, predicted_value = prediction
            self.insert_prediction(future_timestamp, miner_key, predicted_value, category, pair)
    
    async def set_weights(
        self,
        settings: ValidatorSettings,
    ) -> None:
        """
        Set weights for miners based on their scores.

        Args:
            netuid: The network UID.
            client: The CommuneX client.
            key: The keypair for signing transactions.
        """

        # Create a cursor object
        c = self.conn.cursor()

        # Get the current time
        now = time.time()

        # Calculate the start of the weighting period
        start_time = now - settings.weighting_period - 3*60
        print(f"start_time: {start_time}")
        # Retrieve all predictions made within the weighting period
        c.execute("""
            SELECT predictions.*, prices.price 
            FROM predictions 
            INNER JOIN prices ON predictions.timestamp = prices.timestamp 
            WHERE predictions.timestamp >= ? AND prices.price IS NOT NULL
        """, (start_time,))

        predictions = c.fetchall()
        
        # Group predictions by miner key
        grouped_predictions = defaultdict(list)
        for timestamp, miner_key, predicted_value, category, pair, price in predictions:
            grouped_predictions[miner_key].append((timestamp, category, pair, predicted_value, price))

        # Calculate scores for each miner
        scores = {}
        for miner_key, miner_predictions in grouped_predictions.items():
            differences = []
            for timestamp, category, pair, predicted_value, price in miner_predictions:                
                # Calculate the difference
                if predicted_value == -1:
                    difference = None
                else:
                    difference = abs(float(price) - float(predicted_value))
                
                differences.append(difference)

            # Calculate the average difference
            if differences:
                # Remove None values
                differences = [d for d in differences if d is not None]

                if differences:
                    average_difference = sum(differences) / len(differences)
                    # If there were any None values, replace them with 5 times the average
                    num_none = differences.count(None)
                    if num_none > 0:
                        average_difference = (average_difference * len(differences) + 5 * average_difference * num_none) / (len(differences) + num_none)
                else:
                    # If all values were None, assign a large average difference
                    average_difference = 10000000
            else:
                # If the miner has no predictions, assign a large average difference
                average_difference = 10000000

            # Store the score
            scores[miner_key] = average_difference
        
        # Normalize the scores
        if scores:
            for miner_key, score in scores.items():
                if score == 10000000:
                    scores[miner_key] = 0
            
            remaining_scores = {key: score for key, score in scores.items() if score != 0}        

            if remaining_scores:
                min_score = min(remaining_scores.values())
                max_score = max(remaining_scores.values())

                if max_score == min_score:
                    # If all scores are equal, assign a uniform weight
                    for miner_key in remaining_scores:
                        scores[miner_key] = settings.max_allowed_weights

                else:
                    # Normalize the remaining miners' scores
                    for miner_key, score in remaining_scores.items():
                        normalized_score = self.sigmoid((max_score - score) / (max_score - min_score))
                        scores[miner_key] = normalized_score * settings.max_allowed_weights

            print(f"scores: {scores}")
        
        # the blockchain call to set the weights
        if scores:            
            id_map_key = self.client.query_map_key(self.netuid)
            key_to_id = {v: k for k, v in id_map_key.items()}
            scores = {key_to_id[key]: score for key, score in scores.items() if key in key_to_id}
            _ = _set_weights(settings, scores, self.netuid, self.client, self.key)

    async def validation_loop(self, settings: ValidatorSettings) -> None:
        """
        Run the validation loop continuously based on the provided settings.

        Args:
            settings: The validator settings to use for the validation loop.
        """
        # Create two tasks that run concurrently
        task1 = asyncio.create_task(self.send_request_loop(settings))
        task2 = asyncio.create_task(self.set_weights_loop(settings))
        task3 = asyncio.create_task(self.get_price_loop(settings))
        # Wait for both tasks to complete
        await asyncio.gather(task1, task2, task3)

    async def send_request_loop(self, settings: ValidatorSettings) -> None:
        """
        Continuously send requests to miners every interval seconds.

        Args:
            interval: The interval in seconds between each request.
        """
        while True:
            update_repository()
            start_time = time.time()
            await self.send_request(self.netuid)
            elapsed = time.time() - start_time
            if elapsed < settings.iteration_interval:
                sleep_time = settings.iteration_interval - elapsed
                log(f"Sending requests Sleeping for {sleep_time}")
                await asyncio.sleep(sleep_time)

    async def set_weights_loop(self, settings: ValidatorSettings) -> None:
        """
        Continuously set weights for miners every interval seconds.

        Args:
            interval: The interval in seconds between each weighting.
        """
        while True:
            start_time = time.time()
            await self.set_weights(settings)
            elapsed = time.time() - start_time
            if elapsed < settings.weighting_period:
                sleep_time = settings.weighting_period - elapsed
                log(f"Setting weights Sleeping for {sleep_time}")
                await asyncio.sleep(sleep_time)

    async def get_price_loop(self, settings: ValidatorSettings) -> None:
        """
        Continuously get actual price for the future timestamp in every 1 min using Kraken API.

        Args:
            interval: The interval in seconds between each weighting.
        """
        while True:
            start_time = time.time()

            # Fetch the first record in prices table where price is still empty
            c = self.conn.cursor()
            c.execute("SELECT * FROM prices WHERE price IS NULL ORDER BY timestamp ASC LIMIT 1")
            record = c.fetchone()

            if record:
                timestamp, category, pair, _ = record

                # Fetch the real data
                real_data = await self.fetch_real_data(category, pair, timestamp)

                # Update the price in the prices table
                c.execute("UPDATE prices SET price = ? WHERE timestamp = ? AND category = ? AND pair = ?", (real_data, timestamp, category, pair))
                self.conn.commit()

            elapsed = time.time() - start_time
            if elapsed < settings.get_real_data_interval:
                sleep_time = settings.get_real_data_interval - elapsed
                log(f"Price loop Sleeping for {sleep_time}")
                await asyncio.sleep(sleep_time)