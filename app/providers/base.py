from abc import ABC, abstractmethod

import pandas as pd


class StockProvider(ABC):
    name: str

    @abstractmethod
    def fetch(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        raise NotImplementedError
