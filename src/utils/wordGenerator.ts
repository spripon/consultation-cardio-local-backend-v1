
import { Document, Packer } from 'docx';
import { saveAs } from 'file-saver';
import { FormData } from '@/components/pacemaker/types';
import { translations } from '@/translations';
import { createPatientInfoParagraphs } from './docx/patientInfoParagraphs';
import { createDeviceInfoParagraphs } from './docx/deviceInfoParagraphs';
import { createStatusInfoParagraphs } from './docx/statusInfoParagraphs';
import { createStimulationParagraphs } from './docx/stimulationParagraphs';
import { createProbeTestsParagraphs } from './docx/probeTestsParagraphs';
import { createConclusionParagraphs } from './docx/conclusionParagraphs';

export const generateWordDocument = async (formData: FormData, language: 'fr' | 'en' = 'fr') => {
  const t = translations[language];
  
  const doc = new Document({
    sections: [{
      properties: {},
      children: [
        ...createPatientInfoParagraphs(formData, t),
        ...createDeviceInfoParagraphs(formData, t),
        ...createStatusInfoParagraphs(formData, t),
        ...createStimulationParagraphs(formData, t),
        ...createProbeTestsParagraphs(formData, t),
        ...createConclusionParagraphs(formData, t)
      ]
    }]
  });

  const blob = await Packer.toBlob(doc);
  saveAs(blob, `${language === 'fr' ? 'Compte_rendu' : 'Report'}_${formData.patientName}_${formData.date}.docx`);
};
