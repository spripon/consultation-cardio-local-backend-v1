
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { DictationButton } from "@/components/ui/dictation-button";
import { CardiologyFormData } from "./types";

interface ConclusionSectionProps {
  formData: CardiologyFormData;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => void;
}

const ConclusionSection = ({ formData, onChange }: ConclusionSectionProps) => {
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
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="conclusion">AU TOTAL</Label>
          <DictationButton 
            onTranscript={handleDictation('conclusion')}
          />
        </div>
        <Textarea
          id="conclusion"
          name="conclusion"
          value={formData.conclusion}
          onChange={onChange}
          className="min-h-[120px]"
          placeholder="Etat cardiaque stable..."
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="treatmentPlan">Conduite à tenir</Label>
          <DictationButton 
            onTranscript={handleDictation('treatmentPlan')}
          />
        </div>
        <Textarea
          id="treatmentPlan"
          name="treatmentPlan"
          value={formData.treatmentPlan}
          onChange={onChange}
          className="min-h-[120px]"
          placeholder="J'envisage pour..."
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="nextAppointment">Prochain rendez-vous (délai)</Label>
        <Input
          id="nextAppointment"
          name="nextAppointment"
          value={formData.nextAppointment}
          onChange={onChange}
          placeholder="dans ... mois/semaines"
          className="w-full"
        />
      </div>
    </div>
  );
};

export default ConclusionSection;
