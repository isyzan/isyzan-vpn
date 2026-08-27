#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Isyzan VPN - Автоматическое копирование подписки
Берёт серверы из популярных подписок и переименовывает в Isyzan
"""

import base64
import json
import re
import requests
import time
from datetime import datetime

# Список популярных подписок-источников
SOURCES = [
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub2.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/ts-sf/fly/main/v2",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
]

def fetch_subscription(url):
    """Скачивание подписки"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': '*/*'
        }
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return []
            
        content = response.text.strip()
        
        # Проверка на base64
        if re.match(r'^[A-Za-z0-9+/=]+$', content):
            try:
                decoded = base64.b64decode(content).decode('utf-8')
                content = decoded
            except:
                pass
                
        # Разбиваем на строки
        lines = content.split('\n')
        return [line.strip() for line in lines if line.strip().startswith(('vmess://', 'vless://', 'trojan://', 'ss://'))]
        
    except Exception:
        return []

def rename_to_isyzan(link, index):
    """Переименование сервера в Isyzan"""
    
    if link.startswith('vmess://'):
        # Декодируем VMess
        try:
            encoded = link.replace('vmess://', '')
            # Добавляем padding
            padding = '=' * (-len(encoded) % 4)
            decoded = base64.b64decode(encoded + padding).decode('utf-8')
            config = json.loads(decoded)
            
            # Переименовываем
            config['ps'] = f"Isyzan-{index:03d}"
            
            # Кодируем обратно
            new_json = json.dumps(config)
            new_encoded = base64.b64encode(new_json.encode()).decode().rstrip('=')
            return f"vmess://{new_encoded}"
        except:
            return None
    
    elif link.startswith('vless://'):
        # Добавляем имя в конец
        if '#' in link:
            # Убираем старое имя
            link = link.split('#')[0]
        return f"{link}#Isyzan-{index:03d}"
    
    elif link.startswith('trojan://'):
        # Добавляем имя в конец
        if '#' in link:
            link = link.split('#')[0]
        return f"{link}#Isyzan-{index:03d}"
    
    elif link.startswith('ss://'):
        # Добавляем имя в конец
        if '#' in link:
            link = link.split('#')[0]
        return f"{link}#Isyzan-{index:03d}"
    
    return None

def remove_duplicates(links):
    """Удаление дубликатов"""
    seen = set()
    unique = []
    
    for link in links:
        # Извлекаем IP и порт для проверки
        match = re.search(r'@([\d.]+):(\d+)', link)
        if match:
            key = f"{match.group(1)}:{match.group(2)}"
        else:
            # Для VMess пробуем декодировать
            try:
                encoded = link.replace('vmess://', '')
                padding = '=' * (-len(encoded) % 4)
                decoded = base64.b64decode(encoded + padding).decode('utf-8')
                config = json.loads(decoded)
                key = f"{config.get('add')}:{config.get('port')}"
            except:
                key = link[:50]
        
        if key not in seen:
            seen.add(key)
            unique.append(link)
    
    return unique

def main():
    print("=" * 60)
    print("ISYZAN VPN - СИНХРОНИЗАЦИЯ ПОДПИСОК")
    print("=" * 60)
    print()
    
    all_links = []
    
    # Скачиваем со всех источников
    for source in SOURCES:
        print(f"Скачивание: {source}")
        links = fetch_subscription(source)
        print(f"  Получено: {len(links)} серверов")
        all_links.extend(links)
        time.sleep(2)  # Пауза между запросами
    
    print()
    print(f"Всего получено: {len(all_links)} серверов")
    
    # Удаляем дубликаты
    unique_links = remove_duplicates(all_links)
    print(f"Уникальных: {len(unique_links)} серверов")
    
    # Переименовываем в Isyzan
    isyzan_links = []
    for i, link in enumerate(unique_links):
        renamed = rename_to_isyzan(link, i + 1)
        if renamed:
            isyzan_links.append(renamed)
    
    print(f"Переименовано: {len(isyzan_links)} серверов")
    print()
    
    # Сохраняем обычный список
    with open('subscription.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(isyzan_links))
    print("✓ Сохранено: subscription.txt")
    
    # Создаём base64 версию для HAPP
    content = '\n'.join(isyzan_links)
    encoded = base64.b64encode(content.encode()).decode()
    
    with open('happ_subscription.txt', 'w', encoding='utf-8') as f:
        f.write(encoded)
    print("✓ Сохранено: happ_subscription.txt")
    
    # Сохраняем статистику
    stats = {
        'updated_at': datetime.now().isoformat(),
        'total_servers': len(isyzan_links),
        'sources_checked': len(SOURCES),
        'protocols': {
            'vmess': sum(1 for l in isyzan_links if l.startswith('vmess://')),
            'vless': sum(1 for l in isyzan_links if l.startswith('vless://')),
            'trojan': sum(1 for l in isyzan_links if l.startswith('trojan://')),
            'shadowsocks': sum(1 for l in isyzan_links if l.startswith('ss://')),
        }
    }
    
    with open('stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=4, ensure_ascii=False)
    print("✓ Сохранено: stats.json")
    
    print()
    print("=" * 60)
    print("ИТОГИ")
    print("=" * 60)
    print(f"Серверов Isyzan: {len(isyzan_links)}")
    print(f"  VMess: {stats['protocols']['vmess']}")
    print(f"  VLESS: {stats['protocols']['vless']}")
    print(f"  Trojan: {stats['protocols']['trojan']}")
    print(f"  Shadowsocks: {stats['protocols']['shadowsocks']}")
    print()
    print("Ссылка для HAPP:")
    print("https://raw.githubusercontent.com/isyzan/isyzan-vpn/main/happ_subscription.txt")
    print()

if __name__ == '__main__':
    main()
