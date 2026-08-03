# Feature Registry

Le Feature Registry est le contrat central qui déclare les objets analytiques autorisés dans **Crypto Quant Bot V3.1-Ops**. Aucune feature non enregistrée dans ce document et dans `config/feature_registry.yaml` ne peut être utilisée par une couche décisionnelle future.

Le Lot 8 renforce ce registre : chaque entrée possède `name`, `description`, `inputs`, `formula`, `timeframe`, `available_at_rule`, `lookahead_safe` et `status`.

Toutes les entrées ci-dessous sont non stratégiques, lookahead-safe en V1 et `MVP_REQUIRED`. Elles gardent `used_for_decision=false` dans les datasets audités.

| name | description | inputs | formula | timeframe | available_at_rule | lookahead_safe | status |
|---|---|---|---|---|---|---|---|
| close | Prix de clôture de la candle clôturée | close | close | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| simple_return_1 | Rendement simple depuis la candle précédente | close, previous_close | close_t / close_t_minus_1 - 1 | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| log_return_1 | Rendement logarithmique depuis la candle précédente | close, previous_close | ln(close_t / close_t_minus_1) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| hl_range | Amplitude high low | high, low | high - low | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| oc_change | Variation close open | open, close | close - open | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| oc_range | Amplitude absolue open close | open, close | abs(close - open) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| typical_price | Prix typique OHLC | high, low, close | (high + low + close) / 3 | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| true_range | True range OHLC sans futur | high, low, previous_close | max(high-low, abs(high-previous_close), abs(low-previous_close)) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| rolling_mean_close_3 | Moyenne mobile des 3 clôtures disponibles | close | mean(close_t_minus_2_to_t) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| rolling_volatility_return_3 | Écart-type des 3 derniers rendements disponibles | simple_return_1 | sample_std(return_t_minus_2_to_t) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| volume_sum_3 | Somme des 3 volumes disponibles | volume | sum(volume_t_minus_2_to_t) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| close_to_close_abs_return | Retour absolu close-to-close | close, previous_close | abs(close_t / close_t_minus_1 - 1) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| realized_volatility_3 | Volatilité réalisée sur 3 rendements | simple_return_1 | sample_std(last_3_returns) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| realized_volatility_6 | Volatilité réalisée sur 6 rendements | simple_return_1 | sample_std(last_6_returns) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| atr_3 | Average True Range sur 3 candles | true_range | mean(last_3_true_ranges) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| atr_6 | Average True Range sur 6 candles | true_range | mean(last_6_true_ranges) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| volatility_percentile_lookback | Rang de volatilité dans la fenêtre disponible | true_range, atr_3, atr_6 | percentile_rank_without_future_data | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| rolling_high_6 | Plus haut des 6 dernières candles disponibles | high | max(high_t_minus_5_to_t) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| rolling_low_6 | Plus bas des 6 dernières candles disponibles | low | min(low_t_minus_5_to_t) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| rolling_range_6 | Amplitude du range 6 candles | rolling_high_6, rolling_low_6 | rolling_high_6 - rolling_low_6 | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| rolling_mid_6 | Milieu du range 6 candles | rolling_high_6, rolling_low_6 | (rolling_high_6 + rolling_low_6) / 2 | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| close_position_in_range_6 | Position de la clôture dans le range | close, rolling_low_6, rolling_range_6 | (close - rolling_low_6) / rolling_range_6 | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| range_width_pct | Largeur du range rapportée au close | rolling_range_6, close | rolling_range_6 / close | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| compression_score | Score déterministe de compression | range_width_pct | 1 - percentile_rank(range_width_pct) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| expansion_score | Score déterministe d expansion | true_range | percentile_rank(true_range) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| range_state | État de range non décisionnel | compression_score, expansion_score | unknown_or_compressed_or_normal_or_expanding | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| direction_score | Score directionnel déterministe | close, close_t_minus_3 | clipped_normalized_return_over_trend_window | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| trend_score | Score de tendance déterministe | direction_score | abs(direction_score) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| range_score | Score de range déterministe | direction_score, expansion_score, range_width_pct | bounded_range_score | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| volatility_score | Score de volatilité déterministe | volatility_percentile_lookback | bounded_volatility_score | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| regime_state | État de régime non décisionnel | direction_score, range_score, volatility_score | deterministic_regime_classifier | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| confidence_score | Score de confiance du régime | available_sub_scores | mean_of_available_bounded_scores | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| regime_confidence_score | Alias documentaire du score de confiance du régime | available_sub_scores | mean_of_available_bounded_scores | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| vwap | VWAP cumulatif sur candles clôturées | typical_price, volume | sum(price_volume) / sum(volume) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| anchored_vwap | VWAP ancré sur anchor connue | anchor, typical_price, volume | sum_from_anchor(price_volume) / sum_from_anchor(volume) | 5m/15m | available_at >= usable_from de l anchor | true | MVP_REQUIRED |
| cumulative_price_volume | Cumul prix volume disponible | typical_price, volume | sum(typical_price * volume) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| cumulative_volume | Cumul volume disponible | volume | sum(volume) | 5m/15m | available_at de la candle clôturée | true | MVP_REQUIRED |
| strength_score | Score de force pivot ou zone | confirmed_object_components | bounded_strength_score | 5m/15m | available_at >= usable_from de l objet | true | MVP_REQUIRED |

## Interdictions avant les lots de backtest supervisés

Les champs `future_*`, `target`, `label`, `signal`, `long_signal`, `short_signal`, `trade_signal`, `entry_signal`, `exit_signal`, `buy` et `sell` sont interdits dans les noms de clés JSONL audités au Lot 8.

Le registre ne crée aucune stratégie, aucun backtest, aucun paper trading, aucun ML, aucun appel API, aucun WebSocket et aucun signal exploitable.
