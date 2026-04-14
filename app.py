import asyncio
import json
import os
from datetime import datetime
from aiohttp import web
import aiohttp_cors

# Хранилище для активных WebSocket-соединений
connected_websockets = set()
client_nicknames = {}

async def websocket_handler(request):
    """Обрабатывает входящие WebSocket-соединения."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    nickname = None
    try:
        # Получаем первый JSON с никнеймом
        msg = await ws.receive_json()
        if msg.get('type') == 'login':
            nickname = msg.get('nickname')
            if nickname:
                connected_websockets.add(ws)
                client_nicknames[ws] = nickname

                # Уведомляем всех о новом пользователе
                await broadcast({
                    'type': 'system',
                    'message': f"{nickname} присоединился к чату 🎉"
                })
                print(f"✅ {nickname} подключился | Всего: {len(connected_websockets)}")

                # Основной цикл получения сообщений от этого клиента
                async for msg_json in ws:
                    data = json.loads(msg_json)
                    if data.get('type') == 'message':
                        await broadcast({
                            'type': 'message',
                            'nickname': nickname,
                            'message': data['message'],
                            'time': datetime.now().strftime("%H:%M")
                        })
                        print(f"💬 {nickname}: {data['message']}")

    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        # Очистка при отключении клиента
        if ws in connected_websockets:
            connected_websockets.remove(ws)
            if nickname:
                await broadcast({
                    'type': 'system',
                    'message': f"{nickname} покинул чат 👋"
                })
                print(f"📤 {nickname} отключился")

    return ws

async def broadcast(message):
    """Отправляет сообщение всем подключенным клиентам."""
    if connected_websockets:
        for ws in connected_websockets.copy():
            try:
                await ws.send_json(message)
            except:
                # Если отправить не удалось, клиент, вероятно, отключился
                if ws in connected_websockets:
                    connected_websockets.remove(ws)

async def health_check(request):
    """Простой endpoint для проверки работоспособности сервера."""
    return web.Response(text="OK")

# Создаем основное приложение aiohttp
app = web.Application()
app.router.add_get('/ws', websocket_handler)  # <- ВАЖНО: путь /ws
app.router.add_get('/health', health_check)

# Настройка CORS (важно для браузерных клиентов)
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
    print("   🚀 MODERN MESSENGER (WORKING) 🚀")
    print("=" * 50)
    print(f"Сервер запущен на порту {port}")
    print(f"WebSocket endpoint: /ws")
    print(f"Health check: /health")
    web.run_app(app, host='0.0.0.0', port=port)