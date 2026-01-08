# Blockchain Forensics Prototype

Прототип системы профилирования активности в Bitcoin-блокчейне с интеграцией CryptoDeepTools.


```bash
# 1. Активация окружения
source .venv/bin/activate

# 2. Офлайн-демонстрация (для защиты НИР)
python main.py analyze data/sample_dataset.json --out analysis.json

# 3. Анализ реального адреса
python main.py fetch bc1qm9ph0jahvqn4vk67s4jjxgvzdzun7hpds9ckvt --out dataset.json --limit 50
python main.py analyze dataset.json --out my_analysis.json

# 4. Демонстрация CryptoDeepTools
python main.py cdt-pubtoaddr 0301c1768b48843933bd7f0e8782716e8439fc44723d3745feefde2d57b761f503

# 5. Просмотр результатов
cat my_analysis.json | python -m json.tool | head -n 80
```

**Результат:** файлы analysis.json с профилями адресов, кластерами и графовой статистикой.

---

## Установка и настройка (macOS)

### 1. Проверка Python
```bash
python3 --version  # Требуется Python 3.9+
```

Если Python не установлен:
```bash
brew install python
```

### 2. Создание виртуального окружения
```bash
cd blockchain_forensics_prototype
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Установка зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Установка CryptoDeepTools
```bash
python main.py cdt-install --repo-dir vendor/CryptoDeepTools
```

## Использование

### Вариант А: Офлайн-демонстрация (для презентации)

Анализ заранее подготовленного датасета без доступа к интернету:

```bash
python main.py analyze data/sample_dataset.json --out analysis_sample.json
```

Результат сохраняется в `analysis_sample.json`.

### Вариант Б: Анализ реального адреса (онлайн)

#### 1. Сбор данных о Bitcoin-адресе
```bash
python main.py fetch <BITCOIN_ADDRESS> --out dataset.json --limit 200
```

Пример:
```bash
python main.py fetch bc1qm9ph0jahvqn4vk67s4jjxgvzdzun7hpds9ckvt --out dataset.json --limit 200
```

#### 2. Анализ собранных данных
```bash
python main.py analyze dataset.json --out analysis.json
```

### Вариант В: Интеграция с CryptoDeepTools

#### Извлечение публичного ключа из транзакции
```bash
python main.py extract-pubkey <TXID> --vin-index 0
```

Пример:
```bash
python main.py extract-pubkey 65d8bd45f01bd6209d8695d126ba6bb4f2936501c12b9a1ddc9e38600d35aaa2
```

#### Преобразование публичного ключа в адрес (CryptoDeepTools)
```bash
python main.py cdt-pubtoaddr <PUBKEY_HEX> --repo-dir vendor/CryptoDeepTools
```

Пример с известным публичным ключом:
```bash
python main.py cdt-pubtoaddr 0301c1768b48843933bd7f0e8782716e8439fc44723d3745feefde2d57b761f503
```

Вывод:
```
CryptoDeepTools pubtoaddr.py result:
Public Key: 0301c1768b48843933bd7f0e8782716e8439fc44723d3745feefde2d57b761f503
Bitcoin Address: 1D9Y4JH374qsdXxzp7DMLFsak4HeiCanUX
```


Пример профиля адреса:
```json
{
  "tx_count_involving": 8,
  "first_seen": 1746996227,
  "last_seen": 1766696645,
  "total_in_btc": 0.01464883,
  "total_out_btc": 0.0,
  "fees_paid_btc": 0.0,
  "top_counterparties": [["bc1qryhgpmfv03qjhhp2dj8nw8g4ewg08jzmgy3cyx", 8]],
  "flags": []
}
```

## Все доступные команды

```bash
python main.py --help
```

Команды:
- `fetch` — Сбор истории транзакций адреса через публичный API
- `analyze` — Анализ датасета с построением графов и кластеров
- `cdt-install` — Клонирование репозитория CryptoDeepTools
- `cdt-pubtoaddr` — Запуск CryptoDeepTools pubtoaddr.py
- `extract-pubkey` — Извлечение публичного ключа из транзакции

## Технические особенности

### Кластеризация адресов

Используются эвристики:
1. **Multi-input heuristic** — адреса, используемые как входы в одной транзакции, вероятно принадлежат одному субъекту
2. **Change-address detection** — обнаружение сдачи на основе анализа выходов

### OSINT-интеграция

Проект поддерживает добавление меток адресов из внешних источников:
```bash
python main.py analyze dataset.json --labels labels.json --out analysis_labeled.json
```

Формат `labels.json`:
```json
{
  "bc1qexample...": {
    "kind": "exchange",
    "name": "Binance",
    "source": "public report"
  }
}
```

### Интеграция с CryptoDeepTools

Проект явно использует инструменты из репозитория [CryptoDeepTools](https://github.com/demining/CryptoDeepTools):
- `03CheckBitcoinAddressBalance/pubtoaddr.py` — преобразование публичного ключа в Bitcoin-адрес

## пример использования всех возможностей (на реальных данных)

### Сценарий 1: Анализ активного Bitcoin-адреса

**Шаг 1: Активируем окружение**
```bash
source .venv/bin/activate
```

**Шаг 2: Собираем данные о реальном адресе**
```bash
python main.py fetch bc1qm9ph0jahvqn4vk67s4jjxgvzdzun7hpds9ckvt --out my_dataset.json --limit 50
```

Результат:
```
Saved dataset to my_dataset.json (txs=9)
```

**Шаг 3: Анализируем собранные данные**
```bash
python main.py analyze my_dataset.json --out my_analysis.json
```

Результат:
```
Saved analysis to my_analysis.json
```

**Шаг 4: Просматриваем результаты**
```bash
cat my_analysis.json | python -m json.tool | head -n 50
```

- Обнаруженные кластеры адресов (multi-input heuristic)
- Профили всех связанных адресов с метриками
- Топ контрагентов
- Временные паттерны активности
- Флаги подозрительного поведения (high_volume и др.)

### Сценарий 2: Демонстрация CryptoDeepTools

**Шаг 1: Проверяем установку CryptoDeepTools**
```bash
python main.py cdt-install --repo-dir vendor/CryptoDeepTools
```

Результат:
```
CryptoDeepTools already exists at vendor/CryptoDeepTools
```

**Шаг 2: Конвертируем публичный ключ в адрес**

Используем реальный compressed public key:
```bash
python main.py cdt-pubtoaddr 0301c1768b48843933bd7f0e8782716e8439fc44723d3745feefde2d57b761f503
```

Результат:
```
CryptoDeepTools pubtoaddr.py result:
Public Key: 0301c1768b48843933bd7f0e8782716e8439fc44723d3745feefde2d57b761f503
Bitcoin Address: 1D9Y4JH374qsdXxzp7DMLFsak4HeiCanUX
```

**Шаг 3: Проверка результата (опционально)**

Проверяем полученный адрес в блокчейн-обозревателе:
```bash
"https://blockstream.info/address/1D9Y4JH374qsdXxzp7DMLFsak4HeiCanUX"
```

### Сценарий 3: Анализ адреса с высоким объёмом транзакций

**Адрес с большим количеством транзакций:**
```bash
python main.py fetch bc1qryhgpmfv03qjhhp2dj8nw8g4ewg08jzmgy3cyx --out high_volume.json --limit 100
python main.py analyze high_volume.json --out high_volume_analysis.json
```

Этот адрес показывает признаки:
- Высокого объёма операций (флаг `high_volume`)
- Регулярной активности
- Возможной принадлежности к сервису/бирже

### Сценарий 5: Полный цикл с несколькими адресами

**Анализируем кластер адресов:**

```bash
# Первый адрес из кластера
python main.py fetch bc1qt636clld6p7tmexeapjhgm4ncgppdkjhm3s7vq --out addr1.json --limit 30

