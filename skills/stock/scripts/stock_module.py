#!/usr/bin/env python3
"""
Stock Data Module - ChatGPT Skills
统一的股票数据获取模块，支持美股和A股

功能:
- 实时报价 (US: yfinance, CN: AKShare)
- 历史K线数据
- 技术分析 (RSI, MACD, 布林带, 移动平均线)
- 价格走势图表生成

使用方法:
    from stock_module import StockClient

    client = StockClient()

    # 美股报价
    quote = client.get_quote("AAPL")

    # A股报价
    quote = client.get_quote("600519", market="cn")

    # 历史数据
    history = client.get_history("AAPL", period="1y")

    # 技术分析
    analysis = client.analyze("AAPL")

    # 生成图表
    chart = client.get_chart("AAPL", period="6mo")
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import pandas as pd

# Try to import optional dependencies
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("Warning: yfinance not installed. US stock data unavailable.")

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    print("Warning: akshare not installed. A-share data unavailable.")

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class StockClient:
    """统一的股票数据客户端"""

    VALID_PERIODS = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max']

    def __init__(self):
        """初始化股票客户端"""
        self.cache = {}

    def get_quote(self, symbol: str, market: str = "us") -> Dict:
        """
        获取股票实时报价

        Args:
            symbol: 股票代码 (美股: AAPL, A股: 600519 或 sh600519)
            market: 市场 ("us" 或 "cn")

        Returns:
            包含报价信息的字典
        """
        if market.lower() == "cn":
            return self._get_cn_quote(symbol)
        else:
            return self._get_us_quote(symbol)

    def _get_us_quote(self, symbol: str) -> Dict:
        """获取美股报价"""
        if not HAS_YFINANCE:
            return {"error": "yfinance not installed"}

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol.upper(),
                "name": info.get("longName", info.get("shortName", symbol)),
                "price": info.get("currentPrice", info.get("regularMarketPrice")),
                "change": info.get("regularMarketChange"),
                "change_percent": info.get("regularMarketChangePercent"),
                "open": info.get("regularMarketOpen"),
                "high": info.get("regularMarketDayHigh"),
                "low": info.get("regularMarketDayLow"),
                "volume": info.get("regularMarketVolume"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "market": "US",
                "currency": info.get("currency", "USD"),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "symbol": symbol}

    def _get_cn_quote(self, symbol: str) -> Dict:
        """获取A股报价"""
        if not HAS_AKSHARE:
            return {"error": "akshare not installed"}

        try:
            # 标准化股票代码
            if not symbol.startswith(('sh', 'sz', 'bj')):
                # 根据代码判断市场
                if symbol.startswith('6'):
                    symbol = f"sh{symbol}"
                elif symbol.startswith(('0', '3')):
                    symbol = f"sz{symbol}"
                elif symbol.startswith(('4', '8')):
                    symbol = f"bj{symbol}"

            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            code = symbol[2:]  # 去掉前缀

            stock_data = df[df['代码'] == code]
            if stock_data.empty:
                return {"error": f"Stock {symbol} not found", "symbol": symbol}

            row = stock_data.iloc[0]

            return {
                "symbol": symbol,
                "name": row.get('名称', ''),
                "price": float(row.get('最新价', 0)),
                "change": float(row.get('涨跌额', 0)),
                "change_percent": float(row.get('涨跌幅', 0)),
                "open": float(row.get('今开', 0)),
                "high": float(row.get('最高', 0)),
                "low": float(row.get('最低', 0)),
                "volume": int(row.get('成交量', 0)),
                "amount": float(row.get('成交额', 0)),
                "market": "CN",
                "currency": "CNY",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e), "symbol": symbol}

    def get_history(
        self,
        symbol: str,
        period: str = "1y",
        market: str = "us"
    ) -> pd.DataFrame:
        """
        获取历史K线数据

        Args:
            symbol: 股票代码
            period: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            market: 市场

        Returns:
            包含OHLCV数据的DataFrame
        """
        if market.lower() == "cn":
            return self._get_cn_history(symbol, period)
        else:
            return self._get_us_history(symbol, period)

    def _get_us_history(self, symbol: str, period: str) -> pd.DataFrame:
        """获取美股历史数据"""
        if not HAS_YFINANCE:
            return pd.DataFrame()

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            df.reset_index(inplace=True)
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'dividends', 'stock_splits']
            return df[['date', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            print(f"Error fetching history: {e}")
            return pd.DataFrame()

    def _get_cn_history(self, symbol: str, period: str) -> pd.DataFrame:
        """获取A股历史数据"""
        if not HAS_AKSHARE:
            return pd.DataFrame()

        try:
            # 标准化股票代码
            code = symbol[-6:] if len(symbol) > 6 else symbol

            # 计算日期范围
            end_date = datetime.now()
            period_days = {
                '1d': 1, '5d': 5, '1mo': 30, '3mo': 90,
                '6mo': 180, '1y': 365, '2y': 730, '5y': 1825, 'max': 3650
            }
            days = period_days.get(period, 365)
            start_date = end_date - timedelta(days=days)

            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                adjust="qfq"
            )

            if df.empty:
                return pd.DataFrame()

            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 'change_pct', 'change', 'turnover']
            df['date'] = pd.to_datetime(df['date'])
            return df[['date', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            print(f"Error fetching CN history: {e}")
            return pd.DataFrame()

    def analyze(self, symbol: str, market: str = "us", period: str = "6mo") -> Dict:
        """
        技术分析

        Args:
            symbol: 股票代码
            market: 市场
            period: 分析周期

        Returns:
            包含技术指标的字典
        """
        df = self.get_history(symbol, period, market)
        if df.empty:
            return {"error": "No data available"}

        # 计算技术指标
        analysis = {
            "symbol": symbol,
            "market": market.upper(),
            "period": period,
            "data_points": len(df),
            "latest_price": float(df['close'].iloc[-1]),
            "indicators": {}
        }

        # 移动平均线
        if len(df) >= 5:
            analysis["indicators"]["ma5"] = float(df['close'].tail(5).mean())
        if len(df) >= 10:
            analysis["indicators"]["ma10"] = float(df['close'].tail(10).mean())
        if len(df) >= 20:
            analysis["indicators"]["ma20"] = float(df['close'].tail(20).mean())
        if len(df) >= 50:
            analysis["indicators"]["ma50"] = float(df['close'].tail(50).mean())

        # RSI (14期)
        if len(df) >= 14:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            analysis["indicators"]["rsi_14"] = float(rsi.iloc[-1])

            # RSI 信号
            rsi_value = analysis["indicators"]["rsi_14"]
            if rsi_value > 70:
                analysis["indicators"]["rsi_signal"] = "超买 (Overbought)"
            elif rsi_value < 30:
                analysis["indicators"]["rsi_signal"] = "超卖 (Oversold)"
            else:
                analysis["indicators"]["rsi_signal"] = "中性 (Neutral)"

        # MACD
        if len(df) >= 26:
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            histogram = macd - signal

            analysis["indicators"]["macd"] = float(macd.iloc[-1])
            analysis["indicators"]["macd_signal"] = float(signal.iloc[-1])
            analysis["indicators"]["macd_histogram"] = float(histogram.iloc[-1])

            # MACD 信号
            if macd.iloc[-1] > signal.iloc[-1]:
                analysis["indicators"]["macd_trend"] = "看涨 (Bullish)"
            else:
                analysis["indicators"]["macd_trend"] = "看跌 (Bearish)"

        # 布林带
        if len(df) >= 20:
            sma20 = df['close'].rolling(window=20).mean()
            std20 = df['close'].rolling(window=20).std()
            upper_band = sma20 + (std20 * 2)
            lower_band = sma20 - (std20 * 2)

            analysis["indicators"]["bollinger_upper"] = float(upper_band.iloc[-1])
            analysis["indicators"]["bollinger_middle"] = float(sma20.iloc[-1])
            analysis["indicators"]["bollinger_lower"] = float(lower_band.iloc[-1])

            # 布林带位置
            current_price = df['close'].iloc[-1]
            if current_price > upper_band.iloc[-1]:
                analysis["indicators"]["bollinger_signal"] = "价格突破上轨"
            elif current_price < lower_band.iloc[-1]:
                analysis["indicators"]["bollinger_signal"] = "价格突破下轨"
            else:
                analysis["indicators"]["bollinger_signal"] = "价格在通道内"

        # 价格统计
        analysis["statistics"] = {
            "high": float(df['high'].max()),
            "low": float(df['low'].min()),
            "avg_volume": int(df['volume'].mean()),
            "volatility": float(df['close'].pct_change().std() * 100)
        }

        return analysis

    def get_chart(
        self,
        symbol: str,
        period: str = "6mo",
        market: str = "us",
        output: Optional[str] = None,
        chart_type: str = "line"
    ) -> str:
        """
        生成价格走势图

        Args:
            symbol: 股票代码
            period: 时间周期
            market: 市场
            output: 输出文件路径 (None则返回HTML)
            chart_type: 图表类型 (line, candle)

        Returns:
            HTML字符串或文件路径
        """
        df = self.get_history(symbol, period, market)
        if df.empty:
            return "<p>No data available</p>"

        # 获取报价信息
        quote = self.get_quote(symbol, market)
        name = quote.get('name', symbol)

        if HAS_MATPLOTLIB and output and output.endswith('.png'):
            return self._generate_matplotlib_chart(df, symbol, name, period, output)
        else:
            return self._generate_html_chart(df, symbol, name, period, output)

    def _generate_matplotlib_chart(
        self,
        df: pd.DataFrame,
        symbol: str,
        name: str,
        period: str,
        output: str
    ) -> str:
        """使用matplotlib生成PNG图表"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])

        # 价格图
        ax1.plot(df['date'], df['close'], 'b-', linewidth=1.5, label='Close Price')

        # 添加移动平均线
        if len(df) >= 20:
            ma20 = df['close'].rolling(window=20).mean()
            ax1.plot(df['date'], ma20, 'orange', linewidth=1, label='MA20')
        if len(df) >= 50:
            ma50 = df['close'].rolling(window=50).mean()
            ax1.plot(df['date'], ma50, 'green', linewidth=1, label='MA50')

        ax1.set_title(f'{name} ({symbol}) - {period}', fontsize=14)
        ax1.set_ylabel('Price')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)

        # 成交量图
        ax2.bar(df['date'], df['volume'], color='steelblue', alpha=0.7)
        ax2.set_ylabel('Volume')
        ax2.set_xlabel('Date')

        plt.tight_layout()
        plt.savefig(output, dpi=150, bbox_inches='tight')
        plt.close()

        return output

    def _generate_html_chart(
        self,
        df: pd.DataFrame,
        symbol: str,
        name: str,
        period: str,
        output: Optional[str]
    ) -> str:
        """生成交互式HTML图表"""
        # 准备数据
        dates = df['date'].dt.strftime('%Y-%m-%d').tolist()
        prices = df['close'].tolist()
        volumes = df['volume'].tolist()

        # 计算MA20
        ma20 = df['close'].rolling(window=20).mean().fillna(0).tolist() if len(df) >= 20 else []

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{name} ({symbol}) Stock Chart</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #fff;
            padding: 20px;
            margin: 0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            color: #ffcb05;
        }}
        .chart-container {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-box h3 {{
            color: #888;
            font-size: 0.9em;
            margin: 0 0 5px 0;
        }}
        .stat-box p {{
            font-size: 1.3em;
            margin: 0;
            color: #ffcb05;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{name} ({symbol})</h1>
        <p style="text-align:center;color:#888;">Period: {period} | Data Points: {len(df)}</p>

        <div class="stats">
            <div class="stat-box">
                <h3>Latest Price</h3>
                <p>{prices[-1]:.2f}</p>
            </div>
            <div class="stat-box">
                <h3>High</h3>
                <p>{max(prices):.2f}</p>
            </div>
            <div class="stat-box">
                <h3>Low</h3>
                <p>{min(prices):.2f}</p>
            </div>
            <div class="stat-box">
                <h3>Change</h3>
                <p style="color: {'#4caf50' if prices[-1] > prices[0] else '#ff5252'}">
                    {((prices[-1] - prices[0]) / prices[0] * 100):.2f}%
                </p>
            </div>
        </div>

        <div class="chart-container">
            <canvas id="priceChart"></canvas>
        </div>

        <div class="chart-container">
            <canvas id="volumeChart"></canvas>
        </div>
    </div>

    <script>
        const dates = {json.dumps(dates)};
        const prices = {json.dumps(prices)};
        const volumes = {json.dumps(volumes)};
        const ma20 = {json.dumps(ma20)};

        // Price Chart
        new Chart(document.getElementById('priceChart'), {{
            type: 'line',
            data: {{
                labels: dates,
                datasets: [
                    {{
                        label: 'Close Price',
                        data: prices,
                        borderColor: '#3d7dca',
                        backgroundColor: 'rgba(61, 125, 202, 0.1)',
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0
                    }},
                    {{
                        label: 'MA20',
                        data: ma20,
                        borderColor: '#ffcb05',
                        borderWidth: 1,
                        pointRadius: 0,
                        fill: false
                    }}
                ]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        labels: {{ color: '#fff' }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#888' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }},
                    y: {{
                        ticks: {{ color: '#888' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }}
                }}
            }}
        }});

        // Volume Chart
        new Chart(document.getElementById('volumeChart'), {{
            type: 'bar',
            data: {{
                labels: dates,
                datasets: [{{
                    label: 'Volume',
                    data: volumes,
                    backgroundColor: 'rgba(61, 125, 202, 0.6)'
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        labels: {{ color: '#fff' }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#888' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }},
                    y: {{
                        ticks: {{ color: '#888' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

        if output:
            with open(output, 'w') as f:
                f.write(html)
            return output

        return html

    def search(self, keyword: str, market: str = "us") -> List[Dict]:
        """
        搜索股票

        Args:
            keyword: 搜索关键词
            market: 市场

        Returns:
            匹配的股票列表
        """
        if market.lower() == "cn":
            return self._search_cn(keyword)
        else:
            return self._search_us(keyword)

    def _search_us(self, keyword: str) -> List[Dict]:
        """搜索美股"""
        if not HAS_YFINANCE:
            return []

        try:
            # yfinance doesn't have a native search, use ticker directly
            ticker = yf.Ticker(keyword.upper())
            info = ticker.info
            if info and info.get('symbol'):
                return [{
                    "symbol": info.get('symbol'),
                    "name": info.get('longName', info.get('shortName', '')),
                    "type": info.get('quoteType', ''),
                    "exchange": info.get('exchange', '')
                }]
            return []
        except Exception:
            return []

    def _search_cn(self, keyword: str) -> List[Dict]:
        """搜索A股"""
        if not HAS_AKSHARE:
            return []

        try:
            df = ak.stock_zh_a_spot_em()
            # 按代码或名称搜索
            matches = df[
                df['代码'].str.contains(keyword, case=False) |
                df['名称'].str.contains(keyword, case=False)
            ].head(10)

            return [
                {
                    "symbol": row['代码'],
                    "name": row['名称'],
                    "price": row['最新价'],
                    "change_pct": row['涨跌幅']
                }
                for _, row in matches.iterrows()
            ]
        except Exception:
            return []


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description="Stock Data Module - ChatGPT Skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get US stock quote
  python3 stock_module.py quote AAPL

  # Get A-share quote
  python3 stock_module.py quote 600519 --market cn

  # Get history
  python3 stock_module.py history AAPL --period 1y

  # Technical analysis
  python3 stock_module.py analyze AAPL

  # Generate chart
  python3 stock_module.py chart AAPL --output chart.html

  # Search stocks
  python3 stock_module.py search apple
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Quote command
    quote_parser = subparsers.add_parser('quote', help='Get stock quote')
    quote_parser.add_argument('symbol', help='Stock symbol')
    quote_parser.add_argument('--market', '-m', default='us', choices=['us', 'cn'])

    # History command
    history_parser = subparsers.add_parser('history', help='Get historical data')
    history_parser.add_argument('symbol', help='Stock symbol')
    history_parser.add_argument('--period', '-p', default='1y',
                                choices=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'])
    history_parser.add_argument('--market', '-m', default='us', choices=['us', 'cn'])

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Technical analysis')
    analyze_parser.add_argument('symbol', help='Stock symbol')
    analyze_parser.add_argument('--period', '-p', default='6mo')
    analyze_parser.add_argument('--market', '-m', default='us', choices=['us', 'cn'])

    # Chart command
    chart_parser = subparsers.add_parser('chart', help='Generate price chart')
    chart_parser.add_argument('symbol', help='Stock symbol')
    chart_parser.add_argument('--period', '-p', default='6mo')
    chart_parser.add_argument('--market', '-m', default='us', choices=['us', 'cn'])
    chart_parser.add_argument('--output', '-o', help='Output file path')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search stocks')
    search_parser.add_argument('keyword', help='Search keyword')
    search_parser.add_argument('--market', '-m', default='us', choices=['us', 'cn'])

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    client = StockClient()

    if args.command == 'quote':
        result = client.get_quote(args.symbol, args.market)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == 'history':
        df = client.get_history(args.symbol, args.period, args.market)
        if not df.empty:
            print(df.to_string())
        else:
            print("No data available")

    elif args.command == 'analyze':
        result = client.analyze(args.symbol, args.market, args.period)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == 'chart':
        output = args.output or f"{args.symbol}_chart.html"
        result = client.get_chart(args.symbol, args.period, args.market, output)
        print(f"Chart saved to: {result}")

    elif args.command == 'search':
        results = client.search(args.keyword, args.market)
        print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
