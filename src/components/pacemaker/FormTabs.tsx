
import PatientInfoSection from "./PatientInfoSection";
import DeviceInfoSection from "./DeviceInfoSection";
import StimulationSection from "./StimulationSection";
import ProbeTestsSection from "./ProbeTestsSection";
import ConclusionSection from "./ConclusionSection";
import { FormData } from "./types";

interface FormTabsProps {
  formData: FormData;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDeviceTypeChange: (field: keyof FormData['deviceType'], value: string) => void;
  onBatteryStatusChange: (value: string) => void;
}

const FormTabs = ({ formData, onChange, onDeviceTypeChange, onBatteryStatusChange }: FormTabsProps) => {
  return (
    <div className="space-y-8">
      <PatientInfoSection
        date={formData.date}
        patientName={formData.patientName}
        birthDate={formData.birthDate}
        onChange={onChange}
      />

      <DeviceInfoSection
        deviceType={formData.deviceType}
        implantDate={formData.implantDate}
        indication={formData.indication}
        symptoms={formData.symptoms}
        localState={formData.localState}
        batteryStatus={formData.batteryStatus}
        remainingLongevity={formData.remainingLongevity}
        onDeviceTypeChange={onDeviceTypeChange}
        onBatteryStatusChange={onBatteryStatusChange}
        onChange={onChange}
      />

      <StimulationSection
        parameters={formData.parameters}
        stimulationPercentageAtrial={formData.stimulationPercentageAtrial}
        stimulationPercentageVentricular={formData.stimulationPercentageVentricular}
        onChange={onChange}
      />

      <ProbeTestsSection
        deviceType={formData.deviceType}
        atrialProbeImpedance={formData.atrialProbeImpedance}
        atrialProbeDetection={formData.atrialProbeDetection}
        atrialProbeThreshold={formData.atrialProbeThreshold}
        ventricularProbeImpedance={formData.ventricularProbeImpedance}
        ventricularProbeDetection={formData.ventricularProbeDetection}
        ventricularProbeThreshold={formData.ventricularProbeThreshold}
        leftVentricularProbeImpedance={formData.leftVentricularProbeImpedance}
        leftVentricularProbeDetection={formData.leftVentricularProbeDetection}
        leftVentricularProbeThreshold={formData.leftVentricularProbeThreshold}
        onChange={onChange}
      />

      <ConclusionSection
        memoryEvents={formData.memoryEvents}
        programModification={formData.programModification}
        nextSteps={formData.nextSteps}
        nextAppointment={formData.nextAppointment}
        summary={formData.summary}
        onChange={onChange}
      />
    </div>
  );
};

export default FormTabs;
