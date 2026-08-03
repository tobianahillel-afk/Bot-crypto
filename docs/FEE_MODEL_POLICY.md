# Fee Model Policy — Lot 10

Le modèle de frais Lot 10 lit `config/transaction_costs.yaml` et expose des frais maker/taker en points de base.

Pour le V0, chaque estimation utilise `order_type=hypothetical_noop` et applique le `taker_fee_bps` comme coût conservateur. Cette hypothèse ne crée aucun ordre taker réel ou simulé exploitable.

Les frais sont convertis en montant EUR par `notional_amount * fee_bps / 10000` avec un notional théorique fixe. Le résultat reste une donnée d'audit neutre.
