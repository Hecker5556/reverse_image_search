# Simple Reverse Image Search Script

Works with
* Bing
* Google
* Yandex

Automatically creates and saves cookies needed for bing and google

Utility function `sort_by_quality` that can be used to sort the images by quality.

Supports using a proxy for all connections

# Setup

1. in terminal

```bash
git pull https://github.com/hecker5556/reverse_image_search
```

2.

```bash
cd reverse_image_search
```

3.

```bash
pip install -r requirements.txt
```

# Usage

```python
import asyncio
from reverse_image_search import reverse_image_search
async def main():
    file = "image.png"
    proxy = "socks5://127.0.0.1:9050" # Optional
    engine = reverse_image_search()
    results = await engine.google(file, proxy=proxy)
    best = await engine.sort_by_quality(results)
asyncio.run(main())
```