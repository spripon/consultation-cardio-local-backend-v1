
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLanguage } from "@/contexts/LanguageContext";
import { translations } from "@/translations";

interface ConclusionProps {
  memoryEvents: string;
  programModification: string;
  nextSteps: string;
  nextAppointment: string;
  summary: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const ConclusionSection = ({ 
  memoryEvents, 
  programModification, 
  nextSteps, 
  nextAppointment, 
  summary,
  onChange 
}: ConclusionProps) => {
  const { language } = useLanguage();
  const t = translations[language];

  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <div className="space-y-3">
          <Label htmlFor="memoryEvents" className="text-lg font-bold">{t.memoryEvents}</Label>
          <Input
            id="memoryEvents"
            name="memoryEvents"
            value={memoryEvents}
            onChange={onChange}
            className="w-full"
          />
        </div>
        <div className="space-y-3">
          <Label htmlFor="programModification" className="text-lg font-bold">{t.programModification}</Label>
          <Input
            id="programModification"
            name="programModification"
            value={programModification}
            onChange={onChange}
            className="w-full"
          />
        </div>
        <div className="space-y-3">
          <Label htmlFor="nextSteps" className="text-lg font-bold">{t.nextSteps}</Label>
          <Input
            id="nextSteps"
            name="nextSteps"
            value={nextSteps}
            onChange={onChange}
            className="w-full"
          />
        </div>
        <div className="space-y-3">
          <Label htmlFor="nextAppointment" className="text-lg font-bold">{t.nextAppointment}</Label>
          <Input
            id="nextAppointment"
            name="nextAppointment"
            value={nextAppointment}
            onChange={onChange}
            className="w-full"
          />
        </div>
        <div className="space-y-3">
          <Label htmlFor="summary" className="text-lg font-bold">{t.summary}</Label>
          <Input
            id="summary"
            name="summary"
            value={summary}
            onChange={onChange}
            className="w-full"
          />
        </div>
      </div>
    </div>
  );
};

export default ConclusionSection;
