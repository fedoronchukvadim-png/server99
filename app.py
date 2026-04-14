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
        # Ждём первое сообщение с никнеймом
        msg = await ws.receive_json()
        
        if msg.get('type') == 'login':
            nickname = msg.get('nickname')
            if nickname:
                connected_websockets.add(ws)
                client_nicknames[ws] = nickname
                print(f"✅ {nickname} подключился | Всего: {len(connected_websockets)}")

                # Отправляем приветственное сообщение
                await ws.send_json({
                    'type': 'system',
                    'message': f"✨ Добро пожаловать, {nickname}!"
                })

                # Уведомляем всех остальных о новом пользователе
                await broadcast_to_others(ws, {
                    'type': 'system',
                    'message': f"{nickname} присоединился к чату 🎉"
                })

                # Основной цикл получения сообщений
                async for msg_json in ws:
                    data = json.loads(msg_json)
                    if data.get('type') == 'message':
                        # Рассылаем сообщение всем
                        await broadcast({
                            'type': 'message',
                            'nickname': nickname,
                            'message': data['message'],
                            'time': datetime.now().strftime("%H:%M")
                        })
                        print(f"💬 {nickname}: {data['message']}")

    except Exception as e:
        print(f"Ошибка в websocket_handler: {e}")
    finally:
        # Очистка при отключении
        if ws in connected_websockets:
            connected_websockets.remove(ws)
            if nickname:
                await broadcast({
                    'type': 'system',
                    'message': f"{nickname} покинул чат 👋"
                })
                print(f"📤 {nickname} отключился")

    return ws

async def broadcast(message, exclude=None):
    """Отправляет сообщение всем подключенным клиентам."""
    if not connected_websockets:
        return
    
    for ws in connected_websockets.copy():
        if ws != exclude:
            try:
                await ws.send_json(message)
            except:
                # Если отправить не удалось, клиент отключился
                if ws in connected_websockets:
                    connected_websockets.remove(ws)

async def broadcast_to_others(exclude_ws, message):
    """Отправляет сообщение всем, кроме указанного клиента."""
    await broadcast(message, exclude=exclude_ws)

async def health_check(request):
    """Проверка работоспособности сервера."""
    return web.Response(text="OK")

# Создаём приложение
app = web.Application()
app.router.add_get('/ws', websocket_handler)
app.router.add_get('/health', health_check)

# Настройка CORS
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
    print(f"🔗 WebSocket endpoint: /ws")
    print(f"❤️ Health check: /health")
    print("=" * 50)
    web.run_app(app, host='0.0.0.0', port=port)