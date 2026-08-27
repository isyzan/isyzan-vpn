#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Isyzan VPN - Автоматическое обновление подписки
Берёт серверы из популярных подписок и переименовывает в Isyzan
"""

import requests
import base64
import json
import re
import random
from datetime import datetime
from urllib.parse import urlparse, unquote

# Источники популярных подписок
SOURCES = [
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub2.txt",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/ripaojiedian/freenode/main/sub",
]

def fetch_subscription(url):
    """Скачивание подписки"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"Ошибка {url}: {e}")
    return None

def decode_base64(data):
    """Декодирование base64"""
    try:
        # Добавляем padding если нужно
        padding = 4 - len(data) % 4
        if padding != 4:
            data += '=' * padding
        return base64.b64decode(data).decode('utf-8', errors='ignore')
    except:
        return data

def parse_vmess(uri):
    """Парсинг VMess ссылки"""
    try:
        encoded = uri.replace('vmess://', '')
        decoded = decode_base64(encoded)
        config = json.loads(decoded)
        return {
            'protocol': 'vmess',
            'address': config.get('add', ''),
            'port': config.get('port', '443'),
            'uuid': config.get('id', ''),
            'aid': config.get('aid', '0'),
            'network': config.get('net', 'ws'),
            'path': config.get('path', '/'),
            'host': config.get('host', ''),
            'tls': config.get('tls', 'none'),
            'sni': config.get('sni', config.get('host', ''))
        }
    except:
        return None

def parse_vless(uri):
    """Парсинг VLESS ссылки"""
    try:
        parsed = urlparse(uri)
        uuid = parsed.netloc.split('@')[0]
        server = parsed.netloc.split('@')[1]
        address = server.split(':')[0]
        port = server.split(':')[1]
        
        params = {}
        for p in parsed.query.split('&'):
            if '=' in p:
                key, value = p.split('=', 1)
                params[key] = unquote(value)
        
        return {
            'protocol': 'vless',
            'address': address,
            'port': port,
            'uuid': uuid,
            'network': params.get('type', 'tcp'),
            'security': params.get('security', 'none'),
            'sni': params.get('sni', ''),
            'path': params.get('path', '/'),
            'host': params.get('host', '')
        }
    except:
        return None

def parse_trojan(uri):
    """Парсинг Trojan ссылки"""
    try:
        parsed = urlparse(uri)
        password = parsed.netloc.split('@')[0]
        server = parsed.netloc.split('@')[1]
        address = server.split(':')[0]
        port = server.split(':')[1]
        
        params = {}
        for p in parsed.query.split('&'):
            if '=' in p:
                key, value = p.split('=', 1)
                params[key] = unquote(value)
        
        return {
            'protocol': 'trojan',
            'address': address,
            'port': port,
            'password': password,
            'sni': params.get('sni', '')
        }
    except:
        return None

def rename_to_isyzan(server, index):
    """Переименование сервера в Isyzan"""
    city = server.get('address', 'Unknown')[:8]
    server['name'] = f"Isyzan-{index:03d}"
    return server

def generate_vmess_link(server):
    """Генерация VMess ссылки с именем Isyzan"""
    config = {
        "v": "2",
        "ps": server['name'],
        "add": server['address'],
        "port": str(server['port']),
        "id": server['uuid'],
        "aid": str(server.get('aid', '0')),
        "scy": "auto",
        "net": server.get('network', 'ws'),
        "type": "none",
        "host": server.get('host', 'www.google.com'),
        "path": server.get('path', '/'),
        "tls": server.get('tls', 'tls'),
        "sni": server.get('sni', 'www.google.com')
    }
    json_str = json.dumps(config)
    encoded = base64.b64encode(json_str.encode()).decode().rstrip('=')
    return f"vmess://{encoded}"

def generate_vless_link(server):
    """Генерация VLESS ссылки с именем Isyzan"""
    return (
        f"vless://{server['uuid']}@{server['address']}:{server['port']}"
        f"?type={server.get('network', 'ws')}"
        f"&security={server.get('security', 'tls')}"
        f"&sni={server.get('sni', 'www.microsoft.com')}"
        f"&path={server.get('path', '/')}"
        f"&host={server.get('host', 'www.microsoft.com')}"
        f"#{server['name']}"
    )

def generate_trojan_link(server):
    """Генерация Trojan ссылки с именем Isyzan"""
    return (
        f"trojan://{server['password']}@{server['address']}:{server['port']}"
        f"?sni={server.get('sni', 'www.google.com')}"
        f"&type=ws"
        f"&host={server.get('sni', 'www.google.com')}"
        f"&path=/ws/stream"
        f"#{server['name']}"
    )

def main():
    print("=" * 60)
    print("ISYZAN VPN - АВТООБНОВЛЕНИЕ ПОДПИСКИ")
    print(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    all_servers = []
    
    # Скачивание со всех источников
    for source in SOURCES:
        print(f"Скачивание: {source}")
        data = fetch_subscription(source)
        
        if not data:
            print(f"  ❌ Ошибка")
            continue
        
        # Декодирование base64
        decoded = decode_base64(data.strip())
        
        # Парсинг каждой строки
        count = 0
        for line in decoded.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            server = None
            if line.startswith('vmess://'):
                server = parse_vmess(line)
            elif line.startswith('vless://'):
                server = parse_vless(line)
            elif line.startswith('trojan://'):
                server = parse_trojan(line)
            
            if server:
                all_servers.append(server)
                count += 1
        
        print(f"  ✓ Получено {count} серверов")
    
    print()
    print(f"Всего собрано: {len(all_servers)} серверов")
    
    # Удаление дубликатов
    seen = set()
    unique_servers = []
    for server in all_servers:
        key = f"{server['address']}:{server['port']}"
        if key not in seen:
            seen.add(key)
            unique_servers.append(server)
    
    print(f"Уникальных: {len(unique_servers)}")
    
    # Ограничение до 150 серверов
    if len(unique_servers) > 150:
        unique_servers = random.sample(unique_servers, 150)
        print(f"Выбрано случайно: 150")
    
    # Переименование в Isyzan
    final_links = []
    for i, server in enumerate(unique_servers, 1):
        server = rename_to_isyzan(server, i)
        
        if server['protocol'] == 'vmess':
            final_links.append(generate_vmess_link(server))
        elif server['protocol'] == 'vless':
            final_links.append(generate_vless_link(server))
        elif server['protocol'] == 'trojan':
            final_links.append(generate_trojan_link(server))
    
    # Сохранение обычного файла
    with open('subscription.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_links))
    
    # Сохранение base64 для HAPP
    content = '\n'.join(final_links)
    encoded_content = base64.b64encode(content.encode()).decode()
    
    with open('happ_subscription.txt', 'w', encoding='utf-8') as f:
        f.write(encoded_content)
    
    # Сохранение JSON
    with open('servers.json', 'w', encoding='utf-8') as f:
        json.dump(unique_servers, f, indent=4, ensure_ascii=False)
    
    print()
    print("=" * 60)
    print("ГОТОВО!")
    print("=" * 60)
    print(f"Серверов: {len(final_links)}")
    print(f"Файлы обновлены: {datetime.now().strftime('%H:%M:%S')}")
    print()
    print("Ссылка для HAPP:")
    print("https://raw.githubusercontent.com/isyzan/isyzan-vpn/main/happ_subscription.txt")

if __name__ == '__main__':
    main()
