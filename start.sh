#!/bin/sh
set -eu

# TODO: alembic upgrade head  # (РєРѕР»Рё Р·'СЏРІР»СЏС‚СЊСЃСЏ РјС–РіСЂР°С†С–С—)

exec python -m app.main
