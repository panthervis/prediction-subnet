from pydantic_settings import BaseSettings


class ValidatorSettings(BaseSettings):
    iteration_interval: int = 120  # Send requests to miners for every iteration interval in seconds - 2 minutes
    max_allowed_weights: int = 800  # Best score for miner
    weighting_period: int = 240 # 30 blocks time that sets weights for miners - 4 minutes
    get_real_data_interval: int = 60 # getting real data interval for crypto prices - 1 min