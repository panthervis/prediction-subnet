# Prediction Subnet

The Prediction Subnet is an advanced time-series prediction platform designed to support a wide range of domains including cryptocurrency, foreign exchange (forex), gambling, betting, weather predictions and more. This platform leverages a competitive model where miners (prediction models) compete to provide the most accurate predictions, earning incentives based on their performance.


## Overview
Prediction Subnet orchestrates a dynamic competition among various miner modules equipped with state-of-the-art predictive models. The system emphasizes long-term accuracy in predictions, rewarding miners who consistently align closely with real-world outcomes.

## How It Works
Validators: Validators operate as the orchestrators within the subnet. They periodically request predictions for random categories and types, selecting timestamps within the next 8 hours. Upon receiving predictions, validators assess the accuracy using a sigmoid function to determine how closely predictions align with actual outcomes, subsequently distributing incentives based on this accuracy.

Miners: Miners respond to requests from validators with predictions. They are encouraged to utilize any effective methods at their disposal to ensure accuracy. Miners can specialize in specific categories to optimize their predictive capabilities.

## Getting Started
### Prerequisites
Ensure you have Python 3.10+ installed on your system. You can verify this by running:
```sh
python --version
```
### Installation
Clone the repository to your local machine:

```sh
git clone https://github.com/yourusername/prediction-subnet.git
cd prediction-subnet
```

Install required dependencies:
```sh
pip install -r requirements.txt
```

### Validator Setup
Run the validator script to start validating predictions. Replace <name-of-your-com-key> with your actual key.
```sh
python3 -m prediction.validator.cli <name-of-your-com-key>
```

### Miner Setup
Start your miner by running the miner application. Ensure your key is correctly configured.

```sh
python3 -m prediction.validator.cli <name-of-your-com-key>
```

## License
Distributed under the MIT License. See LICENSE for more information.