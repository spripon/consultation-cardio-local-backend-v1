
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import CardiologyFormTabs from "./cardiology/CardiologyFormTabs";
import { MedicalImageExtractor } from "./cardiology/MedicalImageExtractor";
import { useCardiologyForm } from "@/hooks/useCardiologyForm";

const CardiologyForm = () => {
  const {
    formData,
    handleChange,
    handleGenderChange,
    handleReset,
  } = useCardiologyForm();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement Word document generation for cardiology consultation
    toast.success("Fonctionnalité de génération en cours de développement");
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-4xl mx-auto space-y-8 animate-fadeIn">
      <Card className="p-6 shadow-lg border-medical-200">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-medical-800">
            Compte-rendu de consultation de Cardiologie
          </h1>
        </div>

        <MedicalImageExtractor
          formData={formData}
          onChange={handleChange}
        />

        <CardiologyFormTabs 
          formData={formData}
          onChange={handleChange}
          onGenderChange={handleGenderChange}
        />

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
