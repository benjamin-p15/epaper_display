import os, sys, time, math
import pandas as pd
import yfinance as yf #pip install yfinance --break-system-packages
import numpy as np 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from dashboard.epaper_display import ImageDrawer

class StocksDisplayRender:
    def __init__(self, width: int, height: int):
        self.screen=ImageDrawer(width,height)
        self.scale_factor=width/height
        self._cache_img = None
        self._last_update = 0

        self.UPDATE_INTERVAL = 12*60*60
        self.simple_stock_companies=["^GSPC", "VTI", "AAPL", "CAT", "BMW.DE", "BA", "NVDA"]
        self.simple_stock_companies_names = {"^GSPC":"S&P500", "VTI":"Vanguard","AAPL":"Apple","CAT":"Caterpillar" ,"BMW.DE":"BMW","BA":"Boeing", "NVDA": "NAVIDA"}
        self.history_stock_compeny="^GSPC"
        self.history_stock_compeny_name="S&P 500"

        self.simple_stock_file=os.path.join(os.path.dirname(__file__), "data/stock_precent_change.csv")
        self.history_stock_file = os.path.join(os.path.dirname(__file__), "data/history_precent_change.csv")
        os.makedirs(os.path.dirname(self.simple_stock_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.history_stock_file), exist_ok=True)

    def getPrecentChange(self):
        if os.path.exists(self.simple_stock_file) and time.time() - os.path.getmtime(self.simple_stock_file) < self.UPDATE_INTERVAL: return pd.read_csv(self.simple_stock_file, index_col=0)
        data = {}
        for company in self.simple_stock_companies:
            stock = yf.Ticker(company)
            info = stock.history(period="2d")  
            if len(info) >= 2:
                prev_close = info['Close'][-2]
                last_close = info['Close'][-1]
                pct_change = ((last_close - prev_close) / prev_close) * 100
                data[company] = round(pct_change, 2)
            else: data[company] = None
        
        df = pd.DataFrame(list(data.items()), columns=['company', 'precent_change']).set_index('company')
        df.to_csv(self.simple_stock_file)
        return df
        
    def getHistoryChange(self, weeks=52):
        if os.path.exists(self.history_stock_file) and time.time() - os.path.getmtime(self.history_stock_file) < self.UPDATE_INTERVAL:
            df = pd.read_csv(self.history_stock_file, index_col=0, parse_dates=True)
            df.index = pd.to_datetime(df.index, utc=True)
        else:
            compeny = yf.Ticker(self.history_stock_compeny)
            hist = compeny.history(period=f"{weeks*7}d", interval="1wk")
            precent_change = (hist['Close'].pct_change() * 100).round(2)
            df = precent_change.to_frame('precent_change')
            df.to_csv(self.history_stock_file)
        df = df.dropna(subset=['precent_change'])
        df.index = pd.DatetimeIndex(df.index)
        end_date = pd.Timestamp.utcnow()
        start_date = end_date - pd.Timedelta(weeks=weeks)
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        dates_array = df.index.view('int64') // 10**9 
        change_array = df['precent_change'].to_numpy()
        min_max_array = [df.index.min(), df.index.max(), change_array.min(), change_array.max()]
        return dates_array, change_array, min_max_array
    
    def normalize_array(self, arr, new_min=0, new_max=1, smooth=False, smooth_window=3):
        arr = np.array(arr, dtype=float)
        if smooth: arr = pd.Series(arr).rolling(window=smooth_window, min_periods=1, center=True).mean().to_numpy()
        old_min = arr.min()
        old_max = arr.max()
        if old_max == old_min: return np.full_like(arr, new_min)
        return ((arr - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min
    
    def render(self,force=False):
    # Update screen every 10 minutes or if otherwise requested
        now = time.time()
        if force or (self._cache_img is None or now - self._last_update >= 10 * 60):
            self._last_update = now

            stocks=self.getPrecentChange()
            history_timeframe,history_precent,history_bounds=self.getHistoryChange()

            y=0.13
            for company, row in stocks.iterrows():
                precent_change = row['precent_change']

                if precent_change>0: 
                    text_color=1
                    thickness=None
                    stroke_fill=0
                else: 
                    text_color=0
                    thickness=2
                    stroke_fill=1
                if math.isnan(precent_change): text=f"    --"
                else: text=f"{precent_change}%"

                self.screen.add_rectangle(position=(0.86, y-0.0175), size=(0.12,0.075), fill=0, radius=10, thickness=thickness)
                self.screen.add_text([{"text": f"{self.simple_stock_companies_names[company]}:", "size": 18}], position=(0.69, y), align="left", bold=True)
                self.screen.add_text([{"text": text, "size": 18}], position=(0.88, y), align="left", bold=True,fill=text_color,stroke_width=1,stroke_fill=stroke_fill)
                y+=0.085
            self.screen.add_rectangle(position=(0.68, 0.1), size=(0.31,0.61), fill=0, radius=8, thickness=2)


            self.screen.add_text([{"text": f"{self.history_stock_compeny_name}:", "size": 18}], position=(0.65/2, 0.05), align="center", bold=True)
            self.screen.add_rectangle(position=(0.01, 0.1), size=(0.65,0.8), fill=0, radius=8, thickness=2)
            history_timeframe=self.normalize_array(history_timeframe,new_min=0.01+0.01,new_max=0.65-0.01)
            history_precent=self.normalize_array(history_precent,new_min=0.1+0.02,new_max=0.9-0.02,smooth=True)

            for i, history in enumerate(history_timeframe):
                precent = history_precent[i]
                self.screen.add_circle((history,precent),0.005,thickness=-1,fill=0)
                if i > 0: self.screen.add_line((history,precent),(history_timeframe[i-1],history_precent[i-1]),fill=0,thickness=1)

            self.screen.add_rectangle(position=(0.01, 0.91), size=(0.65,0.05), fill=0, radius=8, thickness=2)
            self.screen.add_text([{"text": f"{history_bounds[0].strftime("%B %Y")}", "size": 17}], position=(0.01+0.01, 0.91+0.005), align="left", bold=True)
            self.screen.add_text([{"text": f"{history_bounds[1].strftime("%B %Y")}", "size": 17}], position=(0.66-0.01, 0.91+0.005), align="right", bold=True)

            self.screen.add_rectangle(position=(0.68, 0.72), size=(0.31,0.24), fill=0, radius=8, thickness=2)


            # Screen render stuff
            self._cache_img=self.screen.render()
            if(self._cache_img is None): return None, False
            else: return self._cache_img, True
        return self._cache_img, False

if __name__ == "__main__":
    img, show = StocksDisplayRender(800, 480).render()
    img.show()