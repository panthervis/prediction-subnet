from communex.module import Module, endpoint
from communex.key import generate_keypair
from keylimiter import TokenBucketLimiter
from prediction.miner.prediction import Prediction

class Miner(Module):
    """
    A module class for mining and generating responses to prompts.

    Attributes:
        None

    Methods:
        generate: Generates a response to a given prompt using a specified model.
    """
    @endpoint
    def generate(self, category: str, pair: str, timestamp: int):
        """
        Generates a response to a given prompt using a specified model.

        Args:
            prompt: The prompt to generate a response for.
            model: The model to use for generating the response (default: "gpt-3.5-turbo").

        Returns:
            None
        """
        predictions = []
        match category:
            case "crypto":
                if (pair == "BTCUSDT"):
                    base_currency = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
                    quote_currency = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
                    p = Prediction(base_currency, quote_currency, timestamp)
                    predictions = p.predict()
            case "forex":
                pass
            case "gambling":
                pass
            case "betting":
                pass
            case "weather":    
                pass
            case _:
                pass
                
                
        print(f"Answering prediction for {category} category & {pair} pair: {predictions}")
