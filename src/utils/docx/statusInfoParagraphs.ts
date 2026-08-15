
import { Paragraph, TextRun } from 'docx';
import { FormData } from '@/components/pacemaker/types';

export const createStatusInfoParagraphs = (formData: FormData, t: any) => {
  return [
    new Paragraph({
      children: [
        new TextRun({ text: `${t.symptoms} : `, bold: true }),
        new TextRun({ text: formData.symptoms })
      ],
      spacing: { after: 400 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `${t.localState} : `, bold: true }),
        new TextRun({ text: formData.localState })
      ],
      spacing: { after: 800 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `${t.batteryStatus} : `, bold: true }),
        new TextRun({ text: formData.batteryStatus })
      ],
      spacing: { after: 400 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `${t.remainingLongevity} : `, bold: true }),
        new TextRun({ text: formData.remainingLongevity })
      ],
      spacing: { after: 800 }
    })
  ];
};
