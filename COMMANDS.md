# Готовые команды для тестирования проекта

Все команды протестированы и готовы к использованию. Просто копируйте и запускайте.

## Базовая настройка

```bash
# Переход в директорию проекта
cd /Users/nikolai/Desktop/нир/blockchain_forensics_prototype

# Активация виртуального окружения (всегда первым делом!)
source .venv/bin/activate
```

---

## 🎯 Сценарий 1: Офлайн-демонстрация (для защиты НИР)

**Преимущества:** работает без интернета, быстро, воспроизводимо.

```bash
# Анализ заранее подготовленного датасета
python main.py analyze data/sample_dataset.json --out demo_result.json

# Просмотр результатов
cat demo_result.json | python -m json.tool | head -n 100

# Извлечение статистики графа
cat demo_result.json | python -c "import sys, json; d=json.load(sys.stdin); print(json.dumps(d['graph_stats'], indent=2))"

# Извлечение информации о кластерах
cat demo_result.json | python -c "import sys, json; d=json.load(sys.stdin); print(f'Найдено кластеров: {len(d[\"clusters\"])}')"
```

**Ожидаемый результат:**
```
Saved analysis to demo_result.json
```

---

## 🎯 Сценарий 2: Анализ реального Bitcoin-адреса

### Вариант A: Адрес-накопитель (холодный кошелёк)

```bash
# Сбор данных
python main.py fetch bc1qm9ph0jahvqn4vk67s4jjxgvzdzun7hpds9ckvt --out cold_wallet.json --limit 50

# Анализ
python main.py analyze cold_wallet.json --out cold_wallet_analysis.json

# Просмотр профиля
cat cold_wallet_analysis.json | python -m json.tool | grep -A 15 '"address_profiles"'
```

**Что вы увидите:**
- `total_out_btc: 0.0` (адрес не тратит средства)
- `flags: []` (нет подозрительной активности)
- Тип: холодный/накопительный кошелёк

### Вариант B: Адрес с высоким объёмом (подозрение на биржу)

```bash
# Сбор данных
python main.py fetch bc1qryhgpmfv03qjhhp2dj8nw8g4ewg08jzmgy3cyx --out exchange_wallet.json --limit 100

# Анализ
python main.py analyze exchange_wallet.json --out exchange_analysis.json

# Просмотр флагов
cat exchange_analysis.json | python -c "import sys, json; d=json.load(sys.stdin); [print(f'{addr}: {prof[\"flags\"]}') for addr, prof in d['address_profiles'].items() if prof['flags']]"
```

**Что вы увидите:**
- `flags: ["high_volume"]`
- Большие объёмы входов и выходов (>30 BTC)
- Вероятно: биржевой или сервисный адрес

---

## 🎯 Сценарий 3: Интеграция с CryptoDeepTools

### Проверка установки

```bash
python main.py cdt-install --repo-dir vendor/CryptoDeepTools
```

**Результат:**
```
CryptoDeepTools already exists at vendor/CryptoDeepTools
```

### Конвертация публичного ключа в Bitcoin-адрес

```bash
# Пример 1: Compressed public key (начинается с 03)
python main.py cdt-pubtoaddr 0301c1768b48843933bd7f0e8782716e8439fc44723d3745feefde2d57b761f503

# Пример 2: Другой compressed public key (начинается с 02)
python main.py cdt-pubtoaddr 02c1b2a7f8c4e6c5b7e9d4f2a1c3e5b6a9d8f7e6c4b2a1f9e8d7c6b5a4323130
```

**Ожидаемый вывод:**
```
CryptoDeepTools pubtoaddr.py result:
Public Key: 0301c1768b48843933bd7f0e8782716e8439fc44723d3745feefde2d57b761f503
Bitcoin Address: 1D9Y4JH374qsdXxzp7DMLFsak4HeiCanUX
```

### Проверка результата в блокчейне

```bash
# Открыть адрес в браузере (macOS)
open "https://blockstream.info/address/1D9Y4JH374qsdXxzp7DMLFsak4HeiCanUX"
```

---

## 🎯 Сценарий 4: Анализ кластера адресов

```bash
# Собираем данные по нескольким адресам из одного кластера
python main.py fetch bc1qt636clld6p7tmexeapjhgm4ncgppdkjhm3s7vq --out addr1.json --limit 30
python main.py fetch bc1qj73gk3zsqv35vx0zk3pndcdjcuxsctl2jr5k20 --out addr2.json --limit 30
python main.py fetch bc1qm9ph0jahvqn4vk67s4jjxgvzdzun7hpds9ckvt --out addr3.json --limit 30

# Анализируем каждый
python main.py analyze addr1.json --out analysis_addr1.json
python main.py analyze addr2.json --out analysis_addr2.json
python main.py analyze addr3.json --out analysis_addr3.json

# Сравниваем общих контрагентов
echo "=== Addr1 top counterparties ==="
cat analysis_addr1.json | python -c "import sys, json; d=json.load(sys.stdin); [print(d['address_profiles'][addr]['top_counterparties'][:3]) for addr in list(d['address_profiles'].keys())[:1]]"

echo "=== Addr2 top counterparties ==="
cat analysis_addr2.json | python -c "import sys, json; d=json.load(sys.stdin); [print(d['address_profiles'][addr]['top_counterparties'][:3]) for addr in list(d['address_profiles'].keys())[:1]]"
```

---

## 🎯 Сценарий 5: Извлечение данных для отчёта НИР

### Создание красиво отформатированного JSON

```bash
python main.py analyze data/sample_dataset.json --out report.json
cat report.json | python -m json.tool > formatted_report.json
```

### Извлечение только ключевых метрик

