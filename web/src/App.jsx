import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";

import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import ProfileRequired from "./components/ProfileRequired";
import InterviewSetup from "./pages/InterviewSetup";
import InterviewArena from "./pages/InterviewArena";
import InterviewHistory from "./pages/InterviewHistory";
import InterviewReport from "./pages/InterviewReport";
// Lazy-loaded pages
const Landing = lazy(() => import("./pages/Landing"));
const Onboarding = lazy(() => import("./pages/Onboarding"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Analyze = lazy(() => import("./pages/Analyze"));
const History = lazy(() => import("./pages/History"));
const Analysis = lazy(() => import("./pages/Analysis"));

function Protected({ children }) {
  return <ProtectedRoute>{children}</ProtectedRoute>;
}

function PageLoader() {
  return (
    <div className="route-loader">
      <span className="loading-spinner" />
      <span>Loading SmartHire...</span>
    </div>
  );
}

function NotFound() {
  return (
    <div className="not-found">
      <span>404</span>
      <h1>Page not found</h1>
      <p>The page you're looking for doesn't exist.</p>

      <a href="/dashboard" className="button primary">
        Go to Dashboard
      </a>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public */}
        <Route path="/" element={<Landing />} />

        {/* Onboarding */}
        <Route
          path="/onboarding"
          element={
            <Protected>
              <Onboarding />
            </Protected>
          }
        />

        {/* Dashboard */}
        <Route
          path="/dashboard"
          element={
            <Protected>
              <ProfileRequired>
                <Navbar />
                <Dashboard />
              </ProfileRequired>
            </Protected>
          }
        />

        {/* Analyze */}
        <Route
          path="/analyze"
          element={
            <Protected>
              <ProfileRequired>
                <Navbar />
                <Analyze />
              </ProfileRequired>
            </Protected>
          }
        />

        {/* History */}
        <Route
          path="/history"
          element={
            <Protected>
              <ProfileRequired>
                <Navbar />
                <History />
              </ProfileRequired>
            </Protected>
          }
        />

        {/* Analysis Details */}
        <Route
          path="/analysis/:id"
          element={
            <Protected>
              <ProfileRequired>
                <Navbar />
                <Analysis />
              </ProfileRequired>
            </Protected>
          }
        />

        <Route
          path="/interview/setup"
          element={
            <Protected>
              <ProfileRequired>
                <Navbar />
                <InterviewSetup />
              </ProfileRequired>
            </Protected>
          }
        />
        <Route
          path="/interview/:sessionId"
          element={
            <Protected>
              <ProfileRequired>
                <InterviewArena />
              </ProfileRequired>
            </Protected>
          }
        />
        <Route
          path="/interviews/history"
          element={
            <ProtectedRoute>
              <ProfileRequired>
                <Navbar />
                <InterviewHistory />
              </ProfileRequired>
            </ProtectedRoute>
          }
        />

        <Route
          path="/interview/:sessionId/report"
          element={
            <ProtectedRoute>
              <InterviewReport />
            </ProtectedRoute>
          }
        />

        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}
