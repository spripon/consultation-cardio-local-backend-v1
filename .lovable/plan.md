# Migration vers un déploiement auto-hébergé, 100% local

## Constat (vérifié dans le code)
- Frontend React 18 + Vite 5 + Tailwind + shadcn, une seule page (`src/pages/Index.tsx`) avec deux formulaires (pacemaker, cardiologie).
- `src/hooks/useOpenAIVision.ts` appelle directement `https://api.openai.com/v1/chat/completions` (gpt-4o vision) depuis le navigateur.
- `src/hooks/useSpeechToText.ts` appelle aussi `https://api.openai.com/v1/audio/transcriptions` (Whisper) — même dépendance cloud, à traiter dans la même migration.
- La clé API est saisie dans `ApiKeyInput.tsx` et stockée en clair dans `localStorage` (`useCardiologyForm.ts`).
- Génération DOCX 100% côté client (`src/utils/cardiologyWordGenerator.ts`, `docx` + `file-saver`) — à conserver telle quelle.
- Aucune PWA aujourd'hui : `public/` ne contient que favicon, og-image, placeholder ; `index.html` a encore le titre/description Lovable par défaut et le script `cdn.gpteng.co`. La PWA est donc à créer, pas à conserver.
- Aucun backend, aucune base de données dans le projet.

## Cible

```text
iPhone (PWA)  ──HTTPS──>  Nginx/Caddy (consultation.cardiologie-tarbes.org)
                              │  /            -> build Vite statique
                              │  /api/*       -> FastAPI (uvicorn, 127.0.0.1:8000)
                                                   │
                     ┌─────────────────────────────┼──────────────────────────┐
                  OCR local                 Anonymisation              Catégorisation
            (Tesseract/OCRmyPDF,           (regex MedAiCR +           (règles + NER,
             PaddleOCR/docTR)               NER OpenMed)               LLM local option.)
                                                   │
                                        PostgreSQL + fichiers chiffrés (optionnel)
```

Règle d'or : l'image brute ne quitte jamais le serveur, et l'anonymisation s'exécute **avant** toute persistance, tout log et toute étape de catégorisation.

## Étapes de migration

**Étape 0 — Nettoyage préparatoire (frontend seul)**
Retirer le script `cdn.gpteng.co`, corriger titre/description dans `index.html`, introduire `VITE_API_BASE_URL` (`.env.production` = `/api`).

**Étape 1 — Backend FastAPI + OCR local**
Nouveau dossier `backend/` hors du bundle Vite. Endpoints OCR + anonymisation + catégorisation, sans DB. Le frontend passe de OpenAI à `/api`.

**Étape 2 — Bascule frontend**
`useOpenAIVision.ts` remplacé par `useLocalExtraction.ts` ; `MedicalImageExtractor.tsx` envoie un `FormData` vers `/api/v1/extract`. Suppression de `ApiKeyInput.tsx` et de la clé en `localStorage`. `useSpeechToText.ts` pointe vers `/api/v1/transcribe` (Whisper local via faster-whisper).

**Étape 3 — Persistance optionnelle**
PostgreSQL + pièces jointes chiffrées + auth + audit, activable par variable d'environnement (`ENABLE_PERSISTENCE`). Tant qu'elle est désactivée, le service reste sans état.

**Étape 4 — Déploiement**
Docker Compose, reverse proxy, TLS, sauvegardes.

