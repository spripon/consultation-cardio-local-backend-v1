import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ImageUpload } from '@/components/ui/image-upload';
import { useLocalExtraction } from '@/hooks/useLocalExtraction';
import { CardiologyFormData } from './types';
import { toast } from 'sonner';
import { Loader2, Sparkles } from 'lucide-react';

interface MedicalImageExtractorProps {
  formData: CardiologyFormData;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
}

export const MedicalImageExtractor = ({ 
  formData, 
  onChange, 
}: MedicalImageExtractorProps) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [anonymizedPreview, setAnonymizedPreview] = useState<string | null>(null);
  const { extractMedicalText, isExtracting, error } = useLocalExtraction();

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setAnonymizedPreview(null);
  };

  const handleFileRemove = () => {
    setSelectedFile(null);
    setAnonymizedPreview(null);
  };

  const handleExtractText = async () => {
    if (!selectedFile) {
      toast.error('Veuillez sélectionner un document');
      return;
    }

    try {
      const result = await extractMedicalText(selectedFile);
      
      // Update form data with extracted and categorized fields
      Object.entries(result.fields).forEach(([key, value]) => {
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

      setAnonymizedPreview(result.rawTextAnonymized);

      if (result.warnings.length > 0) {
        result.warnings.forEach((warning) => toast.warning(warning));
      } else {
        toast.success('Texte extrait et catégorisé avec succès !');
      }
      
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
            Extraction automatique depuis une photo ou un PDF
          </h3>
        </div>
        
        <p className="text-sm text-blue-700">
          Téléversez une photo ou un PDF d'un compte-rendu médical pour extraire et catégoriser automatiquement le texte dans les bonnes sections. Le document est traité localement.
        </p>

        <ImageUpload
          onImageSelect={handleFileSelect}
          onImageRemove={handleFileRemove}
          selectedImage={selectedFile}
          disabled={isExtracting}
          accept="image/*,application/pdf"
          capture="environment"
        />

        {error && (
          <div className="text-sm text-red-600 bg-red-50 p-3 rounded border border-red-200">
            {error}
          </div>
        )}

        {anonymizedPreview && (
          <div className="text-sm text-blue-800 bg-blue-100/50 p-3 rounded border border-blue-200">
            <p className="font-medium mb-1">Texte anonymisé :</p>
            <p className="whitespace-pre-wrap">{anonymizedPreview}</p>
          </div>
        )}

        <Button
          onClick={handleExtractText}
          disabled={!selectedFile || isExtracting}
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
      </div>
    </Card>
  );
};
