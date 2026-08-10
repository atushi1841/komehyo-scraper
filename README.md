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
| `proxyConfiguration` | object | `{}` | Apify proxy configuration. Use `useApifyProxy: true` only (auto). Country-specific proxies (`apifyProxyCountry`) return 407 on free plans. |

## Output Sample

```json
{
  "productId": "260-008-023-3589",
  "title": "ルイヴィトン (ソフィアコッポラ&ルイヴィトン) スリムクラッチ M95861 バッグ",
  "brand": "LOUIS VUITTON",
  "price": 75000,
  "referencePrice": null,
  "rank": "中古品A",
  "size": null,
  "material": null,
  "store": "KOMEHYO SHIBUYA",
  "imageUrl": "https://img.komehyo.jp/contents/images/goods/840/2600080233589_1_icon.jpg",
  "productUrl": "https://komehyo.jp/product/260-008-023-3589/",
  "scrapedAt": "2026-08-10T10:02:44Z"
}
```

## Use Cases

- **Luxury resale arbitrage** — find underpriced bags/watches before others
- **Price monitoring** — track Louis Vuitton, Chanel, Rolex market prices
- **Cross-border resale research** — Japan luxury market trends

## Integrations

Works with Apify [Connectors](https://apify.com/integrations) — push results to Slack, Google Sheets, Notion, or Supabase with one click. Trigger on a [Schedule](https://apify.com/docs/schedules) for daily price tracking.

> 💡 **For cross-shop comparison**, use the [Japan Luxury Brand Market Scraper](https://apify.com/fruitful_quintessence/japan-luxury-brand-market-scraper) — it compares Komehyo categories against Jackroad watches in a single dataset.
