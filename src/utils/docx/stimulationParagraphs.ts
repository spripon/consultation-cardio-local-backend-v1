
import { Paragraph, TextRun } from 'docx';
import { FormData } from '@/components/pacemaker/types';

export const createStimulationParagraphs = (formData: FormData, t: any) => {
  return [
    new Paragraph({
      children: [
        new TextRun({ text: `${t.parameters} : `, bold: true }),
        new TextRun({ text: formData.parameters })
      ],
      spacing: { after: 800 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `${t.stimulationPercentage} :`, bold: true })
      ],
      spacing: { after: 200 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `- ${t.atrialStimulation} : `, bold: true }),
        new TextRun({ text: formData.stimulationPercentageAtrial })
      ],
      spacing: { after: 200 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `- ${t.ventricularStimulation} : `, bold: true }),
        new TextRun({ text: formData.stimulationPercentageVentricular })
      ],
      spacing: { after: 800 }
    })
  ];
};
