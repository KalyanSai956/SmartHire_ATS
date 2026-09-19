import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getProfile } from "../services/api";

const ONBOARDING_CACHE_KEY = "smarthire_onboarding_completed";

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

      /*
       * If this user has already completed onboarding during
       * the current login session, don't unnecessarily redirect
       * them while navigating between protected pages.
       */
      const cachedCompleted =
        sessionStorage.getItem(ONBOARDING_CACHE_KEY) === "true";

      if (cachedCompleted) {
        if (active) {
          setCompleted(true);
          setLoading(false);
        }

        /*
         * Still verify the profile in the background.
         * If the request fails, we keep the cached completed state.
         */
        try {
          const profile = await getProfile(accessToken);

          if (!active) return;

          if (profile?.onboarding_completed) {
            sessionStorage.setItem(ONBOARDING_CACHE_KEY, "true");
            setCompleted(true);
          }
        } catch (err) {
          console.warn("Background profile verification failed:", err);
        }

        return;
      }

      try {
        const profile = await getProfile(accessToken);

        if (!active) return;

        const isCompleted = Boolean(profile?.onboarding_completed);

        setCompleted(isCompleted);

        if (isCompleted) {
          sessionStorage.setItem(ONBOARDING_CACHE_KEY, "true");
        }
      } catch (err) {
        if (active) {
          setError(err.message || "Could not load your profile.");
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
   * Authentication is still loading.
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
   * Only redirect to onboarding when we have actually
   * confirmed that onboarding has not been completed.
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
