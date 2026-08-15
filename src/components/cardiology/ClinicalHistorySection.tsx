
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { DictationButton } from "@/components/ui/dictation-button";
import { CardiologyFormData } from "./types";

interface ClinicalHistorySectionProps {
  formData: CardiologyFormData;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
}

const ClinicalHistorySection = ({ formData, onChange }: ClinicalHistorySectionProps) => {
  const handleDictation = (fieldName: string) => (text: string) => {
    const event = {
      target: {
        name: fieldName,
        value: formData[fieldName as keyof CardiologyFormData] + (formData[fieldName as keyof CardiologyFormData] ? '\n' : '') + text,
      }
    } as React.ChangeEvent<HTMLTextAreaElement>;
    onChange(event);
  };
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="previousHistory">Antécédents et comorbidités principales</Label>
          <DictationButton 
            onTranscript={handleDictation('previousHistory')}
          />
        </div>
        <Textarea
          id="previousHistory"
          name="previousHistory"
          value={formData.previousHistory}
          onChange={onChange}
          className="min-h-[100px]"
          placeholder="Texte libre à compléter..."
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="currentTreatment">Traitement habituel</Label>
          <DictationButton 
            onTranscript={handleDictation('currentTreatment')}
          />
        </div>
        <Textarea
          id="currentTreatment"
          name="currentTreatment"
          value={formData.currentTreatment}
          onChange={onChange}
          className="min-h-[100px]"
          placeholder="Texte libre à compléter..."
        />
      </div>
    </div>
  );
};

export default ClinicalHistorySection;
