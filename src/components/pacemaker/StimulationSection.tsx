
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLanguage } from "@/contexts/LanguageContext";
import { translations } from "@/translations";

interface StimulationProps {
  parameters: string;
  stimulationPercentageAtrial: string;
  stimulationPercentageVentricular: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const StimulationSection = ({
  parameters,
  stimulationPercentageAtrial,
  stimulationPercentageVentricular,
  onChange,
}: StimulationProps) => {
  const { language } = useLanguage();
  const t = translations[language];

  return (
    <div className="space-y-8">      
      <div className="space-y-3">
        <Label htmlFor="parameters" className="text-lg font-bold">{t.parameters}</Label>
        <Input
          id="parameters"
          name="parameters"
          value={parameters}
          onChange={onChange}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-3">
          <Label htmlFor="stimulationPercentageAtrial" className="text-lg font-bold">{t.atrialStimulation}</Label>
          <Input
            id="stimulationPercentageAtrial"
            name="stimulationPercentageAtrial"
            value={stimulationPercentageAtrial}
            onChange={onChange}
          />
        </div>
        <div className="space-y-3">
          <Label htmlFor="stimulationPercentageVentricular" className="text-lg font-bold">{t.ventricularStimulation}</Label>
          <Input
            id="stimulationPercentageVentricular"
            name="stimulationPercentageVentricular"
            value={stimulationPercentageVentricular}
            onChange={onChange}
          />
        </div>
      </div>
    </div>
  );
};

export default StimulationSection;
