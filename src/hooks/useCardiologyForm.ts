
import { useState } from "react";
import { CardiologyFormData } from "@/components/cardiology/types";

export const useCardiologyForm = () => {
  const getCurrentDate = () => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  };

  const [formData, setFormData] = useState<CardiologyFormData>({
    date: getCurrentDate(),
    patientName: "",
    gender: "Monsieur",
    birthDate: "",
    consultationReason: "",
    cardiovascularRiskFactors: {
      hypercholesterolemia: false,
      hypertension: false,
      diabetesType2: false,
      overweight: false,
      overweightDetails: "",
      smoking: false,
      smokingDetails: "",
      coronaryHeredity: false,
      coronaryHeredityDetails: "",
    },
    previousHistory: "",
    currentTreatment: "",
    interrogation: "Mr/Mme est asymptomatique du point de vue cardiaque, notamment pas de douleur thoracique angineuse signalée, pas de dyspnée inhabituelle, pas de palpitation ni malaise syncopal",
    clinicalExamination: "TA = … mmHg, auscultation cardiaque et pulmonaire normale, absence de signe d'insuffisance cardiaque gauche ni droite ; pas de signe de phlébite ; pas de souffle carotidien à l'auscultation cervicale ; pouls artériels périphériques perçus.\nDonc un examen clinique cardiologique normal",
    ecg: "s'inscrit en … à …/min, QRS fins, axe QRS = … , P-R normal, QT corrigé normal. Absence de signe d'hypertrophie ventriculaire ni autre élément de dilatation cavitaire. Pas de séquelle de nécrose. La repolarisation est normale",
    lastBiologyResults: "réalisé … retrouve :\n-NFS\n-ionogramme et fonction renale normale (notamment K =… ; créatinine = …)\n-bilan hépatique normal\n-bilan thyroidien normal : TSH = …\n-CRP négatif a …\n-glycemie a jeun normale a …………...\n-bilan lipidique : cholesterol total = … ; LDL = … ; HDL =… ; TG = …",
    conclusion: "Etat cardiaque stable...",
    treatmentPlan: "J'envisage pour...",
    nextAppointment: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const target = e.target as HTMLInputElement;
      if (name.startsWith('cardiovascularRiskFactors.')) {
        const field = name.split('.')[1];
        setFormData(prev => ({
          ...prev,
          cardiovascularRiskFactors: {
            ...prev.cardiovascularRiskFactors,
            [field]: target.checked,
          },
        }));
      }
    } else if (name.startsWith('cardiovascularRiskFactors.')) {
      const field = name.split('.')[1];
      setFormData(prev => ({
        ...prev,
        cardiovascularRiskFactors: {
          ...prev.cardiovascularRiskFactors,
          [field]: value,
        },
      }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleGenderChange = (value: 'Monsieur' | 'Madame') => {
    setFormData(prev => ({ ...prev, gender: value }));
  };

  const handleReset = () => {
    setFormData({
      date: getCurrentDate(),
      patientName: "",
      gender: "Monsieur",
      birthDate: "",
      consultationReason: "",
      cardiovascularRiskFactors: {
        hypercholesterolemia: false,
        hypertension: false,
        diabetesType2: false,
        overweight: false,
        overweightDetails: "",
        smoking: false,
        smokingDetails: "",
        coronaryHeredity: false,
        coronaryHeredityDetails: "",
      },
      previousHistory: "",
      currentTreatment: "",
      interrogation: "Mr/Mme est asymptomatique du point de vue cardiaque, notamment pas de douleur thoracique angineuse signalée, pas de dyspnée inhabituelle, pas de palpitation ni malaise syncopal",
      clinicalExamination: "TA = … mmHg, auscultation cardiaque et pulmonaire normale, absence de signe d'insuffisance cardiaque gauche ni droite ; pas de signe de phlébite ; pas de souffle carotidien à l'auscultation cervicale ; pouls artériels périphériques perçus.\nDonc un examen clinique cardiologique normal",
      ecg: "s'inscrit en … à …/min, QRS fins, axe QRS = … , P-R normal, QT corrigé normal. Absence de signe d'hypertrophie ventriculaire ni autre élément de dilatation cavitaire. Pas de séquelle de nécrose. La repolarisation est normale",
      lastBiologyResults: "réalisé … retrouve :\n-NFS\n-ionogramme et fonction renale normale (notamment K =… ; créatinine = …)\n-bilan hépatique normal\n-bilan thyroidien normal : TSH = …\n-CRP négatif a …\n-glycemie a jeun normale a …………...\n-bilan lipidique : cholesterol total = … ; LDL = … ; HDL =… ; TG = …",
      conclusion: "Etat cardiaque stable...",
      treatmentPlan: "J'envisage pour...",
      nextAppointment: "",
    });
  };

  const [openAIApiKey, setOpenAIApiKey] = useState(() => {
    return localStorage.getItem('openai-api-key') || '';
  });

  const handleOpenAIApiKeyChange = (key: string) => {
    setOpenAIApiKey(key);
    localStorage.setItem('openai-api-key', key);
  };

  return {
    formData,
    handleChange,
    handleGenderChange,
    handleReset,
    openAIApiKey,
    handleOpenAIApiKeyChange,
  };
};
