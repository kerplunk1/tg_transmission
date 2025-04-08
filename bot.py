import requests
from transmission_rpc import Client
import re
import time
from os import environ


class Bot:
    def __init__(self, bot_token, user_id):
        self.user_id = user_id
        self.token = bot_token
        self.update_offset = None


    def get_updates(self):
        url = f"https://api.telegram.org/bot{self.token}/getUpdates"
        if self.update_offset is None:
            response = requests.get(url).json()['result']
        else:
            response = requests.get(url, params={'offset': self.update_offset}).json()['result']
        if response:
            for upd in response:
                self.update_offset = int(upd['update_id']) + 1    
            return response
        else:
            self.update_offset = None
            return None
        
    
    def send_answer(self, message_id, chat_id, text):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        params = {'reply_parameters': {'message_id': message_id}, 'chat_id': chat_id, 'text': text}
        requests.post(url, json=params)
    

    def get_file(self, document):
        if document is not None:
            if document['mime_type'] == 'application/x-bittorrent':
                path_url = f"https://api.telegram.org/bot{self.token}/getFile"
                params = {"file_id": document["file_id"]}
                file_path = requests.get(path_url, params=params).json()['result']['file_path']
                
                download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
                f = requests.get(download_url).content
                
                new_downloading = torrent_client.add_torrent(f)
                return f"{new_downloading.name}. The file has been added for download." 
            else:
                return 'Reject. Unknown file type.'
    
        
    def handle_updates(self, updates):
        if updates is not None:
            for upd in updates:
                message_id = upd['message']['message_id']
                chat_id = upd['message']['chat']['id']
                from_user_id = int(upd['message']['from']['id'])
                if self.user_id == from_user_id:

                    document = self.get_file(upd['message'].get('document'))
                    if document is not None:
                        self.send_answer(message_id, chat_id, document)
                        continue

                    text = upd['message']['text']
                    if text == 'list':
                        active_torrents = torrent_client.get_torrents()
                        info = []
                        for t in active_torrents:
                            info.append({'id': t.id, 'name': t.name, 'progress': t.progress})
                        self.send_answer(message_id, chat_id, str(info))

                    elif re.search(r'rm \d+', text):
                        rm = text.split()
                        torrent_client.remove_torrent(int(rm[1]))
                        self.send_answer(message_id, chat_id, f'A request to delete file with ID {rm[1]} has been sent.')

                    else:
                        self.send_answer(message_id, chat_id, 'Rejected. Unknown request.')
                else:
                    self.send_answer(message_id, chat_id, f'Reject. Permission denied. Restart app with user ID {from_user_id}.')


    def start(self):
        while True:
            updates = self.get_updates()
            self.handle_updates(updates)
            time.sleep(int(environ.get("UPDATE_TIME")))



torrent_client = Client(host=environ.get("TRANSMISSION_SERVER_IP"),
                        port=environ.get("TRANSMISSION_SERVER_PORT"),
                        username=environ.get("TRANSMISSION_SERVER_USER"),
                        password=environ.get("TRANSMISSION_SERVER_PASSWORD"))

bot = Bot(bot_token=environ.get("TELEGRAM_BOT_TOKEN"),
          user_id=int(environ.get("TELEGRAM_USER_ID")))
bot.start()

