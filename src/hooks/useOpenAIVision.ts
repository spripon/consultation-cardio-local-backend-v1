import { useState } from 'react';
import { CardiologyFormData } from '@/components/cardiology/types';

interface ExtractedData {
  previousHistory?: string;
  currentTreatment?: string;
  interrogation?: string;
  clinicalExamination?: string;
  ecg?: string;
  lastBiologyResults?: string;
  conclusion?: string;
  treatmentPlan?: string;
}

export const useOpenAIVision = () => {
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const extractMedicalText = async (
    imageFile: File, 
    apiKey: string
  ): Promise<ExtractedData> => {
    if (!apiKey) {
      throw new Error('Clé API OpenAI requise');
    }

    setIsExtracting(true);
    setError(null);

    try {
      // Convert image to base64
      const base64Image = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const result = reader.result as string;
          // Remove data:image/...;base64, prefix
          const base64 = result.split(',')[1];
          resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(imageFile);
      });

      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'gpt-4o',
          messages: [
            {
              role: 'user',
              content: [
                {
                  type: 'text',
                  text: `Analysez cette image d'un compte-rendu médical de cardiologie et extrayez le texte en le catégorisant dans les sections appropriées. Retournez uniquement un JSON valide avec les clés suivantes (utilisez uniquement les clés pour lesquelles vous trouvez du contenu pertinent):

- "previousHistory": pour les antécédents et comorbidités principales
- "currentTreatment": pour le traitement habituel
- "interrogation": pour les informations à l'interrogatoire
- "clinicalExamination": pour l'examen clinique
- "ecg": pour les résultats ECG
- "lastBiologyResults": pour le dernier bilan biologique
- "conclusion": pour la conclusion diagnostique (AU TOTAL)
- "treatmentPlan": pour la conduite à tenir

Extraire le texte exactement comme écrit, en conservant la terminologie médicale précise. Si une section n'est pas présente, ne pas inclure la clé dans le JSON.`
                },
                {
                  type: 'image_url',
                  image_url: {
                    url: `data:image/jpeg;base64,${base64Image}`,
                    detail: 'high'
                  }
                }
              ]
            }
          ],
          max_tokens: 2000,
          temperature: 0.1
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Erreur lors de l\'analyse de l\'image');
      }

      const data = await response.json();
      const content = data.choices[0]?.message?.content;

      if (!content) {
        throw new Error('Aucune réponse reçue de l\'API OpenAI');
      }

      // Parse JSON response
      try {
        const extractedData = JSON.parse(content);
        return extractedData;
      } catch (parseError) {
        // If JSON parsing fails, try to extract JSON from text
        const jsonMatch = content.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          return JSON.parse(jsonMatch[0]);
        }
        throw new Error('Format de réponse invalide');
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue';
      setError(errorMessage);
      throw err;
    } finally {
      setIsExtracting(false);
    }
  };

  return {
    extractMedicalText,
    isExtracting,
    error
  };
};