
import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import PacemakerForm from "@/components/PacemakerForm";
import CardiologyForm from "@/components/cardiology/CardiologyForm";

const Index = () => {
  const [activeForm, setActiveForm] = useState<'pacemaker' | 'cardiology'>('cardiology');

  return (
    <div className="min-h-screen bg-gradient-to-br from-medical-50 to-blue-50 p-4">
      <div className="container mx-auto py-8">
        <div className="flex justify-center mb-8">
          <Card className="p-6 shadow-lg border-medical-200">
            <h1 className="text-3xl font-bold text-medical-800 text-center mb-6">
              Générateur de comptes-rendus médicaux
            </h1>
            <div className="flex flex-col items-center space-y-4">
              <Button 
                onClick={() => setActiveForm('pacemaker')}
                className={activeForm === 'pacemaker' ? "bg-medical-600 hover:bg-medical-700" : "bg-gray-400 hover:bg-gray-500"}
              >
                Contrôle de dispositif implantable
              </Button>
              <Button 
                onClick={() => setActiveForm('cardiology')}
                className={activeForm === 'cardiology' ? "bg-medical-600 hover:bg-medical-700" : "bg-gray-400 hover:bg-gray-500"}
              >
                Consultation de Cardiologie
              </Button>
            </div>
          </Card>
        </div>
        
        {activeForm === 'pacemaker' && <PacemakerForm />}
        {activeForm === 'cardiology' && <CardiologyForm />}
      </div>
    </div>
  );
};

export default Index;
