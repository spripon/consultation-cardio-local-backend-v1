import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ImageUpload } from '@/components/ui/image-upload';
import { LocalProcessingNotice } from '@/components/LocalProcessingNotice';
import { useLocalExtraction, type ExtractionResult } from '@/hooks/useLocalExtraction';
import { CardiologyFormData } from './types';
import { toast } from 'sonner';
import { AlertTriangle, Check, Loader2, ShieldCheck, Sparkles, X } from 'lucide-react';

const FIELD_LABELS: Record<string, string> = {
  previousHistory: 'Antécédents',
  currentTreatment: 'Traitement actuel',
  interrogation: 'Interrogatoire',
  clinicalExamination: 'Examen clinique',
  ecg: 'ECG',
  lastBiologyResults: 'Biologie',
  conclusion: 'Conclusion',
  treatmentPlan: 'Conduite à tenir',
};

interface MedicalImageExtractorProps {
  formData: CardiologyFormData;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
}

export const MedicalImageExtractor = ({ 
  formData, 
  onChange, 
}: MedicalImageExtractorProps) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [pending, setPending] = useState<ExtractionResult | null>(null);
  const [reviewText, setReviewText] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const { extractMedicalText, isExtracting, error } = useLocalExtraction();

  const resetReview = () => {
    setPending(null);
    setReviewText('');
    setConfirmed(false);
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    resetReview();
  };

  const handleFileRemove = () => {
    setSelectedFile(null);
    resetReview();
  };

  const handleExtractText = async () => {
    if (!selectedFile) {
      toast.error('Veuillez sélectionner un document');
      return;
    }

    try {
      const result = await extractMedicalText(selectedFile);

      // Aucune injection automatique : la relecture humaine est obligatoire.
      setPending(result);
      setReviewText(result.rawTextAnonymized);
      setConfirmed(false);

      result.warnings.forEach((warning) => toast.warning(warning));
      if (result.safeToInject) {
        toast.info('Relisez le texte anonymisé, puis validez pour l\'insérer.');
      } else {
        toast.error('Identifiant résiduel détecté : corrigez le texte avant validation.');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors de l\'extraction';
      toast.error(`Erreur: ${errorMessage}`);
    }
  };

  const handleConfirmInjection = () => {
    if (!pending || !confirmed) return;

    const entries = Object.entries(pending.fields).filter(
      ([, value]) => typeof value === 'string' && value.trim(),
    );

    if (entries.length === 0) {
      toast.warning('Aucune rubrique catégorisée : recopiez manuellement le texte relu.');
      return;
    }

    entries.forEach(([name, value]) => {
      onChange({
        target: { name, value: value as string },
      } as React.ChangeEvent<HTMLTextAreaElement>);
    });

    toast.success(`${entries.length} rubrique(s) insérée(s) après validation.`);
    resetReview();
    setSelectedFile(null);
  };

  const percent = (value?: number) => `${Math.round((value ?? 0) * 100)} %`;

  return (
    <Card className="p-6 mb-6 border-border bg-muted/40">
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold text-foreground">
            Extraction locale depuis une photo ou un PDF
          </h3>
        </div>

        <p className="text-sm text-muted-foreground">
          Le document est lu, anonymisé et catégorisé entièrement sur ce serveur : aucune donnée ne
          sort de l'établissement. L'anonymisation automatique n'est jamais garantie — votre
          relecture est obligatoire avant insertion.
        </p>

        <LocalProcessingNotice />

        <ImageUpload
          onImageSelect={handleFileSelect}
          onImageRemove={handleFileRemove}
          selectedImage={selectedFile}
          disabled={isExtracting}
          accept="image/jpeg,image/png,image/webp,image/tiff,image/heic,application/pdf"
          capture="environment"
        />

        {error && (
          <div className="flex items-start gap-2 rounded border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <Button
          onClick={handleExtractText}
          disabled={!selectedFile || isExtracting}
          className="w-full"
        >
          {isExtracting ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Traitement local en cours...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4 mr-2" />
              Analyser le document localement
            </>
          )}
        </Button>

        {pending && (
          <div className="space-y-4 rounded-lg border border-border bg-background p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold text-foreground">
                Étape de validation humaine
              </span>
              <Badge variant="secondary">OCR {percent(pending.confidence?.ocr)}</Badge>
              <Badge variant="secondary">
                Anonymisation {percent(pending.confidence?.anonymization)}
              </Badge>
              <Badge variant="secondary">
                Catégorisation {percent(pending.confidence?.categorization)}
              </Badge>
              {pending.entities.length > 0 && (
                <Badge variant="outline">{pending.entities.length} identifiant(s) masqué(s)</Badge>
              )}
            </div>

            {!pending.safeToInject && (
              <div className="flex items-start gap-2 rounded border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>
                  Des données potentiellement identifiantes subsistent. Corrigez-les ci-dessous
                  avant toute insertion.
                </span>
              </div>
            )}

            {pending.warnings.length > 0 && (
              <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                {pending.warnings.map((warning, index) => (
                  <li key={`${index}-${warning}`}>{warning}</li>
                ))}
              </ul>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground" htmlFor="anonymized-review">
                Texte anonymisé à relire
              </label>
              <Textarea
                id="anonymized-review"
                value={reviewText}
                onChange={(event) => setReviewText(event.target.value)}
                rows={10}
                className="font-mono text-xs"
              />
            </div>

            <div className="space-y-1 text-sm">
              <p className="font-medium text-foreground">Rubriques proposées</p>
              {Object.entries(pending.fields).filter(([, v]) => (v as string)?.trim()).length ===
              0 ? (
                <p className="text-muted-foreground">
                  Aucune rubrique détectée automatiquement.
                </p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(pending.fields)
                    .filter(([, value]) => (value as string)?.trim())
                    .map(([name]) => (
                      <Badge key={name} variant="outline">
                        {FIELD_LABELS[name] ?? name}
                      </Badge>
                    ))}
                </div>
              )}
            </div>

            <label className="flex items-start gap-2 text-sm text-foreground">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(event) => setConfirmed(event.target.checked)}
                className="mt-1 h-4 w-4 accent-primary"
              />
              <span>
                J'ai relu le texte ci-dessus et je confirme qu'il ne contient plus de donnée
                identifiante.
              </span>
            </label>

            <div className="flex flex-col gap-2 sm:flex-row">
              <Button
                onClick={handleConfirmInjection}
                disabled={!confirmed}
                className="flex-1"
              >
                <Check className="mr-2 h-4 w-4" />
                Valider et insérer dans le formulaire
              </Button>
              <Button variant="outline" onClick={resetReview} className="flex-1">
                <X className="mr-2 h-4 w-4" />
                Rejeter l'extraction
              </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};
