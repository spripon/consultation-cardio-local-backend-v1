
interface GeneratedReportProps {
  report: string;
}

const GeneratedReport = ({ report }: GeneratedReportProps) => {
  if (!report) return null;

  return (
    <div className="mt-8 p-6 bg-gray-50 rounded-lg border border-gray-200">
      <h3 className="text-lg font-medium text-medical-600 mb-4">Compte-rendu généré</h3>
      <pre className="whitespace-pre-wrap font-mono text-sm text-medical-700">{report}</pre>
    </div>
  );
};

export default GeneratedReport;
