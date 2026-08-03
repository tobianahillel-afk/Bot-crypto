# V11 — News / AI / Event Context

Identifiant : `V11_NEWS_AI_EVENT`

Plage canonique : **Lots 103 à 110**

Statut : `PLANNED_LOCKED`

## Objectif de la version

Ajouter news, événements et explications IA comme contexte read-only et non exécutable.

## Gates d’entrée de version

- Les dépendances des versions précédentes sont validées.
- Les invariants de sécurité transverses restent actifs.
- Le scope est approuvé et les artefacts attendus sont listés.
- Les données nécessaires sont disponibles avec qualité suffisante.

## Lot 103 — News / AI Scope Gate & Source Registry

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « News / AI Scope Gate & Source Registry » dans la phase News / AI / Event Context avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Source registry
- News/events read-only
- Market context

### Exigences d’implémentation

- Utiliser uniquement des sources enregistrées et évaluées.
- Séparer ingestion, extraction, scoring et explication.
- Conserver timestamp de publication, événement et réception.
- Limiter le LLM à la reformulation/explication avec citations internes.
- Autoriser le contexte news à réduire ou bloquer le risque, jamais à augmenter seul une position.

### Artefacts attendus

- Event context
- Narrative state
- Reliability scores
- LLM explanations with provenance

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- news_context cannot increase size alone
- LLM cannot approve trade

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 104 — Economic Calendar & Event Schema

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Economic Calendar & Event Schema » dans la phase News / AI / Event Context avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Source registry
- News/events read-only
- Market context

### Exigences d’implémentation

- Utiliser uniquement des sources enregistrées et évaluées.
- Séparer ingestion, extraction, scoring et explication.
- Conserver timestamp de publication, événement et réception.
- Limiter le LLM à la reformulation/explication avec citations internes.
- Autoriser le contexte news à réduire ou bloquer le risque, jamais à augmenter seul une position.

### Artefacts attendus

- Event context
- Narrative state
- Reliability scores
- LLM explanations with provenance

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- news_context cannot increase size alone
- LLM cannot approve trade

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 105 — News Ingestion Read-Only

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « News Ingestion Read-Only » dans la phase News / AI / Event Context avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Source registry
- News/events read-only
- Market context

### Exigences d’implémentation

- Utiliser uniquement des sources enregistrées et évaluées.
- Séparer ingestion, extraction, scoring et explication.
- Conserver timestamp de publication, événement et réception.
- Limiter le LLM à la reformulation/explication avec citations internes.
- Autoriser le contexte news à réduire ou bloquer le risque, jamais à augmenter seul une position.

### Artefacts attendus

- Event context
- Narrative state
- Reliability scores
- LLM explanations with provenance

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- news_context cannot increase size alone
- LLM cannot approve trade

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 106 — Sentiment & Narrative Engine

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Sentiment & Narrative Engine » dans la phase News / AI / Event Context avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Source registry
- News/events read-only
- Market context

### Exigences d’implémentation

- Utiliser uniquement des sources enregistrées et évaluées.
- Séparer ingestion, extraction, scoring et explication.
- Conserver timestamp de publication, événement et réception.
- Limiter le LLM à la reformulation/explication avec citations internes.
- Autoriser le contexte news à réduire ou bloquer le risque, jamais à augmenter seul une position.

### Artefacts attendus

- Event context
- Narrative state
- Reliability scores
- LLM explanations with provenance

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- news_context cannot increase size alone
- LLM cannot approve trade

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 107 — Event Impact & Crypto Event Risk

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Event Impact & Crypto Event Risk » dans la phase News / AI / Event Context avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Source registry
- News/events read-only
- Market context

### Exigences d’implémentation

- Utiliser uniquement des sources enregistrées et évaluées.
- Séparer ingestion, extraction, scoring et explication.
- Conserver timestamp de publication, événement et réception.
- Limiter le LLM à la reformulation/explication avec citations internes.
- Autoriser le contexte news à réduire ou bloquer le risque, jamais à augmenter seul une position.

### Artefacts attendus

- Event context
- Narrative state
- Reliability scores
- LLM explanations with provenance

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- news_context cannot increase size alone
- LLM cannot approve trade

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 108 — Source Reliability & Hallucination Guard

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « Source Reliability & Hallucination Guard » dans la phase News / AI / Event Context avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Source registry
- News/events read-only
- Market context

### Exigences d’implémentation

- Utiliser uniquement des sources enregistrées et évaluées.
- Séparer ingestion, extraction, scoring et explication.
- Conserver timestamp de publication, événement et réception.
- Limiter le LLM à la reformulation/explication avec citations internes.
- Autoriser le contexte news à réduire ou bloquer le risque, jamais à augmenter seul une position.

### Artefacts attendus

- Event context
- Narrative state
- Reliability scores
- LLM explanations with provenance

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- news_context cannot increase size alone
- LLM cannot approve trade

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 109 — LLM Explanation & Context Fusion

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « LLM Explanation & Context Fusion » dans la phase News / AI / Event Context avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Source registry
- News/events read-only
- Market context

### Exigences d’implémentation

- Utiliser uniquement des sources enregistrées et évaluées.
- Séparer ingestion, extraction, scoring et explication.
- Conserver timestamp de publication, événement et réception.
- Limiter le LLM à la reformulation/explication avec citations internes.
- Autoriser le contexte news à réduire ou bloquer le risque, jamais à augmenter seul une position.

### Artefacts attendus

- Event context
- Narrative state
- Reliability scores
- LLM explanations with provenance

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- news_context cannot increase size alone
- LLM cannot approve trade

### Gate de promotion

Validation humaine et rapport PASS requis avant le lot suivant.

## Lot 110 — News/Event Replay, Audit & V11 Closure

**Statut canonique :** `PLANNED_LOCKED`

### Objectif

Implémenter le lot « News/Event Replay, Audit & V11 Closure » dans la phase News / AI / Event Context avec des contrats déterministes, des artefacts auditables et des gates explicites.

### Dépendances et entrées

- Source registry
- News/events read-only
- Market context

### Exigences d’implémentation

- Utiliser uniquement des sources enregistrées et évaluées.
- Séparer ingestion, extraction, scoring et explication.
- Conserver timestamp de publication, événement et réception.
- Limiter le LLM à la reformulation/explication avec citations internes.
- Autoriser le contexte news à réduire ou bloquer le risque, jamais à augmenter seul une position.

### Artefacts attendus

- Event context
- Narrative state
- Reliability scores
- LLM explanations with provenance
- Rapport de clôture V11_NEWS_AI_EVENT

### Tests et critères d’acceptation

- Source provenance présente
- Hallucination tests
- No direct BUY/SELL
- Replay temporel
- Tous les lots de la version sont couverts et leurs gates satisfaits

### Invariants de sécurité

- Aucun secret réel n’est stocké dans les artefacts ou les fixtures.
- Les schémas, versions, timestamps et checksums sont explicites.
- Les erreurs critiques sont fail-closed et produisent un état bloqué, jamais une autorisation implicite.
- news_context cannot increase size alone
- LLM cannot approve trade

### Gate de promotion

Version fermée uniquement après revue humaine, rapport PASS et invariants transverses validés.

## Critères de clôture de la version

- Tous les lots de la plage sont validés ou explicitement rejetés.
- Les registres et documents sont synchronisés.
- Les replays déterministes et tests négatifs passent.
- Les limitations et risques résiduels sont consignés.
- Le rapport de clôture est approuvé humainement.
