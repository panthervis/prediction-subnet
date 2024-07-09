import asyncio
import random
import json

from communex.client import CommuneClient
from substrateinterface import Keypair
from validation import Validation

def load_categories(filename):
        with open(filename, 'r') as file:
            categories = json.load(file)
        return categories

def random_category_selection(categories):
    main_category = random.choice(list(categories.keys()))
    sub_category = random.choice(categories[main_category])
    return main_category, sub_category

async def main():
    client = CommuneClient()
    key = Keypair()  # Placeholder for actual keypair initialization
    netuid = 1234
    validation = Validation(key, netuid, client)
    
    # get prediction category and pair
    # filename = 'predictionList.json'
    # categories = load_categories(filename)
    # category, pair = random_category_selection(categories)
    category = "crypto"
    pair = "BTCUSDT"
    validation.schedule_tasks(category, pair)

if __name__ == '__main__':
    asyncio.run(main())