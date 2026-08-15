import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ImageUpload } from '@/components/ui/image-upload';
import { useOpenAIVision } from '@/hooks/useOpenAIVision';
import { CardiologyFormData } from './types';
import { toast } from 'sonner';
import { Loader2, Sparkles } from 'lucide-react';

interface MedicalImageExtractorProps {
  formData: CardiologyFormData;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  openAIApiKey?: string;
}

export const MedicalImageExtractor = ({ 
  formData, 
  onChange, 
  openAIApiKey 
}: MedicalImageExtractorProps) => {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const { extractMedicalText, isExtracting, error } = useOpenAIVision();

  const handleImageSelect = (file: File) => {
    setSelectedImage(file);
  };

  const handleImageRemove = () => {
    setSelectedImage(null);
  };

  const handleExtractText = async () => {
    if (!selectedImage) {
      toast.error('Veuillez sélectionner une image');
      return;
    }

    if (!openAIApiKey) {
      toast.error('Clé API OpenAI requise');
      return;
    }

    try {
      const extractedData = await extractMedicalText(selectedImage, openAIApiKey);
      
      // Update form data with extracted information
      Object.entries(extractedData).forEach(([key, value]) => {
        if (value && typeof value === 'string') {
          const event = {
            target: {
              name: key,
              value: value
            }
          } as React.ChangeEvent<HTMLTextAreaElement>;
          onChange(event);
        }
      });

      toast.success('Texte extrait et catégorisé avec succès !');
      setSelectedImage(null); // Clear image after successful extraction
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors de l\'extraction';
      toast.error(`Erreur: ${errorMessage}`);
    }
  };

  return (
    <Card className="p-6 mb-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Sparkles className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-blue-900">
            Extraction automatique depuis une photo
          </h3>
        </div>
        
        <p className="text-sm text-blue-700">
          Téléversez une photo d'un compte-rendu médical pour extraire et catégoriser automatiquement le texte dans les bonnes sections.
        </p>

        <ImageUpload
          onImageSelect={handleImageSelect}
          onImageRemove={handleImageRemove}
          selectedImage={selectedImage}
          disabled={isExtracting}
        />

        {error && (
          <div className="text-sm text-red-600 bg-red-50 p-3 rounded border border-red-200">
            {error}
          </div>
        )}

        <Button
          onClick={handleExtractText}
          disabled={!selectedImage || isExtracting || !openAIApiKey}
          className="w-full bg-blue-600 hover:bg-blue-700"
        >
          {isExtracting ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Extraction en cours...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4 mr-2" />
              Extraire et catégoriser le texte
            </>
          )}
        </Button>

        {!openAIApiKey && (
          <p className="text-xs text-amber-600 bg-amber-50 p-2 rounded border border-amber-200">
            ⚠️ Clé API OpenAI requise pour utiliser cette fonctionnalité
          </p>
        )}
      </div>
    </Card>
  );
};