import os
import requests
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Отправляет файл базы данных SQLite в личные сообщения ВК'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Путь к файлу БД (по умолчанию db.sqlite3)')

    def handle(self, *args, **options):
        file_path = options['file'] or 'db.sqlite3'
        
        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f'Файл не найден: {file_path}'))
            return

        # 1. Получаем адрес для загрузки документа в сообщения
        self.stdout.write('Получаем адрес для загрузки...')
        upload_server_response = self._vk_api(
            'docs.getMessagesUploadServer',
            {'peer_id': settings.VK_OWNER_ID, 'type': 'doc'}
        )
        
        if 'error' in upload_server_response:
            self.stderr.write(self.style.ERROR(f"Ошибка получения адреса: {upload_server_response['error']}"))
            return
            
        upload_url = upload_server_response['response']['upload_url']

        # 2. Загружаем файл на сервер ВК
        self.stdout.write(f'Загружаем файл {file_path}...')
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            upload_response = requests.post(upload_url, files=files)
            upload_data = upload_response.json()

        if 'file' not in upload_data:
            self.stderr.write(self.style.ERROR(f"Ошибка загрузки файла: {upload_data}"))
            return

        # 3. Сохраняем документ и получаем его ID
        self.stdout.write('Сохраняем документ...')
        save_response = self._vk_api(
            'docs.save',
            {'file': upload_data['file'], 'title': 'backup.sqlite3'}
        )
        
        if 'error' in save_response:
            self.stderr.write(self.style.ERROR(f"Ошибка сохранения: {save_response['error']}"))
            return

        doc = save_response['response']['doc']
        attachment = f"doc{doc['owner_id']}_{doc['id']}"

        # 4. Отправляем сообщение с прикреплённым файлом
        self.stdout.write('Отправляем сообщение...')
        message_response = self._vk_api(
            'messages.send',
            {
                'user_id': settings.VK_OWNER_ID,
                'message': '📦 Резервная копия базы данных',
                'attachment': attachment,
                'random_id': 0
            }
        )
        
        if 'error' in message_response:
            self.stderr.write(self.style.ERROR(f"Ошибка отправки сообщения: {message_response['error']}"))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Резервная копия успешно отправлена в ВК!'))

    def _vk_api(self, method, params):
        """Вспомогательный метод для вызова VK API."""
        params['access_token'] = settings.VK_GROUP_TOKEN
        params['v'] = '5.199'
        response = requests.get(f'https://api.vk.com/method/{method}', params=params)
        return response.json()