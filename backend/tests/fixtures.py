"""Jeux de données SYNTHÉTIQUES uniquement — aucune donnée patient réelle."""

SYNTHETIC_REPORT = """CENTRE DE CARDIOLOGIE - COMPTE RENDU DE CONSULTATION
Patient : DUPONT Marie
Prénom : Marie
Date de naissance : 03/03/1972
IPP : 1234567
NIR : 2 72 03 65 123 456 78
Téléphone : 06 12 34 56 78
Email : marie.dupont@example.invalid
Adresse : 12 rue des Lilas, 65000 TARBES
Médecin traitant : Dr MARTIN

Antécédents :
Fibrillation auriculaire paroxystique depuis 2019.
HTA traitée, diabète de type 2.
Angioplastie avec stent actif sur l'IVA en 2020.

Traitement actuel :
Apixaban 5 mg x2 par jour.
Bisoprolol 5 mg/j, atorvastatine 40 mg/j.

Interrogatoire :
Patiente de 74 ans, dyspnée NYHA II à l'effort, pas de douleur thoracique.

Examen clinique :
TA 132/78 mmHg, FC 68 bpm, SpO2 97%. Auscultation cardiaque sans souffle.
Pas d'oedèmes des membres inférieurs.

ECG :
Rythme sinusal régulier, QRS fins, PR 180 ms, QTc 420 ms, pas de sus-décalage ST.

Biologie :
Hb 13,2 g/dL, créatinine 82 µmol/L, eGFR 71 mL/min, K+ 4,1 mmol/L, LDL 0,88 g/L, NT-proBNP 210 pg/mL.

Conclusion :
Au total, patiente de 74 ans stable, FEVG 55%, fibrillation auriculaire bien anticoagulée.

Conduite à tenir :
Poursuite du traitement actuel. Contrôle dans 6 mois avec échocardiographie de contrôle.
DUPONT Marie - IPP 1234567 - page 1/1
"""

PII_STRINGS = [
    "DUPONT",
    "Marie",
    "03/03/1972",
    "1234567",
    "2 72 03 65 123 456 78",
    "06 12 34 56 78",
    "marie.dupont@example.invalid",
    "12 rue des Lilas",
    "MARTIN",
]

CLINICAL_STRINGS = [
    "74 ans",
    "FEVG 55%",
    "Fibrillation auriculaire",
    "Apixaban 5 mg x2",
    "créatinine",
    "Rythme sinusal",
]