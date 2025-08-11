install:
pip install -e .

test:
pytest

run:
python cli/bot.py live BTCUSDT
