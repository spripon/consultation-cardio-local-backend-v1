import { useState } from "react";
import { postFormData, postJson } from "@/lib/apiClient";
import { CardiologyFormData } from "@/components/cardiology/types";

export type ExtractedFields = Partial<
  Pick<
    CardiologyFormData,
    | "previousHistory"
    | "currentTreatment"
    | "interrogation"
    | "clinicalExamination"
    | "ecg"
    | "lastBiologyResults"
    | "conclusion"
    | "treatmentPlan"
  >
>;

export interface ExtractionEntity {
  type: string;
  placeholder: string;
  source: string;
  confidence: number;
}

export interface ExtractionConfidence {
  ocr: number;
  anonymization: number;
  categorization: number;
}

export interface ExtractionResult {
  fields: ExtractedFields;
  rawTextAnonymized: string;
  entities: ExtractionEntity[];
  confidence: ExtractionConfidence;
  warnings: string[];
  /** Toujours true : la relecture par un soignant est obligatoire. */
  requiresHumanValidation: boolean;
  /** false si un identifiant résiduel a été détecté : injection interdite. */
  safeToInject: boolean;
  debugRawText?: string | null;
}

export interface AnonymizeResult {
  textAnonymized: string;
  entities: ExtractionEntity[];
  warnings: string[];
  confidence: number;
  requiresHumanValidation: boolean;
  safeToInject: boolean;
}

export interface CategorizeResult {
  fields: ExtractedFields;
  confidence: number;
  warnings: string[];
  requiresHumanValidation: boolean;
}

export const useLocalExtraction = () => {
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const extractMedicalText = async (file: File): Promise<ExtractionResult> => {
    setIsExtracting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const result = await postFormData<ExtractionResult>("/v1/extract", formData);
      return {
        ...result,
        entities: result.entities ?? [],
        warnings: result.warnings ?? [],
        requiresHumanValidation: true,
        // Fail-closed : une valeur absente n'autorise JAMAIS l'injection.
        safeToInject: result.safeToInject === true,
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erreur lors de l'extraction";
      setError(message);
      throw err;
    } finally {
      setIsExtracting(false);
    }
  };

  /** Repasse le texte relu par le médecin dans le pipeline local d'anonymisation. */
  const revalidateText = async (text: string): Promise<AnonymizeResult> => {
    const result = await postJson<AnonymizeResult>("/v1/anonymize", { text });
    return {
      ...result,
      entities: result.entities ?? [],
      warnings: result.warnings ?? [],
      safeToInject: result.safeToInject === true,
      requiresHumanValidation: true,
    };
  };

  /** Catégorise UNIQUEMENT un texte déjà revalidé côté serveur. */
  const categorizeText = async (textAnonymized: string): Promise<CategorizeResult> => {
    const result = await postJson<CategorizeResult>("/v1/categorize", { textAnonymized });
    return {
      ...result,
      fields: result.fields ?? {},
      warnings: result.warnings ?? [],
      requiresHumanValidation: true,
    };
  };

  return {
    extractMedicalText,
    revalidateText,
    categorizeText,
    isExtracting,
    error,
  };
};
