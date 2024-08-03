import aiohttp, re, os, json
from io import BufferedReader
from io import BytesIO
from PIL import Image
from aiohttp_socks import ProxyConnector
from datetime import datetime, timedelta
from html import unescape
from base64 import b64encode
class reverse_image_search:
    def __init__(self) -> None:
        self.proxy = None
        self._proxy = None
    def _give_connector(self, proxy):
        return ProxyConnector.from_url(proxy) if proxy and proxy.startswith("socks") else aiohttp.TCPConnector()
    async def sort_by_quality(self, results: dict):
        """
        Sorts results based on resolution, descending order
        """
        if not list(results.values())[0].get('width'):
            async with aiohttp.ClientSession(connector=self._give_connector(self._proxy)) as session:
                for key, value in results.copy().items():
                    async with session.get(value.get('url'), proxy=self.proxy) as r:
                        if r.status not in [200, 204]:
                            results.pop(key)
                            continue
                        try:
                            byts = await r.content.read()
                            img = Image.open(BytesIO(byts))
                        except Exception as e:
                            results.pop(key)
                            continue
                        results[key]['width'] = img.width
                        results[key]['height'] = img.height
        topkeys = sorted(results.keys(), key=lambda x: results[x].get('width') * results[x].get('height'), reverse=True)
        return [{key: results[key]} for key in topkeys]

    async def _get_SOCS(self, session: aiohttp.ClientSession):
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.7',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Not)A;Brand";v="99", "Brave";v="127", "Chromium";v="127"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        }

        async with session.get("https://google.com", headers=headers, proxy=self.proxy) as r:
            rtext = await r.text("utf-8")
            sCASpattern = r"sCAS=\'(.*?)\';"
            SOCS = re.search(sCASpattern, rtext).group(1)
            with open("cookie_google", "w") as f1:
                f1.write(f"{SOCS}\t{(datetime.now() + timedelta(days=13*30)).isoformat()}")
            return SOCS
    async def _get_MMCASM(self, session: aiohttp.ClientSession):
        async with session.get("https://www.bing.com/images", proxy=self.proxy) as r:
            with open("cookie_bing.json", "w") as f1:
                MMCASM = session.cookie_jar.filter_cookies('https://bing.com').get('MMCASM').value
                rtext = await r.text("utf-8")
                skey = re.search(r"skey=(.*?)\\u002", rtext).group(1)
                json.dump({"skey": skey, "mmcasm": {"cookie": MMCASM, "expiry": (datetime.now() + timedelta(days=385)).isoformat()}}, f1)

            return MMCASM, skey
    async def bing(self, image: str | bytes | BufferedReader, proxy: str = None):
        """
        Args:
            image (str | bytes | io.BufferedReader) - url, path, bytes or buffered reader
            proxy (str) - https/socks proxy to use
        Returns:
            dict: "title": {"source": "source website", "url": "direct image link", "width": width_int, "height": height_int}
        """
        self.proxy = proxy if proxy and proxy.startswith("http") else None
        self._proxy = proxy
        async with aiohttp.ClientSession(connector=self._give_connector(proxy)) as session:
            if not os.path.exists("cookie_bing.json"):
                MMCASM, skey = await self._get_MMCASM(session)
            else:
                with open("cookie_bing.json", "r") as f1:
                    try:
                        cookie_bing = json.load(f1)
                    except:
                        cookie_bing = None
                    if not cookie_bing or datetime.now() > datetime.fromisoformat(cookie_bing['mmcasm']['expiry']):
                        MMCASM, skey = await self._get_MMCASM(session)
                    else:
                        MMCASM = cookie_bing['mmcasm'].get('cookie')
                        skey = cookie_bing['skey']
            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.5',
                'origin': 'https://www.bing.com',
                'cookie': f'MMCASM={MMCASM}',
                'priority': 'u=1, i',
                'sec-ch-ua': '"Not)A;Brand";v="99", "Brave";v="127", "Chromium";v="127"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-model': '""',
                'sec-ch-ua-platform': '"Windows"',
                'sec-ch-ua-platform-version': '"10.0.0"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'sec-gpc': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
            }
            params = {
                'skey': skey,
                'safeSearch': 'Off',
                'setLang': 'en-us',
            }
            req = {"imageInfo":None,"knowledgeRequest":{"invokedSkills":["ImageById","BestRepresentativeQuery","Offline","ObjectDetection","OCR","EntityLinkingFace","EntityLinkingDog","EntityLinkingAnimal","EntityLinkingPlant","EntityLinkingLandmark","EntityLinkingFood","EntityLinkingBook","SimilarImages","RelatedSearches","PagesIncluding","TextAds","ProductAds","SponsoredAds","Annotation","Recipes","Travel","PrismFeed"],"invokedSkillsRequestData":{"adsRequest":{"textRequest":{"mainlineAdsMaxCount":2}}},"index":1}}
            upload = False
            if isinstance(image, str) and not os.path.exists(image) and image.startswith("http"):
                req['imageInfo'] = {"url":image,"source":"Url"}
            elif isinstance(image, str) and os.path.exists(image):
                img = open(image, 'rb')
                upload = True
            elif isinstance(image, BufferedReader):
                img = image
                upload = True
            elif isinstance(image, bytes):
                img = BytesIO(image)
                upload = True
            else:
                raise ValueError("not a proper image")
            if upload:
                params2 = {'view': 'detailv2', 'iss': 'sbiupload', 'FORM': 'SBIIRP', 'sbisrc': 'ImgDropper', 'idpbck': '1', }
                data = aiohttp.FormData()
                data.add_field(name="imgurl", value="")
                data.add_field("cbir","sbi")
                data.add_field("imageBin", b64encode(img.read()))
                headers2 = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'accept-language': 'en-US,en;q=0.5',
                    'cache-control': 'max-age=0',
                    'origin': 'https://www.bing.com',
                    'priority': 'u=0, i',
                    'sec-ch-ua': '"Not)A;Brand";v="99", "Brave";v="127", "Chromium";v="127"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-model': '""',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-ch-ua-platform-version': '"10.0.0"',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'same-origin',
                    'sec-fetch-user': '?1',
                    'sec-gpc': '1',
                    'upgrade-insecure-requests': '1',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                }
                async with session.post("https://www.bing.com/images/search", params=params2, headers=headers2, data=data, proxy=self.proxy, allow_redirects=False) as r:
                    insightsToken = re.search(r"insightsToken=(.*?)&", r.headers.get("location")).group(1)
                    req['imageInfo'] = {"imageInsightsToken":insightsToken,"source":"Gallery"}
            data = aiohttp.FormData()
            data.add_field(
                'knowledgeRequest',
                value=json.dumps(req),
                content_type='application/json'
            )
            async with session.post('https://www.bing.com/images/api/custom/knowledge', headers=headers, data=data, params=params, proxy=self.proxy) as r:
                response = await r.json()
            check = [
                "PagesIncluding",
                "VisualSearch",
            ]
            results = {}
            for i in response['tags'][0]['actions']:
                if i['actionType'] in check:
                    for j in i['data']['value']:
                        results[j['name']] = {'width': j['width'], 'height': j['height'], 'url': j['contentUrl'], 'source': j['hostPageUrl']}
            return results
    async def yandex(self, image: str | bytes | BufferedReader, proxy: str = None):
        """
        Args:
            image (str | bytes | io.BufferedReader) - url, path, bytes or buffered reader
            proxy (str) - https/socks proxy to use
        Returns:
            dict: "title": {"source": "source website", "url": "direct image link", "width": width_int, "height": height_int}
        """
        self.proxy = proxy if proxy and proxy.startswith("http") else None
        self._proxy = proxy
        async with aiohttp.ClientSession(connector=self._give_connector(proxy)) as session:
            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.8',
                'priority': 'u=1, i',
                'sec-ch-ua': '"Not)A;Brand";v="99", "Brave";v="127", "Chromium";v="127"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-model': '""',
                'sec-ch-ua-platform': '"Windows"',
                'sec-ch-ua-platform-version': '"10.0.0"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'sec-gpc': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
            }
            params = {
                'images_avatars_size': 'preview',
                'images_avatars_namespace': 'images-cbir',
            }
            uploading = False
            if isinstance(image, str) and not os.path.exists(image) and image.startswith("http"):
                params['url'] = image
            elif isinstance(image, str) and os.path.exists(image):
                data = open(image, 'rb')
                uploading = True
            elif isinstance(image, BufferedReader):
                data = image
                uploading = True
            elif isinstance(image, bytes):
                data = BytesIO(image)
                uploading = True
            else:
                raise ValueError("not a proper image")
            if uploading:
                async with session.post('https://yandex.com/images-apphost/image-download', params=params, headers=headers, data=data, proxy=self.proxy) as r:
                    response = await r.json()
            else:
                async with session.get('https://yandex.com/images-apphost/image-download', params=params, headers=headers, proxy=self.proxy) as r:
                    response = await r.json()
            req = {"blocks":[{"block":"extra-content","params":{},"version":2},{"block":"i-global__params:ajax","params":{},"version":2},{"block":"serp-controller","params":{},"version":2},{"block":"cbir-page-layout__main-content:ajax","params":{"pageType":"similar"},"version":2}],"metadata":{"bundles":{"lb":"N0/p96}.6Zk+Nw}"},"assets":{"las":"justifier-vertical2=1;justifier-height=1;justifier-setheight=1;fitimages-height=1;justifier-fitincuts=1;react-with-dom=1;367.0=1;119.0=1;383.0=1;295.0=1;303.0=1;231.0=1;cab507.0=1;00c2c3.0=1;4ac185.0=1;c3940d.0=1;c11d35.0=1;ced0b7.0=1;143.0=1;2af8f7.0=1;103.0=1;9261a8.0=1;159.0=1;135.0=1;375.0=1;399.0=1;f4c8df.0=1;4f2872.0=1;8978a4.0=1;07f7ab.0=1"},"extraContent":{"names":["i-react-ajax-adapter"]}}}
            params = {
                'cbir_id': response['cbir_id'],
                'rpt': 'imageview',
                'url': response['sizes']['orig']['path'],
                'format': 'json',
                'request': json.dumps(req),
                'cbir_page': 'similar'
            }
            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'en-US,en;q=0.8',
                'priority': 'u=1, i',
                'sec-ch-ua': '"Not)A;Brand";v="99", "Brave";v="127", "Chromium";v="127"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-model': '""',
                'sec-ch-ua-platform': '"Windows"',
                'sec-ch-ua-platform-version': '"10.0.0"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'sec-gpc': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
            }
            async with session.get(
                'https://yandex.com/images/search',
                params=params,
                headers=headers,
                proxy=self.proxy
            ) as r:
                response = await r.json()
            data_pattern = r"data-bem='(\{\"serp-item\":(?:.*?)\}\})'"
            resp = response['blocks'][3]['html']
            matches = re.findall(data_pattern, resp)
            results = {}
            for i in matches:
                the = json.loads(i)['serp-item']
                title = the['snippet']['title']
                source = the['snippet']['url']
                url = unescape(the['preview'][0]['url'])
                width, height = the['preview'][0]['w'], the['preview'][0]['h']
                results[title] = {"source": source, "url": url, "width": width, "height": height}
            return results
            
    async def google(self, image: str | bytes | BufferedReader = None, region: str = None, proxy: str = None):
        """
        Args:
            image (str | bytes | io.BufferedReader) - url, path, bytes or buffered reader
            region (str) - region shortcode (eg. us, pl, uk)
            proxy (str) - https/socks proxy to use
        Returns:
            dict: "title": {"source": "source website", "url": "direct image link"}
        """
        self.proxy = proxy if proxy and proxy.startswith("http") else None
        self._proxy = proxy
        async with aiohttp.ClientSession(connector=self._give_connector(proxy)) as session:
            if not os.path.exists("cookie_google"):
                SOCS = await self._get_SOCS(session)
            else:
                with open("cookie_google", "r") as f1:
                    try:
                        if len(f1.read().split('\t')) != 2 or datetime.now() > datetime.fromisoformat(f1.read().split('\t')[1]):
                            SOCS = await self._get_SOCS(session)
                        else:
                            SOCS = f1.read().split('\t')[0]
                    except:
                        SOCS = await self._get_SOCS(session)
            cookies = {
                "SOCS": SOCS
            }
            headers = {
                'authority': 'lens.google.com',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US,en;q=0.5',
                'cache-control': 'max-age=0',
                'origin': 'https://www.google.com',
                'referer': 'https://www.google.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            }
            params = {
                're': 'df',
                'st': '1708446151722',
                'vpw': '879',
                'vph': '751',
                'ep': 'gsbubb',
            }
            if region:
                params['hl'] = region
            upload = False
            if isinstance(image, str) and image.startswith('https'):
                params['url'] = image
            elif isinstance(image, str) and os.path.exists(image):
                filename = image
                temp = Image.open(image)
                width, height = temp.size
                imgformat = temp.format.lower()
                image = open(image, 'rb')
                upload = True
            elif isinstance(image, bytes):
                image = BytesIO(image)
                temp = Image.open(image)
                width, height = temp.size
                imgformat = temp.format.lower()
                filename = f"image.{imgformat}"
                image.seek(0)
                upload = True
            elif isinstance(image, BufferedReader):
                temp = Image.open(image)
                width, height = temp.size
                imgformat = temp.format.lower()
                image.seek(0)
                filename = image.name
                upload = True
            else:
                raise ValueError("not a proper image")
            if upload:
                data = aiohttp.FormData()
                data.add_field("encoded_image", image, content_type=f"image/{imgformat}", filename=filename)
                data.add_field("processed_image_dimensions", f"{width},{height}")
                async with session.post("https://lens.google.com/v3/upload", headers=headers, cookies=cookies, params=params, data=data) as r:
                    rtext = await r.text(encoding="utf-8")
                temp.close()
            else:
                async with session.get('https://lens.google.com/uploadbyurl', headers=headers, cookies=cookies, params=params) as r:
                    rtext = await r.text(encoding="utf-8")
            results = {}
            pattern = r"url=\"(.*?)\" data-item-title=\"(.*?)\" jslog=\"(?:.*?)\" data-action-url=(.*?) data-dacl=\"true\""
            for i, j, k in re.findall(pattern, rtext):
                i, j, k = unescape(i), unescape(j), unescape(k)
                results[j] = {'url': i, 'source': k}
        return results