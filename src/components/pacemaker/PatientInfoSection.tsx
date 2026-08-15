
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLanguage } from "@/contexts/LanguageContext";
import { translations } from "@/translations";

interface PatientInfoProps {
  date: string;
  patientName: string;
  birthDate: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const PatientInfoSection = ({ date, patientName, birthDate, onChange }: PatientInfoProps) => {
  const { language } = useLanguage();
  const t = translations[language];

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="space-y-3">
          <Label htmlFor="date" className="text-lg font-bold">{t.dateControl}</Label>
          <Input
            id="date"
            name="date"
            type="date"
            value={date}
            onChange={onChange}
            className="w-full"
          />
        </div>
        <div className="space-y-3">
          <Label htmlFor="patientName" className="text-lg font-bold">{t.patient}</Label>
          <Input
            id="patientName"
            name="patientName"
            value={patientName}
            onChange={onChange}
            className="w-full"
          />
        </div>
        <div className="space-y-3">
          <Label htmlFor="birthDate" className="text-lg font-bold">{t.birthDate}</Label>
          <Input
            id="birthDate"
            name="birthDate"
            type="text"
            placeholder={language === 'fr' ? "JJ/MM/AAAA" : "DD/MM/YYYY"}
            pattern="\d{2}/\d{2}/\d{4}"
            value={birthDate}
            onChange={onChange}
            className="w-full"
          />
        </div>
      </div>
    </div>
  );
};

export default PatientInfoSection;
