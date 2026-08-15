
export interface FormData {
  date: string;
  patientName: string;
  birthDate: string;
  deviceType: {
    category: string;
    chambers: string;
    brand: string;
  };
  implantDate: string;
  indication: string;
  symptoms: string;
  localState: string;
  batteryStatus: string;
  remainingLongevity: string;
  parameters: string;
  stimulationPercentageAtrial: string;
  stimulationPercentageVentricular: string;
  atrialProbeImpedance: string;
  atrialProbeDetection: string;
  atrialProbeThreshold: string;
  ventricularProbeImpedance: string;
  ventricularProbeDetection: string;
  ventricularProbeThreshold: string;
  leftVentricularProbeImpedance: string;
  leftVentricularProbeDetection: string;
  leftVentricularProbeThreshold: string;
  memoryEvents: string;
  programModification: string;
  nextSteps: string;
  nextAppointment: string;
  summary: string;
}
