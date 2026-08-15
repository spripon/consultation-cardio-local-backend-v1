
import { useState } from "react";
import { FormData } from "@/components/pacemaker/types";

export const usePacemakerForm = () => {
  const getCurrentDate = () => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  };

  const [formData, setFormData] = useState<FormData>({
    date: getCurrentDate(),
    patientName: "",
    birthDate: "",
    deviceType: {
      category: "",
      chambers: "",
      brand: "",
    },
    implantDate: "",
    indication: "",
    symptoms: "",
    localState: "",
    batteryStatus: "",
    remainingLongevity: "",
    parameters: "",
    stimulationPercentageAtrial: "",
    stimulationPercentageVentricular: "",
    atrialProbeImpedance: "",
    atrialProbeDetection: "",
    atrialProbeThreshold: "",
    ventricularProbeImpedance: "",
    ventricularProbeDetection: "",
    ventricularProbeThreshold: "",
    leftVentricularProbeImpedance: "",
    leftVentricularProbeDetection: "",
    leftVentricularProbeThreshold: "",
    memoryEvents: "",
    programModification: "",
    nextSteps: "",
    nextAppointment: "",
    summary: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleDeviceTypeChange = (field: keyof typeof formData.deviceType, value: string) => {
    setFormData((prev) => ({
      ...prev,
      deviceType: {
        ...prev.deviceType,
        [field]: value,
      },
    }));
  };

  const handleBatteryStatusChange = (value: string) => {
    setFormData((prev) => ({ ...prev, batteryStatus: value }));
  };

  const handleReset = () => {
    setFormData({
      date: getCurrentDate(),
      patientName: "",
      birthDate: "",
      deviceType: {
        category: "",
        chambers: "",
        brand: "",
      },
      implantDate: "",
      indication: "",
      symptoms: "",
      localState: "",
      batteryStatus: "",
      remainingLongevity: "",
      parameters: "",
      stimulationPercentageAtrial: "",
      stimulationPercentageVentricular: "",
      atrialProbeImpedance: "",
      atrialProbeDetection: "",
      atrialProbeThreshold: "",
      ventricularProbeImpedance: "",
      ventricularProbeDetection: "",
      ventricularProbeThreshold: "",
      leftVentricularProbeImpedance: "",
      leftVentricularProbeDetection: "",
      leftVentricularProbeThreshold: "",
      memoryEvents: "",
      programModification: "",
      nextSteps: "",
      nextAppointment: "",
      summary: "",
    });
  };

  return {
    formData,
    handleChange,
    handleDeviceTypeChange,
    handleBatteryStatusChange,
    handleReset,
  };
};
