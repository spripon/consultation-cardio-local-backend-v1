
import { Paragraph, TextRun } from 'docx';
import { FormData } from '@/components/pacemaker/types';

export const createDeviceInfoParagraphs = (formData: FormData, t: any) => {
  return [
    new Paragraph({
      children: [
        new TextRun({ text: `${t.deviceType} : `, bold: true }),
        new TextRun({ text: `${formData.deviceType.category} - ${formData.deviceType.chambers} - ${formData.deviceType.brand}` })
      ],
      spacing: { after: 400 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `${t.implantDate} : `, bold: true }),
        new TextRun({ text: formData.implantDate })
      ],
      spacing: { after: 400 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `${t.implantIndication} : `, bold: true }),
        new TextRun({ text: formData.indication })
      ],
      spacing: { after: 800 }
    })
  ];
};
