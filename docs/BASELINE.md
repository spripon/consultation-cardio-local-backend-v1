# Baseline auditée

```
LOVABLE_BASELINE_SHA=de542fee77a69ee355d920b33b80f0387148f059
```

Ce SHA identifie l'état du projet Lovable **audité** (runtime 100 % local, OCR/PII/
catégorisation locales, fail-closed) juste avant l'ajout des outils de préparation
au déploiement Ubuntu.

## Portée

- Aucune logique clinique, OCR, anonymisation PII ou frontend n'a été modifiée
  après ce SHA par la préparation Ubuntu : seuls des fichiers de déploiement,
  scripts et documentation ont été ajoutés.
- Ce SHA est la référence de revue / de rollback fonctionnel.

## Rapport avec GitHub

Le SHA GitHub obtenu lors du premier sync Lovable → GitHub **sera différent** de
`de542fee77a69ee355d920b33b80f0387148f059`. La synchronisation crée un historique
Git propre côté dépôt ; il ne s'agit pas d'un miroir des commits Lovable, et il
n'existe aucun moyen de forcer l'égalité des SHA. Ne jamais supposer ni annoncer
qu'ils sont identiques.

Pour tracer un déploiement, conserver **le SHA GitHub réellement déployé** (voir
la section backup/rollback de `deploy/README_UBUNTU.md`) et, en commentaire, le
SHA Lovable de référence ci-dessus.
