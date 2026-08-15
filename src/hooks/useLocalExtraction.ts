import { useState } from "react";
import { postFormData } from "@/lib/apiClient";
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
        safeToInject: result.safeToInject !== false,
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erreur lors de l'extraction";
      setError(message);
      throw err;
    } finally {
      setIsExtracting(false);
    }
  };

  return {
    extractMedicalText,
    isExtracting,
    error,
  };
};
