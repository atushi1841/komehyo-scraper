import asyncio
import json
import random
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode, urljoin

import httpx

try:
    from apify import Actor
except ImportError:
    Actor = None

BASE_URL = "https://komehyo.jp/"
SEARCH_URL = "https://komehyo.jp/search/"
MAX_PAGES = 200

# 商品カードの <a> を抽出。商品IDはハイフン区切り(例: 260-008-023-3589)
CARD_RE = re.compile(
    r'<a\b(?=[^>]*\bclass=["\'][^"\']*p-link--card[^"\']*["\'])(?=[^>]*\bhref="/product/([\d-]+)/")[^>]*>'
)

FIELD_CLASSES = {
    "title": "p-link__txt--productsname",
    "brand": "p-link__txt--brand",
    "size": "p-link__txt--size",
    "rank": "p-link__txt--rank",
    "material": "p-link__txt--material",
    "store": "p-link__txt--store",
    "reference": "p-link__txt--reference",
    "price": "p-link__txt--price",
}


def extract_text(segment: str, class_name: str):
    """指定クラスを持つ span の中身からタグを除去してテキストを返す。"""
    pattern = (
        r'<span[^>]*class=["\'][^"\']*\b'
        + re.escape(class_name)
        + r'\b[^"\']*["\'][^>]*>(.*?)</span>'
    )
    match = re.search(pattern, segment, re.S)
    if not match:
        return None

    text = re.sub(r'<[^>]+>', '', match.group(1))
    text = (
        text.replace('&nbsp;', ' ')
        .replace('&yen;', '¥')
        .replace('&amp;', '&')
        .replace('&#39;', "'")
        .replace('&quot;', '"')
    )
    return re.sub(r'\s+', ' ', text).strip() or None


def extract_rating(segment: str, class_name: str):
    """親span(例: p-link__txt--rank)の内側にある rating の値を返す。"""
    parent = extract_text(segment, class_name)
    if not parent:
        return None
    # 「ランク：中古品A」→「中古品A」、「サイズ：45-54cm」→「45-54cm」
    for prefix in ["ランク：", "サイズ：", "素材：", "在庫店舗：", "ランク:", "サイズ:", "素材:", "在庫店舗:"]:
        if parent.startswith(prefix):
            return parent[len(prefix):].strip()
    return parent


def extract_image_url(segment: str):
    match = re.search(r'<img[^>]+src="([^"]+)"', segment)
    if not match:
        match = re.search(r'<img[^>]+data-src="([^"]+)"', segment)
    if match:
        return urljoin(BASE_URL, match.group(1))
    return None


def parse_price(text):
    if not text:
        return None
    clean = (
        text.replace('￥', '')
        .replace('¥', '')
        .replace('円', '')
        .replace('税込', '')
        .replace('参考上代', '')
        .replace(':', '')
        .replace('：', '')
    )
    match = re.search(r'\d[\d,]*', clean)
    if not match:
        return None
    return int(match.group(0).replace(',', ''))


def iter_product_cards(html):
    for match in CARD_RE.finditer(html):
        product_id = match.group(1)
        start = match.end()
        end = html.find('</a>', start)
        if end == -1:
            end = len(html)
        yield html[start:end], product_id


def make_item(segment: str, product_id: str):
    fields = {
        key: extract_text(segment, class_name)
        for key, class_name in FIELD_CLASSES.items()
    }

    item = {
        "productId": str(product_id),
        "title": fields["title"],
        "brand": fields["brand"],
        "price": parse_price(fields["price"]),
        "referencePrice": parse_price(fields["reference"]),
        "rank": extract_rating(segment, "p-link__txt--rank"),
        "size": extract_rating(segment, "p-link__txt--size"),
        "material": extract_rating(segment, "p-link__txt--material"),
        "store": extract_rating(segment, "p-link__txt--store"),
        "imageUrl": extract_image_url(segment),
        "productUrl": f"{BASE_URL}product/{product_id}/",
        "scrapedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    if not item["title"]:
        return None
    return item


async def fetch_page(client, keyword: str, page: int, headers: dict):
    url = f"{SEARCH_URL}?{urlencode({'q': keyword, 'page': page})}"
    last_error = None

    for attempt in range(3):
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                html = response.text
                # デバッグ: HTMLサイズと商品カード数
                cards_count = len(list(iter_product_cards(html)))
                print(f"[DEBUG] page={page} status=200 size={len(html)} cards={cards_count}", flush=True)
                if cards_count == 0:
                    # 先頭500文字を出力して何が返っているか確認
                    preview = re.sub(r'\s+', ' ', html[:500])
                    print(f"[DEBUG] NO-CARDS preview: {preview[:400]}", flush=True)
                return html
            last_error = RuntimeError(f"Unexpected HTTP status {response.status_code}")
        except httpx.HTTPError as exc:
            last_error = exc

        await asyncio.sleep(min(2 ** attempt, 8) + random.uniform(0, 1))

    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


async def main():
    if Actor is not None:
        await Actor.init()

    results = []

    try:
        # Actor 環境では Apify の入力、ローカルでは stdin を使う。
        # ローカルに apify がインストール済みで get_input() が None を返す場合も stdin にフォールバックする。
        actor_input = await Actor.get_input() if Actor is not None else None
        if not actor_input:
            raw_input = sys.stdin.read()
            actor_input = json.loads(raw_input) if raw_input.strip() else {}

        keyword = str(actor_input.get("keyword") or "").strip()
        if not keyword:
            raise ValueError("keyword is required")

        max_items = int(actor_input.get("maxItems", 100))
        max_items = max(1, min(max_items, 500))

        proxy_url = None
        if Actor is not None:
            proxy_input = actor_input.get("proxyConfiguration")
            if proxy_input:
                # 重要: 引数名は actor_proxy_input= を使うこと。
                proxy_config = await Actor.create_proxy_configuration(
                    actor_proxy_input=proxy_input
                )
                if proxy_config:
                    proxy_url = await proxy_config.new_url()

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        }

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            proxy=proxy_url,
        ) as client:
            page = 1
            seen_ids = set()

            while len(results) < max_items and page <= MAX_PAGES:
                html = await fetch_page(client, keyword, page, headers)
                cards = list(iter_product_cards(html))

                if not cards:
                    break

                for segment, product_id in cards:
                    if len(results) >= max_items:
                        break
                    if product_id in seen_ids:
                        continue
                    seen_ids.add(product_id)

                    item = make_item(segment, product_id)
                    if not item:
                        continue

                    if Actor is not None:
                        await Actor.push_data(item)
                    else:
                        results.append(item)

                if len(cards) < 50:
                    break

                page += 1
                if len(results) < max_items and page <= MAX_PAGES:
                    await asyncio.sleep(random.uniform(1.0, 3.0))

        if Actor is None:
            print(json.dumps(results, ensure_ascii=False, indent=2))

    finally:
        if Actor is not None:
            await Actor.exit()


if __name__ == "__main__":
    asyncio.run(main())
