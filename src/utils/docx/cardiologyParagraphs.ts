
import { Paragraph, TextRun, AlignmentType } from 'docx';
import { CardiologyFormData } from '@/components/cardiology/types';
import { formatDate } from '@/utils/formatters/dateFormatter';

export const createCardiologyParagraphs = (formData: CardiologyFormData) => {
  const paragraphs: Paragraph[] = [];

  // Title
  paragraphs.push(
    new Paragraph({
      children: [
        new TextRun({
          text: "COMPTE-RENDU DE CONSULTATION DE CARDIOLOGIE",
          bold: true,
          size: 28,
        }),
      ],
      alignment: AlignmentType.CENTER,
      spacing: { after: 400 },
    })
  );

  // Date and patient info with formatted date
  const formattedDate = formatDate(formData.date);
  const formattedBirthDate = formatDate(formData.birthDate);
  
  paragraphs.push(
    new Paragraph({
      children: [
        new TextRun({
          text: `Je vois ce jour, le ${formattedDate}, en consultation de Cardiologie, ${formData.gender} ${formData.patientName} né(e) le ${formattedBirthDate}`,
          size: 24,
        }),
      ],
      spacing: { after: 300 },
    })
  );

  // Motif de consultation
  if (formData.consultationReason) {
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: "Motif de consultation",
            bold: true,
            size: 24,
          }),
        ],
        spacing: { after: 200 },
      })
    );
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: formData.consultationReason,
            size: 22,
          }),
        ],
        spacing: { after: 300 },
      })
    );
  }

  // Facteurs de risque cardiovasculaire
  paragraphs.push(
    new Paragraph({
      children: [
        new TextRun({
          text: "Facteurs de risque cardiovasculaire",
          bold: true,
          size: 24,
        }),
      ],
      spacing: { after: 200 },
    })
  );

  const riskFactors = [];
  if (formData.cardiovascularRiskFactors.hypercholesterolemia) riskFactors.push("Hypercholestérolémie");
  if (formData.cardiovascularRiskFactors.hypertension) riskFactors.push("HTA");
  if (formData.cardiovascularRiskFactors.diabetesType2) riskFactors.push("Diabète type II");
  if (formData.cardiovascularRiskFactors.overweight) {
    riskFactors.push(`Surpoids${formData.cardiovascularRiskFactors.overweightDetails ? `: ${formData.cardiovascularRiskFactors.overweightDetails}` : ''}`);
  }
  if (formData.cardiovascularRiskFactors.smoking) {
    riskFactors.push(`Tabac${formData.cardiovascularRiskFactors.smokingDetails ? `: ${formData.cardiovascularRiskFactors.smokingDetails}` : ''}`);
  }
  if (formData.cardiovascularRiskFactors.coronaryHeredity) {
    riskFactors.push(`Hérédité coronarienne${formData.cardiovascularRiskFactors.coronaryHeredityDetails ? `: ${formData.cardiovascularRiskFactors.coronaryHeredityDetails}` : ''}`);
  }

  if (riskFactors.length > 0) {
    riskFactors.forEach(factor => {
      paragraphs.push(
        new Paragraph({
          children: [
            new TextRun({
              text: `• ${factor}`,
              size: 22,
            }),
          ],
          spacing: { after: 100 },
        })
      );
    });
  } else {
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: "Aucun facteur de risque cardiovasculaire identifié",
            size: 22,
          }),
        ],
        spacing: { after: 200 },
      })
    );
  }

  paragraphs.push(new Paragraph({ spacing: { after: 200 } }));

  // Antécédents et comorbidités
  if (formData.previousHistory) {
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: "Antécédents et comorbidités principales",
            bold: true,
            size: 24,
          }),
        ],
        spacing: { after: 200 },
      })
    );
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: formData.previousHistory,
            size: 22,
          }),
        ],
        spacing: { after: 300 },
      })
    );
  }

  // Traitement habituel
  if (formData.currentTreatment) {
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: "Traitement habituel",
            bold: true,
            size: 24,
          }),
        ],
        spacing: { after: 200 },
      })
    );
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: formData.currentTreatment,
            size: 22,
          }),
        ],
        spacing: { after: 300 },
      })
    );
  }

  // À l'interrogatoire
  if (formData.interrogation) {
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: "À l'interrogatoire",
            bold: true,
            size: 24,
          }),
        ],
        spacing: { after: 200 },
      })
    );
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: formData.interrogation,
            size: 22,
          }),
        ],
        spacing: { after: 300 },
      })
    );
  }

  // À l'examen clinique
  if (formData.clinicalExamination) {
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: "À l'examen clinique",
            bold: true,
            size: 24,
          }),
        ],
        spacing: { after: 200 },
      })
    );
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: formData.clinicalExamination,
            size: 22,
          }),
        ],
        spacing: { after: 300 },
      })
    );
  }

  // L'ECG
  if (formData.ecg) {
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: "L'ECG",
            bold: true,
            size: 24,
          }),
        ],
        spacing: { after: 200 },
      })
    );
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: formData.ecg,
            size: 22,
          }),
        ],
        spacing: { after: 300 },
      })
    );
  }

  // Le dernier bilan biologique
  if (formData.lastBiologyResults) {
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: "Le dernier bilan biologique",
            bold: true,
            size: 24,
          }),
        ],
        spacing: { after: 200 },
      })
    );
    
    // Split the biology results by lines and create separate paragraphs for better formatting
    const biologyLines = formData.lastBiologyResults.split('\n');
    biologyLines.forEach((line, index) => {
      if (line.trim()) {
        paragraphs.push(
          new Paragraph({
            children: [
              new TextRun({
                text: line,
                size: 22,
              }),
            ],
            spacing: { after: index === biologyLines.length - 1 ? 300 : 100 },
          })
        );
      }
    });
  }

  // AU TOTAL - bold, uppercase and underlined
  if (formData.conclusion) {
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: "AU TOTAL",
            bold: true,
            underline: {},
            size: 24,
          }),
        ],
        spacing: { after: 200 },
      })
    );
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: formData.conclusion,
            bold: true,
            size: 22,
          }),
        ],
        spacing: { after: 300 },
      })
    );
  }

  // Conduite à tenir
  if (formData.treatmentPlan) {
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: "Conduite à tenir",
            bold: true,
            size: 24,
          }),
        ],
        spacing: { after: 200 },
      })
    );
    paragraphs.push(
      new Paragraph({
        children: [
          new TextRun({
            text: formData.treatmentPlan,
            size: 22,
          }),
        ],
        spacing: { after: 300 },
      })
    );
  }

  // Phrase finale
  paragraphs.push(
    new Paragraph({
      children: [
        new TextRun({
          text: `Sauf évènement imprévu, je pourrai revoir ${formData.gender} ${formData.patientName} pour son suivi cardiologique : ${formData.nextAppointment ? `dans ${formData.nextAppointment}` : 'dans ...'} ou bien évidemment plus tôt en cas de problème.`,
          size: 22,
        }),
      ],
      spacing: { after: 200 },
    })
  );

  paragraphs.push(
    new Paragraph({
      children: [
        new TextRun({
          text: "En vous remerciant de votre confiance et en restant à votre disposition,",
          size: 22,
        }),
      ],
      spacing: { after: 100 },
    })
  );

  paragraphs.push(
    new Paragraph({
      children: [
        new TextRun({
          text: "Bien confraternellement",
          size: 22,
        }),
      ],
      spacing: { after: 200 },
    })
  );

  return paragraphs;
};
