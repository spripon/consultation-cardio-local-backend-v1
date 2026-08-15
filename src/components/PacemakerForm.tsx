
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import FormTabs from "./pacemaker/FormTabs";
import { usePacemakerForm } from "@/hooks/usePacemakerForm";
import { generateWordDocument } from "@/utils/wordGenerator";
import { useLanguage } from "@/contexts/LanguageContext";
import { translations } from "@/translations";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";

const PacemakerForm = () => {
  const { language, setLanguage } = useLanguage();
  const t = translations[language];

  const {
    formData,
    handleChange,
    handleDeviceTypeChange,
    handleBatteryStatusChange,
    handleReset,
  } = usePacemakerForm();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await generateWordDocument(formData, language);
      toast.success(language === 'fr' ? "Compte-rendu généré avec succès" : "Report generated successfully");
    } catch (error) {
      toast.error(language === 'fr' ? "Erreur lors de la génération du compte-rendu" : "Error generating report");
      console.error("Error generating Word document:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-4xl mx-auto space-y-8 animate-fadeIn">
      <Card className="p-6 shadow-lg border-medical-200">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-medical-800">
            {t.reportTitle}
          </h1>
          <RadioGroup
            value={language}
            onValueChange={(value: 'fr' | 'en') => setLanguage(value)}
            className="flex items-center space-x-4"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="fr" id="fr" />
              <Label htmlFor="fr">Français</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="en" id="en" />
              <Label htmlFor="en">English</Label>
            </div>
          </RadioGroup>
        </div>

        <FormTabs 
          formData={formData}
          onChange={handleChange}
          onDeviceTypeChange={handleDeviceTypeChange}
          onBatteryStatusChange={handleBatteryStatusChange}
        />

        <div className="mt-8 flex justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            onClick={handleReset}
          >
            {t.reset}
          </Button>
          <Button type="submit" className="bg-medical-600 hover:bg-medical-700">
            {t.generate}
          </Button>
        </div>
      </Card>
    </form>
  );
};

export default PacemakerForm;

