import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { CardiologyFormData } from "./types";

interface RiskFactorsSectionProps {
  formData: CardiologyFormData;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const RiskFactorsSection = ({ formData, onChange }: RiskFactorsSectionProps) => {
  const handleCheckboxChange = (field: string, checked: boolean) => {
    const event = {
      target: {
        name: `cardiovascularRiskFactors.${field}`,
        type: 'checkbox',
        checked,
      },
    } as React.ChangeEvent<HTMLInputElement>;
    onChange(event);
  };

  return (
    <div className="space-y-6">
      <Label className="text-base font-medium">Facteurs de risque cardiovasculaire</Label>
      
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Checkbox
            id="hypercholesterolemia"
            checked={formData.cardiovascularRiskFactors.hypercholesterolemia}
            onCheckedChange={(checked) => handleCheckboxChange('hypercholesterolemia', checked as boolean)}
          />
          <Label htmlFor="hypercholesterolemia">Hypercholestérolémie</Label>
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox
            id="hypertension"
            checked={formData.cardiovascularRiskFactors.hypertension}
            onCheckedChange={(checked) => handleCheckboxChange('hypertension', checked as boolean)}
          />
          <Label htmlFor="hypertension">HTA</Label>
        </div>

        <div className="flex items-center space-x-2">
          <Checkbox
            id="diabetesType2"
            checked={formData.cardiovascularRiskFactors.diabetesType2}
            onCheckedChange={(checked) => handleCheckboxChange('diabetesType2', checked as boolean)}
          />
          <Label htmlFor="diabetesType2">Diabète type II</Label>
        </div>

        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="overweight"
              checked={formData.cardiovascularRiskFactors.overweight}
              onCheckedChange={(checked) => handleCheckboxChange('overweight', checked as boolean)}
            />
            <Label htmlFor="overweight">Surpoids</Label>
          </div>
          {formData.cardiovascularRiskFactors.overweight && (
            <Input
              name="cardiovascularRiskFactors.overweightDetails"
              value={formData.cardiovascularRiskFactors.overweightDetails}
              onChange={onChange}
              placeholder="... Kg / ... m"
              className="ml-6 w-auto"
            />
          )}
        </div>

        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="smoking"
              checked={formData.cardiovascularRiskFactors.smoking}
              onCheckedChange={(checked) => handleCheckboxChange('smoking', checked as boolean)}
            />
            <Label htmlFor="smoking">Tabac</Label>
          </div>
          {formData.cardiovascularRiskFactors.smoking && (
            <Input
              name="cardiovascularRiskFactors.smokingDetails"
              value={formData.cardiovascularRiskFactors.smokingDetails}
              onChange={onChange}
              placeholder="... cg/jour depuis ..."
              className="ml-6 w-auto"
            />
          )}
        </div>

        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="coronaryHeredity"
              checked={formData.cardiovascularRiskFactors.coronaryHeredity}
              onCheckedChange={(checked) => handleCheckboxChange('coronaryHeredity', checked as boolean)}
            />
            <Label htmlFor="coronaryHeredity">Hérédité coronarienne</Label>
          </div>
          {formData.cardiovascularRiskFactors.coronaryHeredity && (
            <Input
              name="cardiovascularRiskFactors.coronaryHeredityDetails"
              value={formData.cardiovascularRiskFactors.coronaryHeredityDetails}
              onChange={onChange}
              placeholder="Détails..."
              className="ml-6 w-auto"
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default RiskFactorsSection;