**Étape 5 — PWA**
Manifest + icônes (support écran d'accueil iPhone). Service worker offline uniquement si besoin explicite.

## Fichiers à ajouter

```text
backend/
  app/main.py                   FastAPI, CORS restreint, montage des routeurs
  app/config.py                 Settings (pydantic-settings), feature flags
  app/api/v1/extract.py         POST /extract, /ocr, /anonymize, /categorize
  app/api/v1/transcribe.py      POST /transcribe (faster-whisper local)
  app/api/v1/reports.py         CRUD comptes-rendus (étape 3)
  app/api/v1/auth.py            login / refresh / logout (étape 3)
  app/services/ocr.py           Tesseract (fra) + OCRmyPDF ; backend alternatif PaddleOCR/docTR
  app/services/preprocess.py    désinclinaison, recadrage, binarisation (OpenCV)
  app/services/anonymize.py     regex/règles MedAiCR + NER OpenMed, redaction PDF
  app/services/categorize.py    mots-clés + sectionneur + NER ; option LLM local (Ollama)
  app/services/crypto.py        chiffrement au repos des pièces jointes (AES-GCM)
  app/models/, app/schemas/     SQLAlchemy + Pydantic
  app/db/session.py, migrations/ Alembic
  tests/                        jeux d'essai OCR / anonymisation / catégorisation
  Dockerfile, requirements.txt
deploy/
  docker-compose.yml, nginx/consultation.conf (ou Caddyfile), .env.example, backup.sh
public/manifest.webmanifest, public/icons/*        (étape 5)
src/lib/apiClient.ts            fetch typé vers VITE_API_BASE_URL
src/hooks/useLocalExtraction.ts remplace useOpenAIVision.ts
```

## Fichiers à modifier / supprimer
- Modifier : `src/components/cardiology/MedicalImageExtractor.tsx` (upload vers /api, `accept="image/*,application/pdf"`, `capture="environment"` pour l'appareil photo iPhone, affichage du texte anonymisé avant injection dans le formulaire), `src/hooks/useSpeechToText.ts`, `src/hooks/useCardiologyForm.ts` (retrait de l'état clé API), `src/components/CardiologyForm.tsx` et `src/components/cardiology/CardiologyForm.tsx` (retrait de `ApiKeyInput`), `index.html`, `vite.config.ts` (proxy `/api` en dev).
- Supprimer : `src/hooks/useOpenAIVision.ts`, `src/components/cardiology/ApiKeyInput.tsx`, et la clé stockée dans `localStorage` (nettoyage au premier chargement).

Remarque : `src/components/CardiologyForm.tsx` et `src/components/cardiology/CardiologyForm.tsx` sont deux variantes ; seule celle de `cardiology/` est utilisée par `Index.tsx`. Le doublon sera supprimé lors de la migration.

## Endpoints

| Méthode | Chemin | Rôle |
| --- | --- | --- |
| POST | `/api/v1/extract` | image/PDF -> OCR -> anonymisation -> catégorisation ; renvoie les champs du formulaire |
| POST | `/api/v1/ocr` | texte brut OCR seul (debug/qualité) |
| POST | `/api/v1/anonymize` | anonymisation d'un texte, renvoie texte + entités masquées |
| POST | `/api/v1/categorize` | texte anonymisé -> champs |
| POST | `/api/v1/transcribe` | audio -> texte (Whisper local) |
| GET/POST/PUT | `/api/v1/patients`, `/api/v1/reports` | persistance optionnelle |
| POST | `/api/v1/auth/login`, `/refresh`, `/logout` | authentification |
| GET | `/api/v1/health`, `/api/v1/audit` | supervision, journal d'audit |

Réponse de `/extract` : `{ fields: { previousHistory, currentTreatment, interrogation, clinicalExamination, ecg, lastBiologyResults, conclusion, treatmentPlan }, rawTextAnonymized, entities: [...], confidence: {...}, warnings: [...] }` — clés identiques à `CardiologyFormData`, donc aucun changement de modèle côté formulaire.

## Anonymisation et catégorisation
1. Prétraitement image -> OCR (Tesseract `fra` par défaut ; PaddleOCR/docTR en repli sur manuscrit/tableaux).
2. Anonymisation en cascade : regex/règles type MedAiCR (nom, date de naissance, NIR, téléphone, adresse, IPP, e-mail) puis NER OpenMed pour le résiduel ; remplacement par jetons `[NOM]`, `[DATE]`… Pour un PDF, redaction destructive (suppression de la couche texte, pas seulement un rectangle noir).
3. Catégorisation par sectionneur : détection d'en-têtes ("Antécédents", "Traitement", "ECG", "Biologie", "Au total", "Conduite à tenir"), scores de mots-clés cardiologiques, puis NER pour les segments non attribués. Option `CATEGORIZER=llm` via Ollama local (modèle instruct léger) si les règles sont insuffisantes — jamais d'API cloud.
4. Le médecin valide toujours la proposition avant injection dans le formulaire (aucune écriture silencieuse).

## Risques de sécurité et parades
- **Fuite de données de santé** : suppression totale de l'appel OpenAI et de la clé en `localStorage` ; egress réseau du conteneur backend bloqué par défaut.
- **Anonymisation imparfaite** : l'OCR échoue -> ne jamais considérer un texte non anonymisable comme sûr ; taux de rappel mesuré sur un jeu d'essai ; validation humaine obligatoire.
- **Logs et fichiers temporaires** : aucun texte brut en log, `tmpfs` pour les fichiers intermédiaires, purge immédiate après traitement.
- **Upload** : limite de taille, contrôle MIME réel, désinfection des noms, protection contre les PDF piégés, quotas.
- **Accès** : authentification obligatoire dès l'étape 3 (sessions cookie `HttpOnly`/`Secure`/`SameSite=Strict`), rôles en table séparée, jamais sur la table profil.
- **Au repos** : disque chiffré, pièces jointes chiffrées AES-GCM avec clé hors base, PostgreSQL non exposé publiquement, sauvegardes chiffrées et testées.
- **Traçabilité** : journal d'audit en append-only (qui, quoi, quand) — exigence hébergement de données de santé.
- **Réglementaire** : un serveur auto-hébergé traitant des données de santé identifiantes relève de l'HDS ; à valider avant tout usage réel sur patients (le mode sans persistance limite fortement l'exposition).

## Détails techniques
- Python 3.12, FastAPI + uvicorn derrière Nginx/Caddy ; traitements OCR en tâche de fond bornée (pool de workers) pour ne pas bloquer l'event loop.
- Images Docker : `frontend` (build Vite servi en statique), `backend` (Tesseract, poppler, OCRmyPDF), `db` (PostgreSQL 16), volume `attachments`.
- TLS via Caddy (automatique) ou Certbot avec Nginx ; en-têtes HSTS, CSP, `X-Content-Type-Options`.
- iPhone : `<input type="file" accept="image/*,application/pdf" capture="environment">` ; compression client avant envoi pour les gros clichés.
- Aucun changement fonctionnel du générateur DOCX : il continue de tourner dans le navigateur.
