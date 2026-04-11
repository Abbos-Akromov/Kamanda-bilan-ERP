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
        
        # Convert empty strings to None
        receiver_id = receiver_id if receiver_id else None
        group_id = group_id if group_id else None
        
        # Save to DB
        saved_msg = await self.save_message(user.id, message, receiver_id, group_id)
        
        # Create notification for Direct Messages
        if receiver_id and not group_id:
            await self.create_chat_notification(user.id, receiver_id, message)
            
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
            try:
                msg.receiver_id = int(receiver_id)
            except (ValueError, TypeError):
                msg.receiver_id = None
            msg.msg_type = 'direct'
        
        msg.save()
        return msg

    @database_sync_to_async
    def create_chat_notification(self, sender_id, receiver_id, content):
        from apps.notifications.models import Notification
        from apps.accounts.models import User
        
        sender = User.objects.get(id=sender_id)
        Notification.objects.create(
            user_id=receiver_id,
            title=f"Yangi xabar: {sender.get_full_name() or sender.username}",
            body=content[:100] + ('...' if len(content) > 100 else ''),
            notif_type='chat_message',
            link=f"/chat/user/{sender_id}/"
        )