```bash
# Статистика графа
cat report.json | python -c "import sys, json; d=json.load(sys.stdin); print('=== Graph Statistics ==='); print(json.dumps(d['graph_stats'], indent=2))"

# Информация о кластерах
cat report.json | python -c "import sys, json; d=json.load(sys.stdin); print(f'Total clusters: {len(d[\"clusters\"])}'); [print(f'Cluster {c[\"cluster_id\"]}: {len(c[\"addresses\"])} addresses') for c in d['clusters']]"

# Суммарная активность
cat report.json | python -c "import sys, json; d=json.load(sys.stdin); print(f'Root address: {d[\"root_address\"]}'); print(f'Transactions analyzed: {d[\"tx_count\"]}'); print(f'Notes: {d[\"notes\"]}')"
```

### Экспорт таблицы адресов для Excel

```bash
# Создание CSV с профилями адресов
cat report.json | python -c "
import sys, json
d = json.load(sys.stdin)
print('address,tx_count,total_in_btc,total_out_btc,fees_paid_btc,flags')
for addr, prof in d['address_profiles'].items():
    print(f'{addr},{prof[\"tx_count_involving\"]},{prof[\"total_in_btc\"]},{prof[\"total_out_btc\"]},{prof[\"fees_paid_btc\"]},{\"|\".join(prof[\"flags\"])}')
" > address_profiles.csv

# Просмотр CSV
cat address_profiles.csv | head -n 10
```

---

## 🎯 Сценарий 6: Полный цикл анализа для презентации

```bash
# Шаг 1: Сбор данных
echo "📊 Шаг 1: Сбор ончейн-данных..."
python main.py fetch bc1qm9ph0jahvqn4vk67s4jjxgvzdzun7hpds9ckvt --out presentation_data.json --limit 50

# Шаг 2: Анализ
echo "🔍 Шаг 2: Анализ транзакций и кластеризация..."
python main.py analyze presentation_data.json --out presentation_analysis.json

# Шаг 3: Демонстрация CryptoDeepTools
echo "🔧 Шаг 3: Демонстрация интеграции с CryptoDeepTools..."
python main.py cdt-pubtoaddr 0301c1768b48843933bd7f0e8782716e8439fc44723d3745feefde2d57b761f503

# Шаг 4: Извлечение ключевых результатов
echo "📈 Шаг 4: Ключевые результаты анализа:"
cat presentation_analysis.json | python -c "
import sys, json
d = json.load(sys.stdin)
print(f'✓ Проанализировано транзакций: {d[\"tx_count\"]}')
print(f'✓ Обнаружено кластеров: {len(d[\"clusters\"])}')
print(f'✓ Узлов в графе адресов: {d[\"graph_stats\"][\"address_graph_nodes\"]}')
print(f'✓ Рёбер в графе: {d[\"graph_stats\"][\"address_graph_edges\"]}')
print(f'✓ Профилей адресов создано: {len(d[\"address_profiles\"])}')
"

echo "✅ Анализ завершён! Результаты сохранены в presentation_analysis.json"
```

---

## 📋 Полезные команды для отладки

### Проверка версий

```bash
python --version
pip list | grep -E 'requests|pandas|networkx|matplotlib|base58'
```

### Просмотр помощи

```bash
python main.py --help
python main.py fetch --help
python main.py analyze --help
python main.py cdt-pubtoaddr --help
```

### Очистка временных файлов

```bash
rm -f addr*.json analysis_addr*.json cold_wallet*.json exchange*.json demo_result.json presentation*.json high_volume*.json my_*.json
```

---

## 🎓 Команды для защиты НИР (демонстрация без интернета)

```bash
# Активация окружения
source .venv/bin/activate

# Команда 1: Офлайн-анализ
python main.py analyze data/sample_dataset.json --out nir_demo.json

# Команда 2: Показать результаты
cat nir_demo.json | python -m json.tool | head -n 60

# Команда 3: Статистика графа
cat nir_demo.json | python -c "import sys, json; print(json.dumps(json.load(sys.stdin)['graph_stats'], indent=2))"

# Команда 4: Демонстрация CryptoDeepTools (офлайн, если репо уже склонирован)
python main.py cdt-pubtoaddr 0301c1768b48843933bd7f0e8782716e8439fc44723d3745feefde2d57b761f503

# Команда 5: Показать кластеры
cat nir_demo.json | python -c "import sys, json; d=json.load(sys.stdin); print(f'Обнаружено кластеров: {len(d[\"clusters\"])}'); [print(f'  Кластер {i}: {len(c[\"addresses\"])} адресов') for i, c in enumerate(d['clusters'][:5])]"
```

**Время выполнения:** < 2 секунды
**Требования:** не требуется интернет (если CryptoDeepTools уже установлен)

---

## 🔗 Быстрые ссылки

- Репозиторий CryptoDeepTools: https://github.com/demining/CryptoDeepTools
- Blockstream Explorer: https://blockstream.info
- Bitcoin Testnet Explorer: https://blockstream.info/testnet

---

## ⚡ Самые частые команды (шпаргалка)

```bash
# Активация окружения
source .venv/bin/activate

# Офлайн-демо
python main.py analyze data/sample_dataset.json --out result.json

# Онлайн-анализ
python main.py fetch <ADDRESS> --out data.json --limit 50
python main.py analyze data.json --out analysis.json

# CryptoDeepTools
python main.py cdt-pubtoaddr <PUBKEY_HEX>

# Просмотр результатов
cat analysis.json | python -m json.tool | less
```

---

**Примечание:** Все команды протестированы на macOS с Python 3.9+. Для других ОС замените `source .venv/bin/activate` на:
- Windows: `.venv\Scripts\activate`
- Linux: `source .venv/bin/activate`
