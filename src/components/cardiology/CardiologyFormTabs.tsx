
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import PatientInfoSection from "./PatientInfoSection";
import RiskFactorsSection from "./RiskFactorsSection";
import ClinicalSections from "./ClinicalSections";
import ConclusionSection from "./ConclusionSection";
import { CardiologyFormData } from "./types";

interface CardiologyFormTabsProps {
  formData: CardiologyFormData;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  onGenderChange: (value: 'Monsieur' | 'Madame') => void;
  apiKey?: string;
}

const CardiologyFormTabs = ({ formData, onChange, onGenderChange, apiKey }: CardiologyFormTabsProps) => {
  return (
    <Tabs defaultValue="patient" className="w-full">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="patient">Patient</TabsTrigger>
        <TabsTrigger value="risks">Facteurs de risque</TabsTrigger>
        <TabsTrigger value="clinical">Examen clinique</TabsTrigger>
        <TabsTrigger value="conclusion">Conclusion</TabsTrigger>
      </TabsList>

      <TabsContent value="patient" className="mt-6">
        <PatientInfoSection 
          formData={formData} 
          onChange={onChange}
          onGenderChange={onGenderChange}
        />
      </TabsContent>

      <TabsContent value="risks" className="mt-6">
        <RiskFactorsSection 
          formData={formData} 
          onChange={onChange}
        />
      </TabsContent>

      <TabsContent value="clinical" className="mt-6">
        <ClinicalSections 
          formData={formData} 
          onChange={onChange}
          apiKey={apiKey}
        />
      </TabsContent>

      <TabsContent value="conclusion" className="mt-6">
        <ConclusionSection 
          formData={formData} 
          onChange={onChange}
          apiKey={apiKey}
        />
      </TabsContent>
    </Tabs>
  );
};

export default CardiologyFormTabs;
