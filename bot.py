import asyncio
from aiohttp import web

async def health(request):
    return web.Response(text="OK")

async def control(request):
    return web.FileResponse('control.html')

app = web.Application()
app.router.add_get('/', health)
app.router.add_get('/control.html', control)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=10000)
