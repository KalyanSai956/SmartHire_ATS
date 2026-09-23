import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getProfile } from "../services/api";

export default function ProfileRequired({ children }) {
  const { accessToken, session, loading: authLoading } = useAuth();

  const location = useLocation();

  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function checkProfile() {
      if (!session || !accessToken) {
        if (active) {
          setLoading(false);
        }

        return;
      }

      try {
        /*
         * Always check the actual profile from the backend.
         *
         * We intentionally do not rely on sessionStorage here.
         * This makes onboarding persistence work across:
         * - browser refresh
         * - closing the browser
         * - logging out
         * - logging back in
         * - different devices
         */
        const profile = await getProfile(accessToken);

        if (!active) return;

        const isCompleted = Boolean(profile?.onboarding_completed);

        setCompleted(isCompleted);
      } catch (err) {
        if (active) {
          setError(err.message || "Could not load your career profile.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    if (!authLoading) {
      checkProfile();
    }

    return () => {
      active = false;
    };
  }, [accessToken, session, authLoading]);

  /*
   * Authentication/profile loading.
   */
  if (authLoading || loading) {
    return (
      <div className="route-loader">
        <span className="loading-spinner" />
        <span>Loading your career profile...</span>
      </div>
    );
  }

  /*
   * No authenticated session.
   */
  if (!session) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location.pathname,
        }}
      />
    );
  }

  /*
   * Profile API failed.
   */
  if (error) {
    return (
      <div className="route-loader">
        <span>{error}</span>
      </div>
    );
  }

  /*
   * User has not completed onboarding.
   *
   * Onboarding.jsx will load the saved onboarding_step
   * and restore the user's previous answers.
   */
  if (!completed) {
    return (
      <Navigate
        to="/onboarding"
        replace
        state={{
          from: location.pathname,
        }}
      />
    );
  }

  return children;
}
