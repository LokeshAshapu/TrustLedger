import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppShell } from "./layouts/AppShell";
import { CommandCenterPage } from "./pages/CommandCenterPage";
import { RefundRiskPage } from "./pages/RefundRiskPage";
import { DecisionsPage } from "./pages/DecisionsPage";
import { DecisionInvestigationPage } from "./pages/DecisionInvestigationPage";
import { EvidencePage } from "./pages/EvidencePage";
import { RiskPage } from "./pages/RiskPage";
import { AuditPage } from "./pages/AuditPage";
import { SimulatorPage } from "./pages/SimulatorPage";
import { TestPaymentPage } from "./pages/TestPaymentPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<Navigate to="/command-center" replace />} />
          <Route path="/test-payment" element={<TestPaymentPage />} />
          <Route path="/command-center" element={<CommandCenterPage />} />
          <Route path="/refund-risk" element={<RefundRiskPage />} />
          <Route path="/decisions" element={<DecisionsPage />} />
          <Route path="/decisions/:decisionId" element={<DecisionInvestigationPage />} />
          <Route path="/evidence" element={<EvidencePage />} />
          <Route path="/risk" element={<RiskPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/simulator" element={<SimulatorPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
};

export default App;
