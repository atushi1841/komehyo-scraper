# Komehyo Japan Luxury Resale Scraper

Scrape Japan's largest reuse department store, **Komehyo (コメ兵)**, for authentic luxury items from **Louis Vuitton, Chanel, Gucci, Hermès, Rolex**, and more.

This actor uses plain HTTP requests (`httpx`) against Komehyo's server-side rendered search pages. No headless browser or product detail pages are required, making it fast and cost-efficient.

## Why Komehyo?

- One of Japan's biggest authenticated luxury resale marketplaces
- Huge inventory across bags, wallets, jewelry, watches, and fashion
- SSR search pages are directly crawlable
- `robots.txt` contains no `Disallow` rules
- Ideal for Japan luxury resale price monitoring, brand bag arbitrage, and cross-border resale research

## Input

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `keyword` | string | `ルイヴィトン` | Search keyword, e.g. `シャネル`, `グッチ`, `LOUIS VUITTON` |
| `maxItems` | integer | `100` | Maximum products to scrape, up to `500` |
| `proxyConfiguration` | object | `{}` | Apify proxy configuration |

## Output Sample

