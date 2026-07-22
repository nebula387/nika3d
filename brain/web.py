"""
Поиск актуальной информации в интернете: погода, курсы валют, новости,
общий веб-поиск. Все источники бесплатные и не требуют API-ключей.

  погода   — open-meteo.com (геокодинг + прогноз)
  валюты   — open.er-api.com (обновляется раз в сутки, есть RUB)
  поиск/новости — ddgs (DuckDuckGo)
"""

import requests

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
_FX_URL      = "https://open.er-api.com/v6/latest/{base}"

_WEATHER_CODES = {
    0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "rime fog",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow",
    80: "rain showers", 81: "rain showers", 82: "violent rain showers",
    95: "thunderstorm",
}

# Разговорные названия валют → ISO-код
CURRENCY_WORDS = {
    "dollar": "USD", "dollars": "USD", "usd": "USD",
    "euro": "EUR", "euros": "EUR", "eur": "EUR",
    "pound": "GBP", "pounds": "GBP", "sterling": "GBP", "gbp": "GBP",
    "ruble": "RUB", "rubles": "RUB", "rouble": "RUB", "roubles": "RUB", "rub": "RUB",
    "yuan": "CNY", "renminbi": "CNY", "cny": "CNY",
    "yen": "JPY", "jpy": "JPY",
    "franc": "CHF", "francs": "CHF", "chf": "CHF",
}


def get_weather(city: str) -> str:
    """Текущая погода в городе city. Возвращает готовую фразу на английском."""
    try:
        geo = requests.get(_GEOCODE_URL, params={"name": city, "count": 1}, timeout=8).json()
        results = geo.get("results")
        if not results:
            return f"Couldn't find a location called '{city}'."

        loc = results[0]
        lat, lon = loc["latitude"], loc["longitude"]
        place, country = loc.get("name", city), loc.get("country", "")

        wx = requests.get(_WEATHER_URL, params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,weather_code,wind_speed_10m",
        }, timeout=8).json()

        cur = wx["current"]
        desc = _WEATHER_CODES.get(cur["weather_code"], "unclear conditions")
        return (
            f"Weather in {place}, {country}: {cur['temperature_2m']}°C, {desc}, "
            f"wind {cur['wind_speed_10m']} km/h."
        )
    except Exception as e:
        return f"Weather lookup failed: {e}"


def get_exchange_rate(base: str, target: str) -> str:
    """Курс base->target. Коды валют ISO (USD, EUR, RUB, ...)."""
    try:
        resp = requests.get(_FX_URL.format(base=base.upper()), timeout=8).json()
        if resp.get("result") != "success":
            return f"Exchange rate lookup failed for {base.upper()}."
        rate = resp.get("rates", {}).get(target.upper())
        if rate is None:
            return f"No exchange rate found for {base.upper()} to {target.upper()}."
        return f"1 {base.upper()} = {rate:.4f} {target.upper()}."
    except Exception as e:
        return f"Exchange rate lookup failed: {e}"


def web_search(query: str, max_results: int = 4) -> str:
    """Обычный веб-поиск через DuckDuckGo. Возвращает сырые сниппеты."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No search results found."
        return "\n".join(f"- {r['title']}: {r['body']}" for r in results)
    except Exception as e:
        return f"Web search failed: {e}"


def news_search(topic: str = "", max_results: int = 4) -> str:
    """Свежие новости по теме (или общие, если topic пустой)."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.news(topic or "world news", max_results=max_results))
        if not results:
            return "No news results found."
        return "\n".join(f"- [{r.get('date', '')[:10]}] {r['title']}" for r in results)
    except Exception as e:
        return f"News search failed: {e}"
