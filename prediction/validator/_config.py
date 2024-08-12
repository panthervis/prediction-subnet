from pydantic_settings import BaseSettings


class ValidatorSettings(BaseSettings):
    iteration_interval: int = 100  # Send requests to miners for every iteration interval in seconds - 5 minutes
    max_allowed_weights: int = 800  # Best score for miner
    weighting_period: int = 300 # 300 blocks that sets weights for miners - 40 minutes
    get_real_data_interval: int = 60 # getting real data interval for crypto prices - 1 min