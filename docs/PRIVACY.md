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