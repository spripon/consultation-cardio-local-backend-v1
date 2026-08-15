
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { DictationButton } from "@/components/ui/dictation-button";
import { CardiologyFormData } from "./types";

interface ExaminationSectionProps {
  formData: CardiologyFormData;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
}

const ExaminationSection = ({ formData, onChange }: ExaminationSectionProps) => {
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
          <Label htmlFor="interrogation">À l'interrogatoire</Label>
          <DictationButton 
            onTranscript={handleDictation('interrogation')}
          />
        </div>
        <Textarea
          id="interrogation"
          name="interrogation"
          value={formData.interrogation}
          onChange={onChange}
          className="min-h-[120px]"
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="clinicalExamination">À l'examen clinique</Label>
          <DictationButton 
            onTranscript={handleDictation('clinicalExamination')}
          />
        </div>
        <Textarea
          id="clinicalExamination"
          name="clinicalExamination"
          value={formData.clinicalExamination}
          onChange={onChange}
          className="min-h-[120px]"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="ecg">L'ECG</Label>
        <Textarea
          id="ecg"
          name="ecg"
          value={formData.ecg}
          onChange={onChange}
          className="min-h-[120px]"
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="lastBiologyResults">Le dernier bilan biologique</Label>
          <DictationButton 
            onTranscript={handleDictation('lastBiologyResults')}
          />
        </div>
        <Textarea
          id="lastBiologyResults"
          name="lastBiologyResults"
          value={formData.lastBiologyResults}
          onChange={onChange}
          className="min-h-[200px]"
        />
      </div>
    </div>
  );
};

export default ExaminationSection;
