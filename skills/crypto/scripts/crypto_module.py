#!/usr/bin/env python3
"""
Crypto Data Module for ChatGPT Skills
Cryptocurrency price, market data, and analysis

Data Source: CoinGecko API (free, no API key required)

Usage:
    from crypto_module import CryptoClient

    client = CryptoClient()

    # Get current price
    price = client.get_price("bitcoin")
    price = client.get_price("ethereum", currency="cny")

    # Get detailed market data
    data = client.get_market_data("bitcoin")

    # Get historical prices
    history = client.get_history("bitcoin", days=30)

    # Get trending coins
    trending = client.get_trending()

    # Search cryptocurrencies
    results = client.search("eth")

Command Line:
    python3 crypto_module.py price bitcoin
    python3 crypto_module.py price ethereum --currency cny
    python3 crypto_module.py market bitcoin
    python3 crypto_module.py history bitcoin --days 30
    python3 crypto_module.py trending
    python3 crypto_module.py search eth
    python3 crypto_module.py top 10
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union


class CryptoClient:
    """Cryptocurrency data client using CoinGecko API"""

    BASE_URL = "https://api.coingecko.com/api/v3"

    # Common crypto ID mappings
    CRYPTO_ALIASES = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "usdt": "tether",
        "bnb": "binancecoin",
        "xrp": "ripple",
        "ada": "cardano",
        "doge": "dogecoin",
        "sol": "solana",
        "dot": "polkadot",
        "matic": "matic-network",
        "shib": "shiba-inu",
        "ltc": "litecoin",
        "avax": "avalanche-2",
        "link": "chainlink",
        "atom": "cosmos",
        "uni": "uniswap",
        "xlm": "stellar",
        "etc": "ethereum-classic",
        "xmr": "monero",
        "algo": "algorand",
        "trx": "tron",
        "near": "near",
        "apt": "aptos",
        "arb": "arbitrum",
        "op": "optimism",
    }

    def __init__(self, currency: str = "usd"):
        """
        Initialize crypto client

        Args:
            currency: Default currency for prices (usd, cny, eur, jpy, etc.)
        """
        self.default_currency = currency.lower()

    def _request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request"""
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            if params:
                url += "?" + urllib.parse.urlencode(params)

            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "CryptoModule/1.0",
                    "Accept": "application/json"
                }
            )

            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                return {"error": "Rate limit exceeded. Please wait a moment."}
            return {"error": f"HTTP Error: {e.code}"}
        except Exception as e:
            return {"error": str(e)}

    def _resolve_id(self, crypto: str) -> str:
        """Resolve crypto symbol/alias to CoinGecko ID"""
        crypto = crypto.lower().strip()
        return self.CRYPTO_ALIASES.get(crypto, crypto)

    def get_price(
        self,
        crypto: str,
        currency: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get current price for a cryptocurrency

        Args:
            crypto: Cryptocurrency ID or symbol (e.g., "bitcoin", "btc", "ethereum")
            currency: Target currency (default: usd)

        Returns:
            Dict with price data
        """
        crypto_id = self._resolve_id(crypto)
        currency = (currency or self.default_currency).lower()

        data = self._request("simple/price", {
            "ids": crypto_id,
            "vs_currencies": currency,
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true",
            "include_last_updated_at": "true"
        })

        if not data or "error" in data:
            return data

        if crypto_id not in data:
            return {"error": f"Cryptocurrency not found: {crypto}"}

        price_data = data[crypto_id]
        return {
            "id": crypto_id,
            "symbol": crypto.upper(),
            "currency": currency.upper(),
            "price": price_data.get(currency),
            "change_24h": price_data.get(f"{currency}_24h_change"),
            "volume_24h": price_data.get(f"{currency}_24h_vol"),
            "market_cap": price_data.get(f"{currency}_market_cap"),
            "last_updated": datetime.fromtimestamp(
                price_data.get("last_updated_at", 0)
            ).isoformat() if price_data.get("last_updated_at") else None
        }

    def get_market_data(
        self,
        crypto: str,
        currency: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get detailed market data for a cryptocurrency

        Args:
            crypto: Cryptocurrency ID or symbol
            currency: Target currency

        Returns:
            Dict with detailed market data
        """
        crypto_id = self._resolve_id(crypto)
        currency = (currency or self.default_currency).lower()

        data = self._request(f"coins/{crypto_id}", {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false"
        })

        if not data or "error" in data:
            return data

        market = data.get("market_data", {})

        return {
            "id": data.get("id"),
            "symbol": data.get("symbol", "").upper(),
            "name": data.get("name"),
            "currency": currency.upper(),
            "price": market.get("current_price", {}).get(currency),
            "market_cap": market.get("market_cap", {}).get(currency),
            "market_cap_rank": market.get("market_cap_rank"),
            "fully_diluted_valuation": market.get("fully_diluted_valuation", {}).get(currency),
            "volume_24h": market.get("total_volume", {}).get(currency),
            "high_24h": market.get("high_24h", {}).get(currency),
            "low_24h": market.get("low_24h", {}).get(currency),
            "change_24h": market.get("price_change_24h"),
            "change_percent_24h": market.get("price_change_percentage_24h"),
            "change_percent_7d": market.get("price_change_percentage_7d"),
            "change_percent_30d": market.get("price_change_percentage_30d"),
            "change_percent_1y": market.get("price_change_percentage_1y"),
            "ath": market.get("ath", {}).get(currency),
            "ath_change_percent": market.get("ath_change_percentage", {}).get(currency),
            "ath_date": market.get("ath_date", {}).get(currency),
            "atl": market.get("atl", {}).get(currency),
            "atl_change_percent": market.get("atl_change_percentage", {}).get(currency),
            "circulating_supply": market.get("circulating_supply"),
            "total_supply": market.get("total_supply"),
            "max_supply": market.get("max_supply"),
            "last_updated": market.get("last_updated")
        }

    def get_history(
        self,
        crypto: str,
        days: int = 30,
        currency: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get historical price data

        Args:
            crypto: Cryptocurrency ID or symbol
            days: Number of days (1, 7, 14, 30, 90, 180, 365, max)
            currency: Target currency

        Returns:
            Dict with historical price data
        """
        crypto_id = self._resolve_id(crypto)
        currency = (currency or self.default_currency).lower()

        data = self._request(f"coins/{crypto_id}/market_chart", {
            "vs_currency": currency,
            "days": days,
            "interval": "daily" if days > 1 else "hourly"
        })

        if not data or "error" in data:
            return data

        prices = data.get("prices", [])
        volumes = data.get("total_volumes", [])
        market_caps = data.get("market_caps", [])

        history = []
        for i, (timestamp, price) in enumerate(prices):
            history.append({
                "date": datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d"),
                "timestamp": timestamp,
                "price": price,
                "volume": volumes[i][1] if i < len(volumes) else None,
                "market_cap": market_caps[i][1] if i < len(market_caps) else None
            })

        return {
            "id": crypto_id,
            "currency": currency.upper(),
            "days": days,
            "data": history
        }

    def get_trending(self) -> Optional[Dict]:
        """
        Get trending cryptocurrencies

        Returns:
            Dict with trending coins
        """
        data = self._request("search/trending")

        if not data or "error" in data:
            return data

        coins = []
        for item in data.get("coins", []):
            coin = item.get("item", {})
            coins.append({
                "id": coin.get("id"),
                "symbol": coin.get("symbol", "").upper(),
                "name": coin.get("name"),
                "market_cap_rank": coin.get("market_cap_rank"),
                "score": coin.get("score")
            })

        return {
            "trending": coins,
            "updated_at": datetime.now().isoformat()
        }

    def get_top(
        self,
        limit: int = 10,
        currency: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """
        Get top cryptocurrencies by market cap

        Args:
            limit: Number of results (1-250)
            currency: Target currency

        Returns:
            List of top cryptocurrencies
        """
        currency = (currency or self.default_currency).lower()
        limit = min(max(1, limit), 250)

        data = self._request("coins/markets", {
            "vs_currency": currency,
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": "false"
        })

        if not data or isinstance(data, dict) and "error" in data:
            return data

        results = []
        for coin in data:
            results.append({
                "rank": coin.get("market_cap_rank"),
                "id": coin.get("id"),
                "symbol": coin.get("symbol", "").upper(),
                "name": coin.get("name"),
                "price": coin.get("current_price"),
                "change_24h": coin.get("price_change_percentage_24h"),
                "market_cap": coin.get("market_cap"),
                "volume_24h": coin.get("total_volume"),
                "currency": currency.upper()
            })

        return results

    def search(self, query: str) -> Optional[List[Dict]]:
        """
        Search for cryptocurrencies

        Args:
            query: Search query

        Returns:
            List of matching cryptocurrencies
        """
        data = self._request("search", {"query": query})

        if not data or "error" in data:
            return data

        results = []
        for coin in data.get("coins", [])[:10]:
            results.append({
                "id": coin.get("id"),
                "symbol": coin.get("symbol", "").upper(),
                "name": coin.get("name"),
                "market_cap_rank": coin.get("market_cap_rank")
            })

        return results

    def get_exchanges(self, limit: int = 10) -> Optional[List[Dict]]:
        """
        Get top cryptocurrency exchanges

        Args:
            limit: Number of results

        Returns:
            List of exchanges
        """
        data = self._request("exchanges", {
            "per_page": min(limit, 100),
            "page": 1
        })

        if not data or isinstance(data, dict) and "error" in data:
            return data

        results = []
        for ex in data[:limit]:
            results.append({
                "id": ex.get("id"),
                "name": ex.get("name"),
                "country": ex.get("country"),
                "trust_score": ex.get("trust_score"),
                "trust_score_rank": ex.get("trust_score_rank"),
                "trade_volume_24h_btc": ex.get("trade_volume_24h_btc"),
                "url": ex.get("url")
            })

        return results

    def get_global(self) -> Optional[Dict]:
        """
        Get global cryptocurrency market data

        Returns:
            Dict with global market statistics
        """
        data = self._request("global")

        if not data or "error" in data:
            return data

        global_data = data.get("data", {})

        return {
            "active_cryptocurrencies": global_data.get("active_cryptocurrencies"),
            "markets": global_data.get("markets"),
            "total_market_cap_usd": global_data.get("total_market_cap", {}).get("usd"),
            "total_volume_24h_usd": global_data.get("total_volume", {}).get("usd"),
            "btc_dominance": global_data.get("market_cap_percentage", {}).get("btc"),
            "eth_dominance": global_data.get("market_cap_percentage", {}).get("eth"),
            "market_cap_change_24h": global_data.get("market_cap_change_percentage_24h_usd"),
            "updated_at": datetime.fromtimestamp(
                global_data.get("updated_at", 0)
            ).isoformat() if global_data.get("updated_at") else None
        }


def format_number(num, decimals=2):
    """Format large numbers"""
    if num is None:
        return "-"
    if num >= 1e12:
        return f"{num/1e12:.{decimals}f}T"
    if num >= 1e9:
        return f"{num/1e9:.{decimals}f}B"
    if num >= 1e6:
        return f"{num/1e6:.{decimals}f}M"
    if num >= 1e3:
        return f"{num/1e3:.{decimals}f}K"
    return f"{num:.{decimals}f}"


def format_price(price, currency="USD"):
    """Format price with currency symbol"""
    if price is None:
        return "-"
    symbols = {"USD": "$", "CNY": "¥", "EUR": "€", "JPY": "¥", "GBP": "£"}
    symbol = symbols.get(currency.upper(), "")
    if price >= 1:
        return f"{symbol}{price:,.2f}"
    else:
        return f"{symbol}{price:.6f}"


def main():
    """Command line interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Crypto Module - ChatGPT Skills")
    parser.add_argument("command", choices=["price", "market", "history", "trending", "top", "search", "exchanges", "global"],
                       help="Command to execute")
    parser.add_argument("crypto", nargs="?", help="Cryptocurrency ID or symbol")
    parser.add_argument("--currency", "-c", default="usd", help="Target currency (usd, cny, eur, etc.)")
    parser.add_argument("--days", "-d", type=int, default=30, help="Days for history")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Number of results")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    client = CryptoClient(currency=args.currency)

    if args.command == "price":
        if not args.crypto:
            print("Error: Please provide a cryptocurrency")
            return

        result = client.get_price(args.crypto, args.currency)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif "error" in result:
            print(f"Error: {result['error']}")
        else:
            change = result['change_24h'] or 0
            change_symbol = "+" if change >= 0 else ""
            print(f"\n{'='*50}")
            print(f"  {result['symbol']} ({result['id']})")
            print(f"{'='*50}")
            print(f"  价格: {format_price(result['price'], result['currency'])}")
            print(f"  24h涨跌: {change_symbol}{change:.2f}%")
            print(f"  24h成交量: {format_number(result['volume_24h'])}")
            print(f"  市值: {format_number(result['market_cap'])}")
            print(f"{'='*50}\n")

    elif args.command == "market":
        if not args.crypto:
            print("Error: Please provide a cryptocurrency")
            return

        result = client.get_market_data(args.crypto, args.currency)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n{'='*60}")
            print(f"  {result['name']} ({result['symbol']})")
            print(f"  市值排名: #{result['market_cap_rank']}")
            print(f"{'='*60}")
            print(f"  价格: {format_price(result['price'], result['currency'])}")
            print(f"  24h最高: {format_price(result['high_24h'], result['currency'])}")
            print(f"  24h最低: {format_price(result['low_24h'], result['currency'])}")
            print(f"  24h涨跌: {result['change_percent_24h']:.2f}%")
            print(f"  7d涨跌: {result['change_percent_7d']:.2f}%" if result['change_percent_7d'] else "")
            print(f"  30d涨跌: {result['change_percent_30d']:.2f}%" if result['change_percent_30d'] else "")
            print(f"  市值: {format_number(result['market_cap'])}")
            print(f"  24h成交量: {format_number(result['volume_24h'])}")
            print(f"  流通量: {format_number(result['circulating_supply'], 0)}")
            print(f"  历史最高: {format_price(result['ath'], result['currency'])} ({result['ath_change_percent']:.1f}%)")
            print(f"{'='*60}\n")

    elif args.command == "history":
        if not args.crypto:
            print("Error: Please provide a cryptocurrency")
            return

        result = client.get_history(args.crypto, args.days, args.currency)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n{result['id'].upper()} - {args.days}天历史数据")
            print("-" * 40)
            for item in result['data'][-10:]:  # Show last 10 days
                print(f"  {item['date']}: {format_price(item['price'], result['currency'])}")
            if len(result['data']) > 10:
                print(f"  ... (共 {len(result['data'])} 条数据)")
            print()

    elif args.command == "trending":
        result = client.get_trending()

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n{'='*50}")
            print(f"  热门加密货币")
            print(f"{'='*50}")
            for i, coin in enumerate(result['trending'], 1):
                rank = f"#{coin['market_cap_rank']}" if coin['market_cap_rank'] else ""
                print(f"  {i}. {coin['symbol']} - {coin['name']} {rank}")
            print(f"{'='*50}\n")

    elif args.command == "top":
        limit = args.crypto if args.crypto and args.crypto.isdigit() else args.limit
        result = client.get_top(int(limit) if limit else 10, args.currency)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif isinstance(result, dict) and "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n{'='*70}")
            print(f"  市值排名前 {len(result)} 加密货币")
            print(f"{'='*70}")
            print(f"  {'排名':<6}{'代码':<8}{'价格':<15}{'24h涨跌':<12}{'市值':<15}")
            print(f"  {'-'*60}")
            for coin in result:
                change = coin['change_24h'] or 0
                change_str = f"{'+' if change >= 0 else ''}{change:.1f}%"
                print(f"  #{coin['rank']:<5}{coin['symbol']:<8}"
                      f"{format_price(coin['price'], coin['currency']):<15}"
                      f"{change_str:<12}{format_number(coin['market_cap']):<15}")
            print(f"{'='*70}\n")

    elif args.command == "search":
        if not args.crypto:
            print("Error: Please provide a search query")
            return

        result = client.search(args.crypto)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif isinstance(result, dict) and "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n搜索结果: '{args.crypto}'")
            print("-" * 40)
            for coin in result:
                rank = f"#{coin['market_cap_rank']}" if coin['market_cap_rank'] else ""
                print(f"  {coin['symbol']} - {coin['name']} {rank}")
                print(f"    ID: {coin['id']}")
            print()

    elif args.command == "exchanges":
        result = client.get_exchanges(args.limit)

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif isinstance(result, dict) and "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n{'='*60}")
            print(f"  Top {len(result)} 加密货币交易所")
            print(f"{'='*60}")
            for ex in result:
                print(f"  {ex['trust_score_rank']}. {ex['name']}")
                print(f"     信任分: {ex['trust_score']}/10 | 24h交易量: {format_number(ex['trade_volume_24h_btc'])} BTC")
            print(f"{'='*60}\n")

    elif args.command == "global":
        result = client.get_global()

        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n{'='*50}")
            print(f"  全球加密货币市场数据")
            print(f"{'='*50}")
            print(f"  活跃币种: {result['active_cryptocurrencies']:,}")
            print(f"  交易市场: {result['markets']:,}")
            print(f"  总市值: ${format_number(result['total_market_cap_usd'])}")
            print(f"  24h成交量: ${format_number(result['total_volume_24h_usd'])}")
            print(f"  BTC占比: {result['btc_dominance']:.1f}%")
            print(f"  ETH占比: {result['eth_dominance']:.1f}%")
            print(f"  24h市值变化: {result['market_cap_change_24h']:.2f}%")
            print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
