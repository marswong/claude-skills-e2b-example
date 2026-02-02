---
name: stock
description: Query US and China A-share stock data including real-time quotes, historical K-line data, technical analysis (MA, RSI, MACD, Bollinger Bands), and chart generation. Use when user asks about stock prices, market data, or technical indicators.
---

# Stock 股票数据 Skill

查询美股和A股的实时报价、历史K线、技术分析和图表生成。

## 快速开始

### 安装依赖

```bash
# 美股数据
pip3 install yfinance

# A股数据 (可选)
pip3 install akshare
```

### 验证安装

```bash
python3 ~/.claude/skills/stock/scripts/stock_module.py quote AAPL
```

## 功能列表

### 1. 实时报价

```bash
# 美股
python3 ~/.claude/skills/stock/scripts/stock_module.py quote AAPL
python3 ~/.claude/skills/stock/scripts/stock_module.py quote TSLA
python3 ~/.claude/skills/stock/scripts/stock_module.py quote MSFT

# A股
python3 ~/.claude/skills/stock/scripts/stock_module.py quote 600519 --market cn
python3 ~/.claude/skills/stock/scripts/stock_module.py quote 000001 --market cn
```

### 2. 历史K线数据

```bash
python3 ~/.claude/skills/stock/scripts/stock_module.py history AAPL --period 1y
python3 ~/.claude/skills/stock/scripts/stock_module.py history AAPL --period 6mo
python3 ~/.claude/skills/stock/scripts/stock_module.py history AAPL --period 1mo
python3 ~/.claude/skills/stock/scripts/stock_module.py history 600519 --market cn --period 3mo
```

支持周期：1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max

### 3. 技术分析

```bash
python3 ~/.claude/skills/stock/scripts/stock_module.py analyze AAPL
python3 ~/.claude/skills/stock/scripts/stock_module.py analyze TSLA --period 6mo
python3 ~/.claude/skills/stock/scripts/stock_module.py analyze 600519 --market cn
```

包含指标：
- **MA**: 移动平均线 (MA5, MA10, MA20, MA50)
- **RSI**: 相对强弱指数 (14期)
- **MACD**: 指数平滑异同移动平均线
- **布林带**: 上轨、中轨、下轨

### 4. 生成图表

```bash
# HTML 交互式图表
python3 ~/.claude/skills/stock/scripts/stock_module.py chart AAPL --period 6mo --output aapl_chart.html

# PNG 静态图表 (需要 matplotlib)
python3 ~/.claude/skills/stock/scripts/stock_module.py chart AAPL --period 6mo --output aapl_chart.png
```

### 5. 搜索股票

```bash
python3 ~/.claude/skills/stock/scripts/stock_module.py search apple
python3 ~/.claude/skills/stock/scripts/stock_module.py search "茅台" --market cn
```

## Python 模块使用

```python
from stock_module import StockClient

client = StockClient()

# 获取报价
quote = client.get_quote("AAPL")
print(f"价格: ${quote['price']}, 涨跌: {quote['change_percent']:.2f}%")

# 获取历史数据
history = client.get_history("AAPL", period="6mo")
print(history.tail())

# 技术分析
analysis = client.analyze("AAPL")
print(f"RSI: {analysis['indicators']['rsi_14']:.2f}")
print(f"MACD: {analysis['indicators']['macd_trend']}")

# 生成图表
client.get_chart("AAPL", period="6mo", output="chart.html")
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `--market` | 市场 (us/cn)，默认 us |
| `--period` | 时间周期 (1d/5d/1mo/3mo/6mo/1y/2y/5y/max) |
| `--output` | 输出文件路径 |

## 数据说明

### 美股数据
- 数据源：Yahoo Finance (yfinance)
- 实时性：15分钟延迟
- 货币：USD

### A股数据
- 数据源：东方财富 (akshare)
- 实时性：实时
- 货币：CNY

---

**费用**: 免费
**依赖**: yfinance (美股), akshare (A股)