# Второй адрес из кластера
python main.py fetch bc1qj73gk3zsqv35vx0zk3pndcdjcuxsctl2jr5k20 --out addr2.json --limit 30

# Анализ обоих
python main.py analyze addr1.json --out analysis1.json
python main.py analyze addr2.json --out analysis2.json
```

Сравниваем результаты, чтобы увидеть:
- Общих контрагентов
- Похожие паттерны активности
- Совпадение временных интервалов

### Сценарий 6: Извлечение публичного ключа из транзакции (экспериментальный)

**Попытка извлечь pubkey из реальной SegWit-транзакции:**

```bash
python main.py extract-pubkey a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d --vin-index 0
```

**Примечание:** Публичный ключ раскрывается только в транзакциях, где адрес **тратит** средства (является входом). Для адресов, которые только получают BTC, публичный ключ недоступен (это часть модели безопасности Bitcoin).

### Сравнение результатов разных адресов

**Просмотр ключевых метрик:**

```bash
# Профиль адреса-получателя
cat my_analysis.json | python -m json.tool | grep -A 10 '"bc1qm9ph0jahvqn4vk67s4jjxgvzdzun7hpds9ckvt"'

# Профиль адреса с высоким объёмом
cat high_volume_analysis.json | grep -A 10 '"total_in_btc"'
```

### Практические наблюдения из анализа

**Адрес bc1qm9ph0jahvqn4vk67s4jjxgvzdzun7hpds9ckvt:**
- Тип поведения: накопительный (только входы)
- total_in_btc: 0.01464883
- total_out_btc: 0.0
- Вывод: адрес не тратил средства, вероятно "холодный" кошелёк

**Адрес bc1qryhgpmfv03qjhhp2dj8nw8g4ewg08jzmgy3cyx:**
- Флаг: `high_volume`
- total_in_btc: ~31.17 BTC
- total_out_btc: ~31.19 BTC
- Вывод: транзитный адрес, вероятно сервис/биржа

### Экспорт результатов для отчёта

```bash
python main.py analyze data/sample_dataset.json --out report_analysis.json
cat report_analysis.json | python -m json.tool > formatted_report.json
```

**Извлечение только кластеров:**
```bash
cat my_analysis.json | python -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data['clusters'], indent=2))"
```

**Извлечение графовой статистики:**
```bash
cat my_analysis.json | python -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data['graph_stats'], indent=2))"
```

Результат:
```json
{
  "address_graph_nodes": 2,
  "address_graph_edges": 2,
  "bipartite_nodes": 10,
  "bipartite_edges": 16
}
```

### Использование с пользовательскими OSINT-метками 

**Формат файла labels.json:**
```json
{
  "bc1qryhgpmfv03qjhhp2dj8nw8g4ewg08jzmgy3cyx": {
    "kind": "suspected_exchange",
    "name": "Unknown Exchange Wallet",
    "source": "High volume pattern analysis",
    "confidence": "medium"
  },
  "bc1qm9ph0jahvqn4vk67s4jjxgvzdzun7hpds9ckvt": {
    "kind": "personal_wallet",
    "name": "Cold storage candidate",
    "source": "No outgoing transactions",
    "confidence": "high"
  }
}
```

```bash
python main.py analyze dataset.json --labels labels.json --out labeled_analysis.json
```



Учебный проект. Использует открытые инструменты и публичные данные.
