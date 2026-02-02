---
name: crypto
description: Query cryptocurrency prices, market data, historical prices, trending coins, and exchange rankings from CoinGecko. Use when user asks about Bitcoin, Ethereum, or any crypto prices, market cap, or trading data.
---

# Crypto 加密货币 Skill

查询加密货币价格、市场数据、历史价格、趋势榜和交易所信息。数据源：CoinGecko（免费，无需 API Key）。

## 快速开始

无需安装额外依赖，直接使用：

```bash
python3 ~/.claude/skills/crypto/scripts/crypto_module.py price bitcoin
```

## 功能列表

### 1. 实时价格

```bash
# 美元计价
python3 ~/.claude/skills/crypto/scripts/crypto_module.py price bitcoin
python3 ~/.claude/skills/crypto/scripts/crypto_module.py price ethereum
python3 ~/.claude/skills/crypto/scripts/crypto_module.py price btc    # 支持缩写

# 其他货币计价
python3 ~/.claude/skills/crypto/scripts/crypto_module.py price bitcoin --currency cny
python3 ~/.claude/skills/crypto/scripts/crypto_module.py price ethereum --currency eur
```

支持的缩写：btc, eth, usdt, bnb, xrp, ada, doge, sol, dot, matic, shib, ltc, avax, link, atom, uni 等

### 2. 详细市场数据

```bash
python3 ~/.claude/skills/crypto/scripts/crypto_module.py market bitcoin
python3 ~/.claude/skills/crypto/scripts/crypto_module.py market ethereum --currency cny
```

返回：当前价格、24h涨跌、7d涨跌、30d涨跌、市值、市值排名、24h交易量、历史最高价、流通量等

### 3. 历史价格

```bash
python3 ~/.claude/skills/crypto/scripts/crypto_module.py history bitcoin --days 30
python3 ~/.claude/skills/crypto/scripts/crypto_module.py history ethereum --days 90
python3 ~/.claude/skills/crypto/scripts/crypto_module.py history btc --days 365
```

### 4. 趋势榜

```bash
python3 ~/.claude/skills/crypto/scripts/crypto_module.py trending
```

### 5. 市值排行

```bash
python3 ~/.claude/skills/crypto/scripts/crypto_module.py top 10
python3 ~/.claude/skills/crypto/scripts/crypto_module.py top 20 --currency cny
```

### 6. 全球市场统计

```bash
python3 ~/.claude/skills/crypto/scripts/crypto_module.py global
```

返回：活跃币种数、交易市场数、总市值、24h交易量、BTC/ETH市场占比、24h市值变化

### 7. 交易所排行

```bash
python3 ~/.claude/skills/crypto/scripts/crypto_module.py exchanges
python3 ~/.claude/skills/crypto/scripts/crypto_module.py exchanges --limit 20
```

返回：交易所名称、信任评分、24h交易量(BTC)、国家

### 8. 搜索加密货币

```bash
python3 ~/.claude/skills/crypto/scripts/crypto_module.py search "eth"
python3 ~/.claude/skills/crypto/scripts/crypto_module.py search "solana"
```

## Python 模块使用

```python
from crypto_module import CryptoClient

client = CryptoClient(currency="usd")

# 获取价格
price = client.get_price("bitcoin")
print(f"BTC: ${price['price']:,.2f}, 24h涨跌: {price['change_24h']:.2f}%")

# 详细市场数据
market = client.get_market_data("ethereum")
print(f"ETH 市值排名: #{market['market_cap_rank']}")

# 历史价格
history = client.get_history("bitcoin", days=30)
for item in history['data'][-5:]:
    print(f"{item['date']}: ${item['price']:,.2f}")

# 趋势榜
trending = client.get_trending()
for coin in trending['trending']:
    print(f"{coin['symbol']}: {coin['name']}")

# 全球统计
global_data = client.get_global()
print(f"总市值: ${global_data['total_market_cap_usd']:,.0f}")
print(f"BTC占比: {global_data['btc_dominance']:.1f}%")
```

## 参数说明

| 参数 | 说明 |
|------|------|
| `--currency` / `-c` | 计价货币 (usd/cny/eur/jpy 等) |
| `--days` / `-d` | 历史数据天数 |
| `--limit` / `-l` | 结果数量限制 |
| `--json` | JSON 格式输出 |

## 支持的计价货币

usd, cny, eur, jpy, gbp, krw, hkd, twd, sgd, aud, cad, chf, inr, thb, vnd, idr, myr, php 等

---

**费用**: 免费
**数据源**: CoinGecko API
**限制**: 免费版有速率限制，请求过于频繁会被限流
