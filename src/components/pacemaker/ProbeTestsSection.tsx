
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLanguage } from "@/contexts/LanguageContext";
import { translations } from "@/translations";

interface ProbeTestsProps {
  deviceType: {
    chambers: string;
  };
  atrialProbeImpedance: string;
  atrialProbeDetection: string;
  atrialProbeThreshold: string;
  ventricularProbeImpedance: string;
  ventricularProbeDetection: string;
  ventricularProbeThreshold: string;
  leftVentricularProbeImpedance?: string;
  leftVentricularProbeDetection?: string;
  leftVentricularProbeThreshold?: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const ProbeTestsSection = ({
  deviceType,
  atrialProbeImpedance,
  atrialProbeDetection,
  atrialProbeThreshold,
  ventricularProbeImpedance,
  ventricularProbeDetection,
  ventricularProbeThreshold,
  leftVentricularProbeImpedance = "",
  leftVentricularProbeDetection = "",
  leftVentricularProbeThreshold = "",
  onChange,
}: ProbeTestsProps) => {
  const { language } = useLanguage();
  const t = translations[language];
  
  const showAtrialSection = deviceType.chambers === "double-chambre" || deviceType.chambers === "triple-chambre";
  const showLeftVentricularSection = deviceType.chambers === "triple-chambre";

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {showAtrialSection && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-medical-600">
              {`${t.probeTests} - ${language === 'fr' ? 'sonde atriale' : 'Atrial Lead'}`}
            </h2>
            <div className="space-y-2">
              <Label htmlFor="atrialProbeImpedance">{t.impedance}</Label>
              <Input
                id="atrialProbeImpedance"
                name="atrialProbeImpedance"
                value={atrialProbeImpedance}
                onChange={onChange}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="atrialProbeDetection">{t.detection}</Label>
              <Input
                id="atrialProbeDetection"
                name="atrialProbeDetection"
                value={atrialProbeDetection}
                onChange={onChange}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="atrialProbeThreshold">{t.threshold}</Label>
              <Input
                id="atrialProbeThreshold"
                name="atrialProbeThreshold"
                value={atrialProbeThreshold}
                onChange={onChange}
                className="w-full"
              />
            </div>
          </div>
        )}

        <div className="space-y-4">
          <h2 className="text-xl font-bold text-medical-600">
            {`${t.probeTests} - ${language === 'fr' 
              ? (showLeftVentricularSection ? 'sonde VD' : 'sonde ventriculaire')
              : (showLeftVentricularSection ? 'RV Lead' : 'Ventricular Lead')}`}
          </h2>
          <div className="space-y-2">
            <Label htmlFor="ventricularProbeImpedance">{t.impedance}</Label>
            <Input
              id="ventricularProbeImpedance"
              name="ventricularProbeImpedance"
              value={ventricularProbeImpedance}
              onChange={onChange}
              className="w-full"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="ventricularProbeDetection">{t.detection}</Label>
            <Input
              id="ventricularProbeDetection"
              name="ventricularProbeDetection"
              value={ventricularProbeDetection}
              onChange={onChange}
              className="w-full"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="ventricularProbeThreshold">{t.threshold}</Label>
            <Input
              id="ventricularProbeThreshold"
              name="ventricularProbeThreshold"
              value={ventricularProbeThreshold}
              onChange={onChange}
              className="w-full"
            />
          </div>
        </div>

        {showLeftVentricularSection && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-medical-600">
              {`${t.probeTests} - ${language === 'fr' ? 'sonde VG' : 'LV Lead'}`}
            </h2>
            <div className="space-y-2">
              <Label htmlFor="leftVentricularProbeImpedance">{t.impedance}</Label>
              <Input
                id="leftVentricularProbeImpedance"
                name="leftVentricularProbeImpedance"
                value={leftVentricularProbeImpedance}
                onChange={onChange}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="leftVentricularProbeDetection">{t.detection}</Label>
              <Input
                id="leftVentricularProbeDetection"
                name="leftVentricularProbeDetection"
                value={leftVentricularProbeDetection}
                onChange={onChange}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="leftVentricularProbeThreshold">{t.threshold}</Label>
              <Input
                id="leftVentricularProbeThreshold"
                name="leftVentricularProbeThreshold"
                value={leftVentricularProbeThreshold}
                onChange={onChange}
                className="w-full"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProbeTestsSection;
