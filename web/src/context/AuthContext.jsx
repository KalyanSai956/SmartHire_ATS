import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL;
const publishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

export const supabase =
  url && publishableKey ? createClient(url, publishableKey) : null;

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }

    let mounted = true;

    async function loadSession() {
      try {
        const { data, error } = await supabase.auth.getSession();

        if (!mounted) return;

        if (error) {
          console.error("Get session error:", error);
          setSession(null);
        } else {
          setSession(data?.session ?? null);
        }
      } catch (error) {
        console.error("Session loading error:", error);

        if (mounted) {
          setSession(null);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, nextSession) => {
      console.log("Auth event:", event);

      if (!mounted) return;

      setSession(nextSession ?? null);
      setLoading(false);
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  // ============================================================
  // SIGN IN
  // ============================================================

  const signIn = async (email, password) => {
    if (!supabase) {
      throw new Error("SmartHire authentication is not configured.");
    }

    const cleanEmail = email.trim().toLowerCase();

    const { data, error } = await supabase.auth.signInWithPassword({
      email: cleanEmail,
      password,
    });

    if (error) {
      throw error;
    }

    setSession(data?.session ?? null);

    return {
      data,
      error: null,
    };
  };

  // ============================================================
  // SIGN UP
  // ============================================================

  const signUp = async (email, password, fullName) => {
    if (!supabase) {
      throw new Error("SmartHire authentication is not configured.");
    }

    const cleanEmail = email.trim().toLowerCase();
    const cleanName = fullName.trim();

    const { data, error } = await supabase.auth.signUp({
      email: cleanEmail,
      password,
      options: {
        data: {
          full_name: cleanName,
        },
      },
    });

    if (error) {
      throw error;
    }

    if (data?.session) {
      setSession(data.session);
    }

    return {
      data,
      error: null,
    };
  };

  // ============================================================
  // SIGN OUT
  // ============================================================

  const signOut = async () => {
    if (!supabase) {
      throw new Error("SmartHire authentication is not configured.");
    }

    const { error } = await supabase.auth.signOut();

    if (error) {
      console.error("Supabase sign out error:", error);

      throw error;
    }

    setSession(null);

    return true;
  };

  const value = useMemo(
    () => ({
      session,
      user: session?.user ?? null,
      accessToken: session?.access_token ?? null,
      loading,
      configured: Boolean(supabase),

      signIn,
      signUp,
      signOut,
    }),
    [session, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
