# Confidentialité et traitement des données

## Principe

Traitement **100 % local**. Le code ne contient aucun appel à un service d'IA ou de
stockage externe (OpenAI, Anthropic, Google, Azure, Supabase…).

## Cycle de vie d'un document

1. Le fichier est envoyé du navigateur vers l'API locale, même origine (`/api`).
2. Type réel vérifié par signature binaire ; taille plafonnée (20 Mo par défaut).
3. OCR local (Tesseract / couche texte PDF). Fichiers temporaires en `tmpfs`,
   supprimés immédiatement après traitement.
4. Anonymisation en plusieurs couches : règles déterministes, modèle PII local
   optionnel, puis balayage de sécurité final.
5. Catégorisation déterministe sur le **texte anonymisé uniquement**.
6. Le texte brut non anonymisé n'est **jamais** renvoyé au frontend en production.
7. Aucune persistance : ni base de données, ni fichier conservé.

## Journalisation

Les journaux ne contiennent aucun contenu patient : uniquement `request_id`, type MIME,
taille et durée. Le frontend ne journalise plus de texte transcrit ni extrait.

## Validation humaine obligatoire

L'anonymisation automatique ne peut pas être garantie. L'interface :

- n'injecte jamais automatiquement le texte dans le dossier ;
- affiche le texte anonymisé, éditable, avec les scores de confiance ;
- bloque l'insertion si un identifiant résiduel a été détecté ;
- exige une case de confirmation explicite du soignant.

## Ce qui est conservé et ce qui est retiré

Retiré : nom, prénom, date de naissance, IPP, NIR, téléphone, e-mail, adresse,
noms de médecins (configurable).

Conservé (politique `gdpr_pseudonymization`, adaptée à la cardiologie) : âge, sexe,
valeurs biologiques, constantes, tracés ECG, traitements et posologies, antécédents.
La politique `strict_no_leak` retire en plus l'âge, le sexe et les dates.
## Précisions d'audit

- **Aucune garantie d'anonymisation.** Le pipeline (règles déterministes +
  modèle PII local + balayage de sécurité) réduit le risque ; il ne l'annule pas.
  La relecture par un professionnel de santé reste obligatoire, et le champ
  `requiresHumanValidation` vaut toujours `true`.
- **Défaut restrictif.** `safeToInject` vaut `false` par défaut, côté serveur
  comme côté navigateur : une réponse tronquée ou inattendue n'autorise jamais
  l'insertion automatique dans le formulaire.
- **Revalidation des corrections.** Le texte relu et corrigé par le médecin est
  repassé sur le serveur (anonymisation + balayage) avant catégorisation. Les
  rubriques insérées sont recalculées à partir du texte réellement validé, pas à
  partir de la première extraction.
- **Isolation réseau.** Le conteneur d'API n'a aucune route de sortie
  (`internal: true`) : aucun appel externe n'est possible, même par erreur.
- **Documents refusés plutôt que tronqués.** Un PDF dépassant la limite de pages
  est rejeté (413) pour éviter tout compte rendu partiel non signalé.

## Revalidation systématique de /categorize

`/api/v1/categorize` ne fait plus confiance au texte reçu : il le repasse par le
pipeline complet `anonymize()` (règles déterministes + modèle PII local OpenMed,
obligatoire en production) avant toute catégorisation.

- modèle requis mais indisponible → **503**, jamais de repli externe ;
- texte modifié par la revalidation ou jugé non sûr → **422**, aucune
  catégorisation ;
- texte inchangé et sûr → catégorisation déterministe.

Cela duplique potentiellement une inférence déjà réalisée par le parcours UI
(anonymisation puis catégorisation). Ce coût CPU est assumé : un appelant direct
de l'API ne doit pas pouvoir contourner la couche modèle.
