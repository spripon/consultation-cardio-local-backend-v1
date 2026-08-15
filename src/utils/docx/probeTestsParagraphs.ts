
import { Paragraph, TextRun } from 'docx';
import { FormData } from '@/components/pacemaker/types';

export const createProbeTestsParagraphs = (formData: FormData, t: any) => {
  const paragraphs: Paragraph[] = [];

  if (formData.deviceType.chambers === "double-chambre" || formData.deviceType.chambers === "triple-chambre") {
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({ text: `${t.probeTests} atriale :`, bold: true })
        ],
        spacing: { after: 200 }
      }),
      new Paragraph({
        children: [
          new TextRun({ text: `- ${t.impedance} = `, bold: true }),
          new TextRun({ text: `${formData.atrialProbeImpedance} ohms` })
        ],
        spacing: { after: 200 }
      }),
      new Paragraph({
        children: [
          new TextRun({ text: `- ${t.detection} = `, bold: true }),
          new TextRun({ text: `${formData.atrialProbeDetection} mV` })
        ],
        spacing: { after: 200 }
      }),
      new Paragraph({
        children: [
          new TextRun({ text: `- ${t.threshold} = `, bold: true }),
          new TextRun({ text: `${formData.atrialProbeThreshold} V` })
        ],
        spacing: { after: 800 }
      })
    );
  }

  paragraphs.push(
    new Paragraph({
      children: [
        new TextRun({ 
          text: `${t.probeTests} ${formData.deviceType.chambers === "triple-chambre" ? "VD" : "ventriculaire"} :`,
          bold: true 
        })
      ],
      spacing: { after: 200 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `- ${t.impedance} = `, bold: true }),
        new TextRun({ text: `${formData.ventricularProbeImpedance} ohms` })
      ],
      spacing: { after: 200 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `- ${t.detection} = `, bold: true }),
        new TextRun({ text: `${formData.ventricularProbeDetection} mV` })
      ],
      spacing: { after: 200 }
    }),
    new Paragraph({
      children: [
        new TextRun({ text: `- ${t.threshold} = `, bold: true }),
        new TextRun({ text: `${formData.ventricularProbeThreshold} V` })
      ],
      spacing: { after: 800 }
    })
  );

  if (formData.deviceType.chambers === "triple-chambre") {
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({ text: `${t.probeTests} VG :`, bold: true })
        ],
        spacing: { after: 200 }
      }),
      new Paragraph({
        children: [
          new TextRun({ text: `- ${t.impedance} = `, bold: true }),
          new TextRun({ text: `${formData.leftVentricularProbeImpedance} ohms` })
        ],
        spacing: { after: 200 }
      }),
      new Paragraph({
        children: [
          new TextRun({ text: `- ${t.detection} = `, bold: true }),
          new TextRun({ text: `${formData.leftVentricularProbeDetection} mV` })
        ],
        spacing: { after: 200 }
      }),
      new Paragraph({
        children: [
          new TextRun({ text: `- ${t.threshold} = `, bold: true }),
          new TextRun({ text: `${formData.leftVentricularProbeThreshold} V` })
        ],
        spacing: { after: 800 }
      })
    );
  }

  return paragraphs;
};
