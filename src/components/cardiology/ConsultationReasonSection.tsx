
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { CardiologyFormData } from "./types";

interface ConsultationReasonSectionProps {
  formData: CardiologyFormData;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
}

const ConsultationReasonSection = ({ formData, onChange }: ConsultationReasonSectionProps) => {
  return (
    <div className="space-y-2">
      <Label htmlFor="consultationReason">Motif de consultation</Label>
      <Textarea
        id="consultationReason"
        name="consultationReason"
        value={formData.consultationReason}
        onChange={onChange}
        className="min-h-[100px]"
        placeholder="Texte libre à compléter..."
      />
    </div>
  );
};

export default ConsultationReasonSection;
