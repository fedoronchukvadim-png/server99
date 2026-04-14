import asyncio
import json
import os
from datetime import datetime
from aiohttp import web
import aiohttp_cors

connected_websockets = set()
client_nicknames = {}

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    nickname = None
    try:
        msg = await ws.receive_json()
        if msg.get('type') == 'login':
            nickname = msg.get('nickname')
            if nickname:
                connected_websockets.add(ws)
                client_nicknames[ws] = nickname
                print(f"✅ {nickname} подключился | Всего: {len(connected_websockets)}")
                
                # Отправляем приветствие
                await ws.send_json({
                    'type': 'system',
                    'message': f"✨ Добро пожаловать, {nickname}!"
                })
                
                # Уведомляем остальных
                for other_ws in connected_websockets:
                    if other_ws != ws:
                        try:
                            await other_ws.send_json({
                                'type': 'system',
                                'message': f"{nickname} присоединился к чату 🎉"
                            })
                        except:
                            pass
                
                # Обрабатываем сообщения
                async for msg_json in ws:
                    data = json.loads(msg_json)
                    if data.get('type') == 'message':
                        for other_ws in connected_websockets:
                            try:
                                await other_ws.send_json({
                                    'type': 'message',
                                    'nickname': nickname,
                                    'message': data['message'],
                                    'time': datetime.now().strftime("%H:%M")
                                })
                            except:
                                pass
                        print(f"💬 {nickname}: {data['message']}")
    
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        if ws in connected_websockets:
            connected_websockets.remove(ws)
            if nickname:
                for other_ws in connected_websockets:
                    try:
                        await other_ws.send_json({
                            'type': 'system',
                            'message': f"{nickname} покинул чат 👋"
                        })
                    except:
                        pass
                print(f"📤 {nickname} отключился")
    
    return ws

async def health_check(request):
    return web.Response(text="OK")

app = web.Application()
app.router.add_get('/ws', websocket_handler)
app.router.add_get('/health', health_check)

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
        allow_methods="*"
    )
})
for route in app.router.routes():
    cors.add(route)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("=" * 50)
    print("   🚀 MODERN MESSENGER SERVER 🚀")
    print("=" * 50)
    print(f"✅ Сервер запущен на порту {port}")
    web.run_app(app, host='0.0.0.0', port=port)