
import { Paragraph, TextRun } from 'docx';
import { FormData } from '@/components/pacemaker/types';
import { formatDate } from '../formatters/dateFormatter';

export const createPatientInfoParagraphs = (formData: FormData, t: any) => {
  return [
    new Paragraph({
      children: [
        new TextRun({
          text: `${t.reportTitle.toUpperCase()}`,
          bold: true,
          size: 36
        })
      ],
      spacing: { after: 800 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `${t.dateControl} : `, bold: true }),
        new TextRun({ text: formatDate(formData.date) })
      ],
      spacing: { after: 800 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `${t.patient} : `, bold: true }),
        new TextRun({ text: formData.patientName })
      ],
      spacing: { after: 400 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `${t.birthDate} : `, bold: true }),
        new TextRun({ text: formData.birthDate })
      ],
      spacing: { after: 800 }
    })
  ];
};
