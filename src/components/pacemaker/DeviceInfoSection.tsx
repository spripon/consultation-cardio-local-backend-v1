
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { FormData } from "./types";
import { useLanguage } from "@/contexts/LanguageContext";
import { translations } from "@/translations";

interface DeviceInfoProps {
  deviceType: FormData['deviceType'];
  implantDate: string;
  indication: string;
  symptoms: string;
  localState: string;
  batteryStatus: string;
  remainingLongevity: string;
  onDeviceTypeChange: (field: keyof FormData['deviceType'], value: string) => void;
  onBatteryStatusChange: (value: string) => void;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const DeviceInfoSection = ({
  deviceType,
  implantDate,
  indication,
  symptoms,
  localState,
  batteryStatus,
  remainingLongevity,
  onDeviceTypeChange,
  onBatteryStatusChange,
  onChange,
}: DeviceInfoProps) => {
  const { language } = useLanguage();
  const t = translations[language];

  return (
    <div className="space-y-8">      
      <div className="space-y-4">
        <Label className="text-lg font-bold">{t.deviceType}</Label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Première colonne */}
          <div>
            <RadioGroup
              value={deviceType.category}
              onValueChange={(value) => onDeviceTypeChange('category', value)}
              className="flex flex-col space-y-2"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="PM" id="PM" />
                <Label htmlFor="PM">PM</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="DAI" id="DAI" />
                <Label htmlFor="DAI">DAI</Label>
              </div>
            </RadioGroup>
          </div>

          {/* Deuxième colonne */}
          <div>
            <RadioGroup
              value={deviceType.chambers}
              onValueChange={(value) => onDeviceTypeChange('chambers', value)}
              className="flex flex-col space-y-2"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="mono-chambre" id="mono" />
                <Label htmlFor="mono">{language === 'fr' ? 'Mono-chambre' : 'Single-chamber'}</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="double-chambre" id="double" />
                <Label htmlFor="double">{language === 'fr' ? 'Double-chambre' : 'Dual-chamber'}</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="triple-chambre" id="triple" />
                <Label htmlFor="triple">{language === 'fr' ? 'Triple-chambre' : 'Triple-chamber'}</Label>
              </div>
            </RadioGroup>
          </div>

          {/* Troisième colonne */}
          <div>
            <RadioGroup
              value={deviceType.brand}
              onValueChange={(value) => onDeviceTypeChange('brand', value)}
              className="flex flex-col space-y-2"
            >
              {[
                ['MEDTRONIC', 'Medtronic'],
                ['ABBOTT (St-Jude)', 'Abbott'],
                ['BOSTON', 'Boston'],
                ['BIOTRONIK', 'Biotronik'],
                ['MICROPORT (Sorin)', 'MicroPort']
              ].map(([label, value]) => (
                <div key={value} className="flex items-center space-x-2">
                  <RadioGroupItem value={value} id={value} />
                  <Label htmlFor={value}>{label}</Label>
                </div>
              ))}
            </RadioGroup>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-3">
          <Label htmlFor="implantDate" className="text-lg font-bold">{`${t.implantDate} (${language === 'fr' ? 'JJ/MM/AAAA' : 'DD/MM/YYYY'})`}</Label>
          <Input
            id="implantDate"
            name="implantDate"
            type="text"
            placeholder={language === 'fr' ? 'JJ/MM/AAAA' : 'DD/MM/YYYY'}
            pattern="\d{2}/\d{2}/\d{4}"
            value={implantDate}
            onChange={onChange}
          />
        </div>
        <div className="space-y-3">
          <Label htmlFor="indication" className="text-lg font-bold">{t.implantIndication}</Label>
          <Input
            id="indication"
            name="indication"
            value={indication}
            onChange={onChange}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-3">
          <Label htmlFor="symptoms" className="text-lg font-bold">{t.symptoms}</Label>
          <Input
            id="symptoms"
            name="symptoms"
            value={symptoms}
            onChange={onChange}
          />
        </div>
        <div className="space-y-3">
          <Label htmlFor="localState" className="text-lg font-bold">{t.localState}</Label>
          <Input
            id="localState"
            name="localState"
            value={localState}
            onChange={onChange}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-3">
          <Label className="text-lg font-bold">{t.batteryStatus}</Label>
          <RadioGroup
            value={batteryStatus}
            onValueChange={onBatteryStatusChange}
            className="flex flex-col space-y-1"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="debut-de-vie" id="debut-vie" />
              <Label htmlFor="debut-vie">{t.batteryLifeStart}</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="milieu-de-vie" id="milieu-vie" />
              <Label htmlFor="milieu-vie">{t.batteryLifeMid}</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="fin-de-vie" id="fin-vie" />
              <Label htmlFor="fin-vie">{t.batteryLifeEnd}</Label>
            </div>
          </RadioGroup>
        </div>
        <div className="space-y-3">
          <Label htmlFor="remainingLongevity" className="text-lg font-bold">{t.remainingLongevity}</Label>
          <Input
            id="remainingLongevity"
            name="remainingLongevity"
            value={remainingLongevity}
            onChange={onChange}
          />
        </div>
      </div>
    </div>
  );
};

export default DeviceInfoSection;
