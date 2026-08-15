
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { useCardiologyForm } from "@/hooks/useCardiologyForm";
import { generateCardiologyWordDocument } from "@/utils/cardiologyWordGenerator";
import { ApiKeyInput } from "./ApiKeyInput";
import { MedicalImageExtractor } from "./MedicalImageExtractor";
import PatientInfoSection from "./PatientInfoSection";
import ConsultationReasonSection from "./ConsultationReasonSection";
import RiskFactorsSection from "./RiskFactorsSection";
import ClinicalHistorySection from "./ClinicalHistorySection";
import ExaminationSection from "./ExaminationSection";
import ConclusionSection from "./ConclusionSection";

const CardiologyForm = () => {
  const {
    formData,
    handleChange,
    handleGenderChange,
    handleReset,
    openAIApiKey,
    handleOpenAIApiKeyChange,
  } = useCardiologyForm();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await generateCardiologyWordDocument(formData);
      toast.success("Compte-rendu de cardiologie généré avec succès");
    } catch (error) {
      toast.error("Erreur lors de la génération du compte-rendu");
      console.error("Error generating cardiology Word document:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-4xl mx-auto space-y-8 animate-fadeIn">
      <Card className="p-6 shadow-lg border-medical-200">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-medical-800">
            Compte-rendu de consultation de Cardiologie
          </h1>
        </div>

        <ApiKeyInput 
          openAIApiKey={openAIApiKey}
          onOpenAIApiKeyChange={handleOpenAIApiKeyChange}
        />

        <MedicalImageExtractor
          formData={formData}
          onChange={handleChange}
          openAIApiKey={openAIApiKey}
        />

        <div className="space-y-8">
          <PatientInfoSection 
            formData={formData} 
            onChange={handleChange}
            onGenderChange={handleGenderChange}
          />
          
          <ConsultationReasonSection 
            formData={formData} 
            onChange={handleChange}
          />
          
          <RiskFactorsSection 
            formData={formData} 
            onChange={handleChange}
          />
          
          <ClinicalHistorySection 
            formData={formData} 
            onChange={handleChange}
            apiKey={openAIApiKey}
          />
          
          <ExaminationSection 
            formData={formData} 
            onChange={handleChange}
            apiKey={openAIApiKey}
          />
          
          <ConclusionSection 
            formData={formData} 
            onChange={handleChange}
            apiKey={openAIApiKey}
          />
        </div>

        <div className="mt-8 flex justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            onClick={handleReset}
          >
            Réinitialiser
          </Button>
          <Button type="submit" className="bg-medical-600 hover:bg-medical-700">
            Générer le compte-rendu
          </Button>
        </div>
      </Card>
    </form>
  );
};

export default CardiologyForm;
