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
        action = data.get('action', 'send')
        user = self.scope['user']

        if action == 'send':
            message = data.get('message', '').strip()
            receiver_id = data.get('receiver_id')
            group_id = data.get('group_id')

            if not message:
                return

            receiver_id = receiver_id if receiver_id else None
            group_id = group_id if group_id else None

            saved_msg = await self.save_message(user.id, message, receiver_id, group_id)

            if receiver_id and not group_id:
                await self.create_chat_notification(user.id, receiver_id, message)
            elif group_id:
                await self.create_group_chat_notification(user.id, group_id, message)

            await self.channel_layer.group_send(self.room_group, {
                'type': 'chat_message',
                'action': 'send',
                'message': message,
                'msg_id': saved_msg.id,
                'sender_id': user.id,
                'sender_name': user.get_full_name() or user.username,
                'sender_initials': (user.first_name[:1] if user.first_name else user.username[:1]).upper(),
                'sender_avatar': user.avatar.url if user.avatar else None,
                'created_at': timezone.now().strftime('%H:%M'),
            })

        elif action == 'edit':
            msg_id = data.get('msg_id')
            new_content = data.get('content', '').strip()
            if not msg_id or not new_content:
                return
            success = await self.edit_message(user.id, msg_id, new_content)
            if success:
                await self.channel_layer.group_send(self.room_group, {
                    'type': 'chat_message',
                    'action': 'edit',
                    'msg_id': msg_id,
                    'content': new_content,
                    'sender_id': user.id,
                })

        elif action == 'delete':
            msg_id = data.get('msg_id')
            if not msg_id:
                return
            success = await self.delete_message(user.id, msg_id)
            if success:
                await self.channel_layer.group_send(self.room_group, {
                    'type': 'chat_message',
                    'action': 'delete',
                    'msg_id': msg_id,
                    'sender_id': user.id,
                })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    # =================== DB METHODS ===================

    @database_sync_to_async
    def save_message(self, sender_id, content, receiver_id=None, group_id=None):
        from apps.chat.models import Message

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
    def edit_message(self, sender_id, msg_id, new_content):
        from apps.chat.models import Message
        try:
            msg = Message.objects.get(id=msg_id, sender_id=sender_id, is_deleted=False)
            msg.content = new_content
            msg.save()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def delete_message(self, sender_id, msg_id):
        from apps.chat.models import Message
        try:
            msg = Message.objects.get(id=msg_id, sender_id=sender_id)
            msg.is_deleted = True
            msg.content = "Xabar o'chirildi"
            msg.save()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def create_chat_notification(self, sender_id, receiver_id, content):
        from apps.notifications.models import Notification
        from apps.accounts.models import User

        sender = User.objects.get(id=sender_id)
        Notification.objects.create(
            user_id=receiver_id,
            title=f"Yangi xabar (Shaxsiy): {sender.get_full_name() or sender.username}",
            body=content[:100] + ('...' if len(content) > 100 else ''),
            notif_type='chat_message',
            link=f"/chat/direct/{sender.id}/"
        )

    @database_sync_to_async
    def create_group_chat_notification(self, sender_id, group_id, content):
        from apps.notifications.models import Notification
        from apps.accounts.models import User
        from apps.courses.models import Group, Enrollment

        sender = User.objects.get(id=sender_id)
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return

        receivers = set()
        if group.teacher_id and group.teacher_id != sender_id:
            receivers.add(group.teacher_id)
        if group.assistant_id and group.assistant_id != sender_id:
            receivers.add(group.assistant_id)

        enrollments = Enrollment.objects.filter(group_id=group_id, status='approved')
        for enr in enrollments:
            if enr.student_id != sender_id:
                receivers.add(enr.student_id)

        notifs = []
        short_content = content[:100] + ('...' if len(content) > 100 else '')
        for rec_id in receivers:
            notifs.append(Notification(
                user_id=rec_id,
                title=f"Guruh xabari ({group.name}): {sender.get_full_name() or sender.username}",
                body=short_content,
                notif_type='chat_message',
                link=f"/chat/group/{group.id}/"
            ))
        if notifs:
            Notification.objects.bulk_create(notifs)
