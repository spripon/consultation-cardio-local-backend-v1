/**
 * Nettoyage des artefacts de l'ancienne architecture cloud.
 *
 * Ce projet ne contient plus aucun appel à un service d'IA externe : les clés API
 * éventuellement stockées par une version précédente de l'application sont
 * supprimées du navigateur au démarrage.
 */
const LEGACY_KEYS = [
  "openAIApiKey",
  "openaiApiKey",
  "OPENAI_API_KEY",
  "openai-api-key",
  "openai_api_key",
] as const;

export function purgeLegacyCloudKeys(): void {
  for (const key of LEGACY_KEYS) {
    try {
      localStorage.removeItem(key);
      sessionStorage.removeItem(key);
    } catch {
      // Stockage indisponible (mode privé strict) : rien à nettoyer.
    }
  }
}