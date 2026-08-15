
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { CardiologyFormData } from "./types";

interface PatientInfoSectionProps {
  formData: CardiologyFormData;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onGenderChange: (value: 'Monsieur' | 'Madame') => void;
}

const PatientInfoSection = ({ formData, onChange, onGenderChange }: PatientInfoSectionProps) => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="date">Date de consultation</Label>
          <Input
            id="date"
            name="date"
            type="date"
            value={formData.date}
            onChange={onChange}
            className="w-full"
          />
        </div>

        <div className="space-y-2">
          <Label>Civilité</Label>
          <RadioGroup
            value={formData.gender}
            onValueChange={(value: 'Monsieur' | 'Madame') => onGenderChange(value)}
            className="flex space-x-4"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="Monsieur" id="monsieur" />
              <Label htmlFor="monsieur">Monsieur</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="Madame" id="madame" />
              <Label htmlFor="madame">Madame</Label>
            </div>
          </RadioGroup>
        </div>

        <div className="space-y-2">
          <Label htmlFor="patientName">Nom du patient</Label>
          <Input
            id="patientName"
            name="patientName"
            value={formData.patientName}
            onChange={onChange}
            className="w-full"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="birthDate">Date de naissance</Label>
          <Input
            id="birthDate"
            name="birthDate"
            type="date"
            value={formData.birthDate}
            onChange={onChange}
            className="w-full"
          />
        </div>
      </div>
    </div>
  );
};

export default PatientInfoSection;
