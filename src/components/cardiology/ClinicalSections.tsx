
import ClinicalHistorySection from "./ClinicalHistorySection";
import ExaminationSection from "./ExaminationSection";
import ConsultationReasonSection from "./ConsultationReasonSection";
import { CardiologyFormData } from "./types";

interface ClinicalSectionsProps {
  formData: CardiologyFormData;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
}

const ClinicalSections = ({ formData, onChange }: ClinicalSectionsProps) => {
  return (
    <div className="space-y-6">
      <ConsultationReasonSection 
        formData={formData}
        onChange={onChange}
      />
      
      <ClinicalHistorySection 
        formData={formData}
        onChange={onChange}
      />
      
      <ExaminationSection 
        formData={formData}
        onChange={onChange}
      />
    </div>
  );
};

export default ClinicalSections;
