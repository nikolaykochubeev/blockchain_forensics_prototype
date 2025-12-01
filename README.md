# Blockchain Forensics Prototype (Open Tools)

Учебный прототип для практической части НИР: профилирование активности Bitcoin‑адресов/кластеров по публичным данным.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python main.py fetch <bitcoin_address> --out dataset.json --limit 200
python main.py analyze dataset.json --out analysis.json
```

## Офлайн‑демо без сети

```bash
python main.py analyze data/sample_dataset.json --out analysis_sample.json
```

## Этические и правовые ограничения

- Прототип работает **только** с публичными ончейн‑данными.
- Не выполняет deanonymization физических лиц.
- OSINT‑метки подключаются только из **открытых** словарей, которые пользователь добавляет самостоятельно.
