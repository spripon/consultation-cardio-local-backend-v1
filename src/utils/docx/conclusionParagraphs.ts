
import { Paragraph, TextRun } from 'docx';
import { FormData } from '@/components/pacemaker/types';

export const createConclusionParagraphs = (formData: FormData, t: any) => {
  return [
    new Paragraph({
      children: [
        new TextRun({ text: `${t.memoryEvents} : `, bold: true }),
        new TextRun({ text: formData.memoryEvents })
      ],
      spacing: { after: 800 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `${t.programModification} : `, bold: true }),
        new TextRun({ text: formData.programModification })
      ],
      spacing: { after: 800 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `${t.nextSteps} : `, bold: true }),
        new TextRun({ text: formData.nextSteps })
      ],
      spacing: { after: 800 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `${t.nextAppointment} : `, bold: true }),
        new TextRun({ text: formData.nextAppointment })
      ],
      spacing: { after: 800 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `${t.summary} : `, bold: true }),
        new TextRun({ text: formData.summary })
      ],
      spacing: { before: 800 }
    })
  ];
};
