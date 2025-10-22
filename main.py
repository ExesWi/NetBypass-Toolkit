"""
NetBypass Toolkit - Интеллектуальный обход сетевых ограничений
Автор: Ex
Версия: 1.0
"""

import requests
import threading
import time
import random
import json
import argparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NetBypass:
    def __init__(self, config_file="netbar_config.json"):
        self.results = {}
        self.lock = threading.Lock()
        self.stats = {
            'attempts': 0,
            'success': 0,
            'failed': 0
        }

        self.config = self.load_config(config_file)

        self.user_agents = self.config.get('user_agents', [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)',
        ])

        self.proxies = self.config.get('proxies', [])

    def load_config(self, config_file):
        default_config = {
            "user_agents": [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)',
            ],
            "proxies": [],
            "timeout_settings": {
                "direct": 5,
                "stealth": 10,
                "chunked": 15,
                "retry": 10
            },
            "retry_settings": {
                "max_retries": 3,
                "base_delay": 1
            }
        }

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"✅ Конфигурация загружена из {config_file}")
                return {**default_config, **config}
            except Exception as e:
                logger.warning(f"❌ Ошибка загрузки конфига: {e}")
                return default_config
        else:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            logger.info(f"📝 Создан файл конфигурации: {config_file}")
            return default_config

    def _update_stats(self, success=True):
        with self.lock:
            self.stats['attempts'] += 1
            if success:
                self.stats['success'] += 1
            else:
                self.stats['failed'] += 1

    def method_direct(self, url, timeout=None):
        if timeout is None:
            timeout = self.config['timeout_settings'].get('direct', 5)

        try:
            logger.info(f"📡 Прямое подключение к {url}")
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                logger.info("✅ Прямое подключение успешно")
                self._update_stats(True)
                return response.text
        except Exception as e:
            logger.warning(f"❌ Прямое подключение: {str(e)[:30]}...")
            self._update_stats(False)
        return None

    def method_stealth(self, url, timeout=None):
        if timeout is None:
            timeout = self.config['timeout_settings'].get('stealth', 10)

        try:
            logger.info(f"🕵‍♂ Скрытое подключение к {url}")
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                logger.info("✅ Скрытое подключение успешно")
                self._update_stats(True)
                return response.text
        except Exception as e:
            logger.warning(f"❌ Скрытое подключение: {str(e)[:30]}...")
            self._update_stats(False)
        return None

    def method_chunked(self, url, timeout=None):
        if timeout is None:
            timeout = self.config['timeout_settings'].get('chunked', 15)

        try:
            logger.info(f"🐌 Медленная загрузка {url}")
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)

            if response.status_code == 200:
                content = ""
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        try:
                            content += chunk.decode('utf-8', errors='ignore')
                        except:
                            pass
                        time.sleep(0.01)

                logger.info("✅ Медленная загрузка успешна")
                self._update_stats(True)
                return content
        except Exception as e:
            logger.warning(f"❌ Медленная загрузка: {str(e)[:30]}...")
            self._update_stats(False)
        return None

    def method_proxy(self, url, timeout=None):
        if timeout is None:
            timeout = self.config['timeout_settings'].get('proxy', 15)

        if not self.proxies:
            logger.info("⏭  Пропуск метода прокси - нет прокси в конфиге")
            return None

        try:
            logger.info(f"🌐 Подключение через прокси к {url}")
            proxy = random.choice(self.proxies)
            proxies_dict = {
                'http': proxy,
                'https': proxy
            }

            headers = {'User-Agent': random.choice(self.user_agents)}
            response = requests.get(url, headers=headers, proxies=proxies_dict, timeout=timeout)

            if response.status_code == 200:
                logger.info("✅ Подключение через прокси успешно")
                self._update_stats(True)
                return response.text
        except Exception as e:
            logger.warning(f"❌ Подключение через прокси: {str(e)[:30]}...")
            self._update_stats(False)
        return None

    def method_retry(self, url, timeout=None):
        if timeout is None:
            timeout = self.config['timeout_settings'].get('retry', 10)

        max_retries = self.config['retry_settings'].get('max_retries', 3)
        base_delay = self.config['retry_settings'].get('base_delay', 1)

        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Попытка {attempt + 1}/{max_retries} для {url}")
                headers = {'User-Agent': random.choice(self.user_agents)}
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)

                response = requests.get(url, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    logger.info(f"✅ Повторная попытка {attempt + 1} успешна")
                    self._update_stats(True)
                    return response.text
            except Exception as e:
                logger.warning(f"❌ Попытка {attempt + 1}: {str(e)[:30]}...")

        self._update_stats(False)
        return None

    def bypass_url(self, url, enabled_methods=None):
        logger.info(f"🚀 Запуск NetBypass для {url}")

        all_methods = {
            'direct': self.method_direct,
            'stealth': self.method_stealth,
            'chunked': self.method_chunked,
            'proxy': self.method_proxy,
            'retry': self.method_retry
        }

        if enabled_methods:
            methods = {name: method for name, method in all_methods.items()
                      if name in enabled_methods}
        else:
            methods = all_methods

        logger.info(f"🎯 Активные методы: {list(methods.keys())}")

        results = {}

        with ThreadPoolExecutor(max_workers=len(methods)) as executor:
            future_to_method = {
                executor.submit(method, url): name
                for name, method in methods.items()
            }

            for future in as_completed(future_to_method, timeout=30):
                method_name = future_to_method[future]
                try:
                    result = future.result()
                    if result:
                        results[method_name] = result
                        logger.info(f"🎯 Метод {method_name} вернул данные ({len(result)} символов)")
                except Exception as e:
                    logger.error(f"💥 Метод {method_name} завершился с ошибкой: {e}")

        if results:
            winner_method = list(results.keys())[0]
            logger.info(f"🏆 Победитель: {winner_method}")
            return {
                'data': results[winner_method],
                'method': winner_method,
                'all_results': {k: f"{len(v)} символов" for k, v in results.items()},
                'stats': self.stats.copy()
            }

        return {
            'data': None,
            'method': 'none',
            'all_results': {},
            'stats': self.stats.copy(),
            'error': 'Все методы не сработали'
        }

    def get_stats(self):
        return self.stats.copy()

def create_default_config():
    config = {
        "user_agents": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        ],
        "proxies": [
            # Добавить сюда рабочие прокси
            # "http://proxy1:port",
            # "http://proxy2:port"
        ],
        "timeout_settings": {
            "direct": 5,
            "stealth": 10,
            "chunked": 15,
            "proxy": 15,
            "retry": 10
        },
        "retry_settings": {
            "max_retries": 3,
            "base_delay": 1
        }
    }

    with open("netbar_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    print("✅ Создан файл конфигурации: netbar_config.json")

def main():

    parser = argparse.ArgumentParser(
        description='NetBar Toolkit - Интеллектуальный обход сетевых ограничений',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python netbar.py https://example.com
  python netbar.py https://example.com --methods direct stealth
  python netbar.py https://example.com --verbose
  python netbar.py --config
        """
    )

    parser.add_argument('url', nargs='?', help='URL для обхода')
    parser.add_argument('--methods', '-m', nargs='+',
                       choices=['direct', 'stealth', 'chunked', 'proxy', 'retry'],
                       help='Выбор конкретных методов')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Подробный вывод (DEBUG уровень)')
    parser.add_argument('--config', '-c', action='store_true',
                       help='Создать файл конфигурации')
    parser.add_argument('--demo', '-d', action='store_true',
                       help='Запустить демонстрацию')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.config:
        create_default_config()
        return

    if args.demo:
        run_demo()
        return

    if not args.url:
        parser.print_help()
        return

    bypass = NetBypass()
    result = bypass.bypass_url(args.url, args.methods)

    print("\n" + "="*60)
    print("NetBar Toolkit - Результаты")
    print("="*60)

    if result['data']:
        print(f"✅ УСПЕХ!")
        print(f"   Метод: {result['method']}")
        print(f"   Размер: {len(result['data'])} символов")
        print(f"   Все результаты: {result['all_results']}")
        print(f"   Статистика: {result['stats']}")

        filename = f"result_{int(time.time())}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(result['data'])
        print(f"   📁 Результат сохранен в: {filename}")
    else:
        print("❌ Не удалось обойти ограничения")
        print(f"   Ошибка: {result.get('error', 'Неизвестная ошибка')}")
        print(f"   Статистика: {result['stats']}")

    print("="*60)

def run_demo():
    print("=" * 60)
    print("NetBar Toolkit - Демонстрация работы")
    print("=" * 60)

    bypass = NetBypass()

    # Test URL
    test_urls = [
        'https://httpbin.org/ip',
        'https://httpbin.org/user-agent',
    ]

    for i, url in enumerate(test_urls, 1):
        print(f"\n🚀 Тест {i}/{len(test_urls)}: {url}")
        print("-" * 50)

        try:
            result = bypass.bypass_url(url)

            if result['data']:
                print(f"✅ УСПЕХ!")
                print(f"   Метод: {result['method']}")
                print(f"   Размер: {len(result['data'])} символов")
                print(f"   Статистика: {result['stats']}")
            else:
                print(f"❌ Не удалось обойти")
                print(f"   Ошибка: {result.get('error', 'Неизвестная ошибка')}")
                print(f"   Статистика: {result['stats']}")

        except Exception as e:
            print(f"💥 Ошибка при тестировании: {e}")

        # Небольшая пауза между тестами
        if i < len(test_urls):
            time.sleep(2)

    print("\n" + "=" * 60)
    print("Демонстрация завершена!")
    print("=" * 60)

if __name__ == "__main__":
    main()
