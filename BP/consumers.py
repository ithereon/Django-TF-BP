from codecs import charmap_build
import json
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from .models import ChatMessage, Thread, AttorneyStaff, Firm, Attorney

User = get_user_model()




class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print('Connected', event)
        user = self.scope['user']
        chat_room = f'user_chatroom_{user.id}'
        self.chat_room = chat_room
        await self.channel_layer.group_add(
            chat_room,
            self.channel_name
        )
        await self.send({
            'type': 'websocket.accept'
        })

    async def websocket_receive(self, event):
        print('Received', event)
        received_data = json.loads(event['text'])
        msg = received_data.get('message')
        sent_by_id = received_data.get('sent_by')
        send_to_id = received_data.get('send_to')
        thread_id = received_data.get('thread_id')

        if not msg:
            print('Error:: empty message!')
            return False
        
        sent_by_user = await self.get_user_object(sent_by_id)
        send_to_user = await self.get_user_object(send_to_id)
        thread_obj = await self.get_thread(thread_id)
        if not sent_by_user:
            print('Sent by user is not correct!')
        if not send_to_user:
            print('Send to user is not correct!')
        if not thread_obj:
            print('Thread is not correct!')

        print(sent_by_user)
        await self.create_chat_message(thread_obj, sent_by_user, msg)
        other_user_chat_room = f'user_chatroom_{send_to_id}'
        print(other_user_chat_room)
        self_user = self.scope['user']

        thread_user = await self.get_thread_user(sent_by_user)
        
        
        response = {
            'message': msg,
            'sent_by': thread_user.id,
            'thread_id': thread_id,
            'sender_name': self_user.username,
        }

        await self.channel_layer.group_send(
            other_user_chat_room,
            {
                'type': 'chat_message',
                'text': json.dumps(response)
            }
        )

        await self.channel_layer.group_send(
            self.chat_room,
            {
                'type': 'chat_message',
                'text': json.dumps(response)
            }
        )
        
    async def websocket_disconnect(self, event):
        print('Disconnected', event)

    @database_sync_to_async
    def get_user_object(self, user_id):
        qs = User.objects.filter(id=int(user_id))
        if qs.exists():
            obj = qs.first()
        else:
            obj = None
        return obj
    
    @database_sync_to_async
    def get_thread(self, thread_id):
        qs = Thread.objects.filter(id=int(thread_id))
        if qs.exists():
            obj = qs.first()
        else:
            obj = None
        return obj

    @database_sync_to_async
    def create_chat_message(self, thread, user, msg):
        sender_name = user.username
        if thread.first_person != user and thread.second_person != user:
            attorney_staff = AttorneyStaff.objects.get(user=user)
            user = attorney_staff.created_by.attorneyprofile.user
        qs = ChatMessage.objects.create(thread=thread, user=user, message=msg, sender_name=sender_name)
        qs.save()
    
    @database_sync_to_async
    def get_thread_user(self, sent_by_user):
        profile = None
        userprofile = None
        thread_user = None
        try:
            profile = Firm.objects.get(user=sent_by_user, account_type='Attorney')
            userprofile = Attorney.objects.get(attorneyprofile=profile)
            thread_user = userprofile.attorneyprofile.user
        except:
            try:
                userprofile = AttorneyStaff.objects.get(user=sent_by_user, account_type='AttorneyStaff')
                print('Hello Im attorney')
                userprofile = userprofile.created_by
                thread_user = userprofile.attorneyprofile.user
                print(thread_user.id)
            except:
                thread_user = sent_by_user
                print('Hello Im Client')
        return sent_by_user
        

    async def chat_message(self, event):
        print('chat_message', event)
        await self.send({
            'type': 'websocket.send',
            'text': event['text']
        })
        