# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from functools import reduce

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


# This class is a sample. Feel free to customize it.
class NanaStrategy(IStrategy):
    """
    This is a sample strategy to inspire you.
    More information in https://www.freqtrade.io/en/latest/strategy-customization/

    You can:
        :return: a Dataframe with all mandatory indicators for the strategies
    - Rename the class name (Do not forget to update class_name)
    - Add any methods you want to build your strategy
    - Add any lib you need to build your strategy

    You must keep:
    - the lib in the section "Do not remove these libs"
    - the methods: populate_indicators, populate_buy_trend, populate_sell_trend
    You should keep:
    - timeframe, minimal_roi, stoploss, trailing_*
    """
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 2

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "60": 0.01,
        "30": 0.02,
        "0": 0.04
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.10

    # Trailing stoploss
    trailing_stop = False
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured

    # Hyperoptable parameters
    #buy_rsi = IntParameter(low=1, high=50, default=30, space='buy', optimize=True, load=True)
    #sell_rsi = IntParameter(low=50, high=100, default=70, space='sell', optimize=True, load=True)
    buy_ema1= IntParameter(3,98,default=9)
    #sell_sma20= IntParameter(5,100,default=24)
    buy_ema2= IntParameter(5,100,default=24)
    #sell_sma20= IntParameter(5,100,default=24)
    
    fastk_period=IntParameter(4,50,default=14)
    slowk_period=IntParameter(4,50,default=14)


    fastperiod=IntParameter(4,50,default=12)
    slowperiod=IntParameter(4,50,default=26)
    signalperiod=IntParameter(4,50,default=9)

    rsi_period=IntParameter(4,60,default=14)

    
    buy_rsi = IntParameter(40, 80, default=50, space="buy")
    sell_rsi = IntParameter(20, 80, default=50, space="sell")

    buy_STK = IntParameter(40, 80, default=50, space="buy")
    sell_STK = IntParameter(20, 80, default=50, space="sell")
    


    #buy_ema_long1 = IntParameter(3, 50, default=5)
    #buy_ema_long2= IntParameter(50,80,default=
    #buy_ema_short = IntParameter(3, 200, default=50)

    # Optimal timeframe for the strategy.
    timeframe = '5m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = True
    sell_profit_only = False
    ignore_roi_if_buy_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 70

    # Optional order type mapping.
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc'
    }

    plot_config = {
        'main_plot': {
            'tema': {},
            'sar': {'color': 'white'},
        },
        'subplots': {
            "MACD": {
                'macd': {'color': 'blue'},
                'macdsignal': {'color': 'orange'},
            },
            "RSI": {
                'rsi': {'color': 'red'},
            }
        }
    }

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        :param dataframe: Dataframe with data from the exchange
        :param metadata: Additional information, like the currently traded pair
        :return: a Dataframe with all mandatory indicators for the strategies
        """
        # EMA - Exponential Moving Average
        for val in self.buy_ema1.range:
             dataframe[f'ema_9b_{val}'] = ta.EMA(dataframe, timeperiod=val)
        for val in self.buy_ema2.range:
            dataframe[f'ema_24b_{val}'] = ta.EMA(dataframe, timeperiod=val)
        

        for val in self.fastperiod.range:
            for val2 in self.slowperiod.range:
                for val3 in self.signalperiod.range:
                    macd = ta.MACD(dataframe, fastperiod=val, slowperiod=val2, signalperiod=val3)            
                    dataframe[f'macd_{val}_{val2}'] = macd['macd']
                    dataframe[f'macdsignal_{val3}'] = macd['macdsignal']
                    #dataframe[f'macdhist_{val3}'] = macd['macdhist']



        for val in self.fastk_period.range:
            for val2 in self.slowk_period.range:
                # Stochastic Fast
                stoch = ta.STOCH(dataframe, fastk_period=val, slowk_period=val2)
                dataframe[f'slowd_{val}_{val2}'] = stoch['slowd']
                dataframe[f'slowk_{val}_{val2}'] = stoch['slowk']



        
        for val in self.rsi_period.range:
            dataframe['rsi'] = ta.RSI(dataframe,timeperiod=val)    

        # Retrieve best bid and best ask from the orderbook
        # ------------------------------------
        """
        # first check if dataprovider is available
        if self.dp:
            if self.dp.runmode.value in ('live', 'dry_run'):
                ob = self.dp.orderbook(metadata['pair'], 1)
                dataframe['best_bid'] = ob['bids'][0][0]
                dataframe['best_ask'] = ob['asks'][0][0]
        """

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy columns
        """
        conditions = []

        conditions.append((dataframe[f'close']>dataframe[f'ema_9b_{self.buy_ema1.value}']))
        conditions.append((dataframe[f'close']>dataframe[f'ema_24b_{self.buy_ema2.value}']))

        conditions.append((dataframe[f'rsi']>self.buy_rsi.value))
        
        conditions.append((dataframe[f'slowd_{self.fastk_period.value}_{self.slowk_period.value}']>self.buy_STK.value))
        conditions.append((dataframe[f'slowK_{self.fastk_period.value}_{self.slowk_period.value}']>self.buy_STK.value))

        #conditions.append(dataframe[f'macd_{self.fastperiod.value}_{self.slowperiod.value}']>dataframe[f'macdsignal_{self.signalperiod.value}'])
        conditions.append(qtpylib.crossed_above(dataframe[f'macd_{self.fastperiod.value}_{self.slowperiod.value}'],dataframe[f'macdsignal_{self.signalperiod.value}']))


        # Check that volume is not 0
        conditions.append(dataframe['volume'] > 0)
        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with sell column
        """
        conditions = []

        conditions.append((dataframe[f'close']<dataframe[f'ema_9b_{self.buy_ema1.value}']))
        conditions.append((dataframe[f'close']<dataframe[f'ema_24b_{self.buy_ema2.value}']))

        conditions.append((dataframe[f'rsi']<self.sell_rsi.value))
        
        conditions.append((dataframe[f'slowd_{self.fastk_period.value}_{self.slowk_period.value}']<self.sell_STK.value))
        conditions.append((dataframe[f'slowK_{self.fastk_period.value}_{self.slowk_period.value}']<self.sell_STK.value))

        conditions.append(qtpylib.crossed_below(dataframe[f'macd_{self.fastperiod.value}_{self.slowperiod.value}'],dataframe[f'macdsignal_{self.signalperiod.value}']))

        # Check that volume is not 0
        conditions.append(dataframe['volume'] > 0)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'sell'] = 1



        return dataframe

