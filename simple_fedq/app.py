import json
import ijson
import asyncio
import aiohttp
import urllib
from sanic import Sanic
from sanic import response
from sanic.response import text
from . import settings

app = Sanic(__name__)
app.config.from_object(settings)


async def stream_results(name, url, response, stream_state):
    limit = stream_state['limit']
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
            objects = data['results']
            # objects = aiojson.items(r.content, 'results.item')
            # async for obj in objects:

            async def iter_objects():
                for obj in objects:
                    yield obj

            async for obj in iter_objects():
                stream_state['total'] += 1
                if stream_state['total'] < stream_state['offset']:
                    continue
                if stream_state['count'] < limit:
                    if stream_state['count'] != 0:
                        response.write(',')
                    stream_state['count'] += 1
                    response.write(json.dumps(obj))


def merge_results(request, api_resource):
    pr = urllib.parse.urlparse(request.url)
    params = urllib.parse.parse_qs(pr.params)
    query = pr.query
    limit = int(params.get('limit', [100])[0])
    offset = int(params.get('offset', [0])[0])

    async def streaming_fn(response):
        loop = asyncio.get_event_loop()
        urls = []

        for name, endpoint in app.config.OMI_ENDPOINTS.items():
            url = urllib.parse.urljoin(endpoint, api_resource)
            # url = f"{url}/;limit={limit};offset={offset}?{query}"
            url = f"{url}/;limit={limit}?{query}"
            urls.append((name, url))

        response.write('{"results":[')
        stream_state = {
            'offset': offset,
            'limit': limit,
            'total': 0,
            'count': 0,
        }
        outcomes = await asyncio.gather(*(stream_results(name, url, response, stream_state) for name, url in urls))
        count = stream_state['count']
        total = stream_state['total']
        response.write('],"count":{},"total":{},"offset":{}'.format(count, total, offset))
        response.write('}')

    return response.stream(streaming_fn, content_type='application/json')


@app.route("/works/<other:.*>")
async def works(request, other):
    return merge_results(request, "works")


@app.route("/recordings/<other:.*>")
async def recordings(request, other):
    return merge_results(request, "recordings")
