# Development Engineering Standard

Ce document fixe les règles obligatoires de développement de **Crypto Quant Bot V3.1-Ops** pour éviter duplication, fonctions géantes, couplage caché, réécritures sans fin et code impossible à auditer.

## 1. Principes

- une responsabilité claire par module, classe et fonction ;
- contrats publics explicites ;
- dépendances orientées vers les abstractions du domaine ;
- aucune duplication fonctionnelle silencieuse ;
- aucun effet de bord caché ;
- aucune permission implicite ;
- priorité à la lisibilité, au déterminisme et à l'auditabilité.

## 2. Taille et complexité

Seuils par défaut, avec dérogation documentée seulement :

```text
fonction <= 50 lignes logiques
classe <= 400 lignes logiques
module <= 800 lignes logiques
complexité cyclomatique par fonction <= 10
profondeur d'imbrication <= 4
nombre de paramètres <= 7
```

Une dérogation exige justification, tests renforcés et plan de simplification.

## 3. Une seule source de vérité

- une capability possède un owner unique ;
- aucune seconde implémentation métier sans statut explicite `REFERENCE`, `EXPERIMENTAL` ou `MIGRATION` ;
- les helpers communs sont centralisés seulement lorsqu'ils représentent réellement le même concept ;
- pas de copier-coller de formules ou de transitions d'état ;
- la recherche de symboles similaires fait partie de la revue de lot.

## 4. Fonctions et API

Chaque fonction publique documente :

- responsabilité ;
- entrées et types ;
- sorties ;
- erreurs ;
- invariants ;
- effets de bord ;
- déterminisme ;
- complexité attendue.

Une fonction ne doit pas calculer, persister, logger et décider simultanément. Les étapes sont séparées lorsque cela améliore la testabilité.

## 5. Modèles et contrats

- modèles immuables par défaut ;
- schémas versionnés ;
- enums fermés ;
- pas de dictionnaires libres aux frontières critiques ;
- validation à l'entrée du domaine ;
- aucune lecture directe d'attributs internes d'un autre domaine ;
- migrations explicites et testées.

## 6. Gestion des erreurs

- exceptions typées ;
- aucun `except Exception: pass` ;
- aucune conversion d'une erreur en succès ;
- erreurs critiques avec reason code stable ;
- état incomplet non publié ;
- écriture atomique ;
- retry borné et uniquement pour opérations sûres/idempotentes.

## 7. Configuration

- aucun seuil métier caché dans le code ;
- configuration typée et versionnée ;
- valeur par défaut conservatrice ;
- validation au démarrage ;
- config effective jointe aux artefacts ;
- changement de config auditable et réversible.

## 8. Déterminisme et temps

- horloge injectée ;
- random seed injectée et persistée ;
- ordre de traitement canonique ;
- pas de dépendance à l'ordre d'un dictionnaire externe ;
- timezone UTC canonique ;
- event-time et processing-time séparés.

## 9. Logging et audit

- logs structurés ;
- correlation_id/run_id partout ;
- pas de secret ni donnée sensible ;
- reason codes stables ;
- aucune décision importante uniquement dans un log libre ;
- chaque transition d'état génère un événement auditable.

## 10. Revue de code

Toute PR de lot vérifie :

- conformité architecture ;
- absence de duplication ;
- noms explicites ;
- complexité ;
- contrats ;
- erreurs ;
- tests ;
- performance ;
- sécurité ;
- documentation ;
- migration et rollback.

Les changements massifs non séparés sont interdits : un lot doit rester auditable commit par commit.

## 11. Refactoring

- pas de refactoring opportuniste non lié au lot ;
- comportement couvert avant refactoring ;
- tests de caractérisation lorsque le comportement historique est mal documenté ;
- aucun renommage d'artefact validé sans migration ;
- suppression uniquement après preuve d'absence d'usage.

## 12. Dépendances

- dépendance externe justifiée ;
- version fixée/contrainte ;
- licence et sécurité vérifiées ;
- wrapper interne pour dépendances critiques ;
- aucune dépendance réseau cachée ;
- plan de remplacement pour composant critique.

## 13. Definition of Clean Code Done

Un lot n'est pas terminé si :

- duplication significative non résolue ;
- fonction ou classe hors seuil sans dérogation ;
- TODO/FIXME critique ;
- dead code ;
- test flaky ;
- seuil métier hardcodé ;
- contrat ambigu ;
- erreur avalée ;
- documentation divergente ;
- dette critique sans ticket, owner et échéance.

Tout écart donne `NO_GO_ENGINEERING_QUALITY`.