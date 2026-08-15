# Baseline auditée

```
LOVABLE_BASELINE_SHA=de542fee77a69ee355d920b33b80f0387148f059
GITHUB_BASELINE_SHA=de542fee77a69ee355d920b33b80f0387148f059
```

Ce SHA identifie l'état applicatif **audité** : runtime local, OCR/PII/catégorisation locales et comportement fail-closed, avant l'ajout des outils de préparation au déploiement Ubuntu.

## Gel GitHub

La synchronisation Lovable → GitHub a conservé l'historique Git et les SHA : le commit GitHub correspondant est exactement `de542fee77a69ee355d920b33b80f0387148f059`.

La branche GitHub immuable de référence est :

```
baseline/lovable-de542fee
```

Elle pointe exactement sur ce commit et ne doit pas être utilisée comme branche de développement.

## Branche de déploiement

Le déploiement Ubuntu V1 utilise la branche :

```
release/ubuntu-v1
```

Cette branche contient la baseline auditée plus uniquement les correctifs et outils de déploiement Ubuntu validés. Pour tracer un déploiement, conserver le SHA GitHub réellement déployé avec la date de mise en production.
