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

export interface ExtractionResult {
  fields: ExtractedFields;
  rawTextAnonymized: string;
  entities: Array<Record<string, unknown>>;
  confidence: Record<string, unknown>;
  warnings: string[];
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
      formData.append("engine", "tesseract");

      const result = await postFormData<ExtractionResult>("/v1/extract", formData);
      return result;
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
