import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group = f'chat_{self.room_name}'
        
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return
            
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '').strip()
        receiver_id = data.get('receiver_id')
        group_id = data.get('group_id')
        
        if not message:
            return
            
        user = self.scope['user']
        
        # Save to DB
        saved_msg = await self.save_message(user.id, message, receiver_id, group_id)
        
        # Broadcast
        await self.channel_layer.group_send(self.room_group, {
            'type': 'chat_message',
            'message': message,
            'sender_id': user.id,
            'sender_name': user.get_full_name() or user.username,
            'created_at': timezone.now().strftime('%H:%M'),
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'created_at': event['created_at'],
        }))

    @database_sync_to_async
    def save_message(self, sender_id, content, receiver_id=None, group_id=None):
        from apps.chat.models import Message
        from apps.accounts.models import User
        from apps.courses.models import Group
        
        msg = Message(sender_id=sender_id, content=content)
        if group_id:
            msg.group_id = group_id
            msg.msg_type = 'group'
        elif receiver_id:
            msg.receiver_id = receiver_id
            msg.msg_type = 'direct'
        
        msg.save()
        return msg
