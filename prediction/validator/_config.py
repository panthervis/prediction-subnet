from pydantic_settings import BaseSettings


class ValidatorSettings(BaseSettings):
    iteration_interval: int = 300  # Send requests to miners for every iteration interval in seconds
    max_allowed_weights: int = 800  # Best score for miner
    weighting_period: int = 2400 # 300 blocks that sets weights for miners - 40 minutes