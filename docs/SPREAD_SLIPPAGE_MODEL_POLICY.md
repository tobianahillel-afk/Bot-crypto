# Spread & Slippage Model Policy — Lot 10

Le spread est estimé en points de base à partir d'une valeur par défaut bornée par la configuration. Le slippage est estimé à partir d'une base statique et d'une composante de volatilité si elle existe dans le MarketState.

Les deux modèles sont bornés. Ils ne contiennent aucune logique d'entrée, de sortie, de direction, de signal ou de décision de trading.

Le Lot 10 n'utilise ni carnet d'ordres live, ni API, ni WebSocket. Les valeurs sont théoriques et destinées à l'audit trail.
