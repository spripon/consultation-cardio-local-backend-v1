
import ClinicalHistorySection from "./ClinicalHistorySection";
import ExaminationSection from "./ExaminationSection";
import ConsultationReasonSection from "./ConsultationReasonSection";
import { CardiologyFormData } from "./types";

interface ClinicalSectionsProps {
  formData: CardiologyFormData;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  apiKey?: string;
}

const ClinicalSections = ({ formData, onChange, apiKey }: ClinicalSectionsProps) => {
  return (
    <div className="space-y-6">
      <ConsultationReasonSection 
        formData={formData}
        onChange={onChange}
      />
      
      <ClinicalHistorySection 
        formData={formData}
        onChange={onChange}
        apiKey={apiKey}
      />
      
      <ExaminationSection 
        formData={formData}
        onChange={onChange}
        apiKey={apiKey}
      />
    </div>
  );
};

export default ClinicalSections;
