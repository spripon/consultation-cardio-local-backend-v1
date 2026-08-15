
import { Document, Packer } from 'docx';
import { saveAs } from 'file-saver';
import { CardiologyFormData } from '@/components/cardiology/types';
import { createCardiologyParagraphs } from './docx/cardiologyParagraphs';

export const generateCardiologyWordDocument = async (formData: CardiologyFormData) => {
  const doc = new Document({
    sections: [{
      properties: {},
      children: createCardiologyParagraphs(formData)
    }]
  });

  const blob = await Packer.toBlob(doc);
  saveAs(blob, `Compte_rendu_Cardiologie_${formData.patientName}_${formData.date}.docx`);
};
