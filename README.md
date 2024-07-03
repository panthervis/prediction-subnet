# Prediction Subnet

Innovative time-series prediction subnet which will provide any time-series prediction data in crypto, forex, gambling, betting, whether, and more based on intensive competition among miners with state-of-the-art models.


## Overview
Prediction subnet will organize competition between miner modules. The more similar to real value to produce for longer time period, the more incentive a miner will get.

## Validator
Validators will periodically send time-series prediction request selecting random categories and type for randomly selected timestamp in next 8 hours.
Upon getting prediction response from miners, it will distribute incentives in sigmoid function on how close the prediction is to the real value.

```sh
python3 validator/validation.py <name-of-your-com-key>
```

## Miner
Miners should respond to validator's request with most correct prediction. Miners are proposed to utilize any methods to provide prediction results. Miners can choose what they are best at prediction among categories from predictoinList.json

```sh
python3 miner/app.py <name-of-your-com-key>
```

