
export interface CardiologyFormData {
  date: string;
  patientName: string;
  gender: 'Monsieur' | 'Madame';
  birthDate: string;
  consultationReason: string;
  cardiovascularRiskFactors: {
    hypercholesterolemia: boolean;
    hypertension: boolean;
    diabetesType2: boolean;
    overweight: boolean;
    overweightDetails: string;
    smoking: boolean;
    smokingDetails: string;
    coronaryHeredity: boolean;
    coronaryHeredityDetails: string;
  };
  previousHistory: string;
  currentTreatment: string;
  interrogation: string;
  clinicalExamination: string;
  ecg: string;
  lastBiologyResults: string;
  conclusion: string;
  treatmentPlan: string;
  nextAppointment: string;
}
