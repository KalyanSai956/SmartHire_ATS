import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  CheckCircle2,
  LockKeyhole,
  Mail,
  Sparkles,
  UserRound,
  X,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

function isValidGmail(email) {
  const value = email.trim().toLowerCase();

  return /^[a-z0-9._%+-]+@gmail\.com$/.test(value);
}

function getAuthErrorMessage(error, isLogin) {
  const message = error?.message?.toLowerCase() || "";

  if (
    message.includes("invalid login credentials") ||
    message.includes("invalid credentials")
  ) {
    return "Email or password is incorrect.";
  }

  if (
    message.includes("user already registered") ||
    message.includes("already registered")
  ) {
    return "An account with this email already exists. Please sign in.";
  }

  if (
    message.includes("email not confirmed") ||
    message.includes("email confirmation")
  ) {
    return "Email confirmation is enabled in Supabase. Please disable it to use instant sign up.";
  }

  if (message.includes("password")) {
    return "Please use a valid password with at least 6 characters.";
  }

  if (message.includes("rate limit")) {
    return "Too many attempts. Please wait a moment and try again.";
  }

  if (message.includes("network")) {
    return "Network error. Please check your internet connection and try again.";
  }

  if (isLogin) {
    return "Unable to sign in. Please check your details and try again.";
  }

  return "Unable to create your account. Please try again.";
}

export default function AuthModal({ mode = "login", onClose, onModeChange }) {
  const navigate = useNavigate();

  const { signIn, signUp, configured } = useAuth();

  const isLogin = mode === "login";

  const [form, setForm] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = "";
    };
  }, []);

  useEffect(() => {
    setError("");
    setSuccess("");
  }, [mode]);

  function update(key, value) {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));

    if (error) {
      setError("");
    }

    if (success) {
      setSuccess("");
    }
  }

  function closeOnBackdrop(event) {
    if (event.target === event.currentTarget && !busy) {
      onClose();
    }
  }

  async function submit(event) {
    event.preventDefault();

    setError("");
    setSuccess("");

    // ----------------------------------------------------------
    // Configuration
    // ----------------------------------------------------------

    if (!configured) {
      setError(
        "SmartHire authentication is not configured. Please check your environment settings.",
      );
      return;
    }

    // ----------------------------------------------------------
    // Name validation
    // ----------------------------------------------------------

    if (!isLogin) {
      const fullName = form.fullName.trim();

      if (!fullName) {
        setError("Please enter your full name.");
        return;
      }

      if (fullName.length < 2) {
        setError("Please enter your complete name.");
        return;
      }
    }

    // ----------------------------------------------------------
    // Gmail validation
    // ----------------------------------------------------------

    const email = form.email.trim().toLowerCase();

    if (!email) {
      setError("Please enter your email address.");
      return;
    }

    if (!isValidGmail(email)) {
      setError("Please provide a valid Gmail address.");
      return;
    }

    // ----------------------------------------------------------
    // Password validation
    // ----------------------------------------------------------

    if (!form.password) {
      setError("Please enter your password.");
      return;
    }

    if (form.password.length < 6) {
      setError("Password must contain at least 6 characters.");
      return;
    }

    // ----------------------------------------------------------
    // Confirm password
    // ----------------------------------------------------------

    if (!isLogin) {
      if (!form.confirmPassword) {
        setError("Please confirm your password.");
        return;
      }

      if (form.password !== form.confirmPassword) {
        setError("Passwords do not match.");
        return;
      }
    }

    setBusy(true);

    try {
      // ========================================================
      // LOGIN
      // ========================================================

      if (isLogin) {
        const { data } = await signIn(email, form.password);

        if (!data?.session) {
          setError("Unable to create a login session. Please try again.");

          return;
        }

        onClose();

        navigate("/dashboard", {
          replace: true,
        });

        return;
      }

      // ========================================================
      // SIGN UP
      // ========================================================

      const { data } = await signUp(email, form.password, form.fullName.trim());

      // --------------------------------------------------------
      // Supabase should return a session because email
      // confirmation is disabled.
      // --------------------------------------------------------

      if (!data?.session) {
        setError(
          "Account created, but automatic sign in was not completed. Please disable email confirmation in Supabase and try again.",
        );

        return;
      }

      setSuccess("Account created successfully.");

      // Small delay so the success message is visible.
      setTimeout(() => {
        onClose();

        navigate("/onboarding", {
          replace: true,
        });
      }, 500);
    } catch (authError) {
      console.error("Authentication error:", authError);

      setError(getAuthErrorMessage(authError, isLogin));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-modal-overlay" onMouseDown={closeOnBackdrop}>
      <div
        className="auth-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-modal-title"
      >
        {/* CLOSE */}

        <button
          type="button"
          className="auth-modal-close"
          onClick={onClose}
          disabled={busy}
          aria-label="Close"
        >
          <X size={19} />
        </button>

        {/* LEFT BRAND PANEL */}

        <div className="auth-modal-brand-panel">
          <div className="auth-modal-brand">
            <span className="auth-modal-brand-mark">
              <Sparkles size={18} />
            </span>

            <span>
              Smart<span>Hire</span>
            </span>
          </div>

          <div className="auth-modal-pitch">
            <span className="auth-modal-kicker">
              <Sparkles size={13} />
              AI-POWERED ATS
            </span>

            <h3>
              {isLogin
                ? "Build a resume that gets noticed."
                : "Turn your resume into an advantage."}
            </h3>

            <p>
              {isLogin
                ? "Continue analyzing your resume, validating your skills, and improving your job match."
                : "Analyze your ATS score, discover skill gaps, and improve your resume with AI-powered insights."}
            </p>

            <div className="auth-modal-benefits">
              <span>
                <CheckCircle2 size={15} />
                ATS compatibility scoring
              </span>

              <span>
                <CheckCircle2 size={15} />
                Job description matching
              </span>

              <span>
                <CheckCircle2 size={15} />
                AI recommendations
              </span>

              <span>
                <CheckCircle2 size={15} />
                Skill validation
              </span>
            </div>
          </div>
        </div>

        {/* RIGHT FORM */}

        <div className="auth-modal-form-panel">
          <div className="auth-modal-form-wrap">
            <p className="auth-modal-eyebrow">
              {isLogin ? "WELCOME BACK" : "GET STARTED"}
            </p>

            <h2 id="auth-modal-title">
              {isLogin
                ? "Sign in to SmartHire"
                : "Create your SmartHire account"}
            </h2>

            <p className="auth-modal-subtitle">
              {isLogin
                ? "Continue analyzing and improving your resume."
                : "Create your account and get started in a few seconds."}
            </p>

            <form onSubmit={submit}>
              {/* FULL NAME */}

              {!isLogin && (
                <label className="auth-modal-field">
                  <span>Full name</span>

                  <div>
                    <UserRound size={16} />

                    <input
                      type="text"
                      value={form.fullName}
                      onChange={(e) => update("fullName", e.target.value)}
                      placeholder="Your full name"
                      autoComplete="name"
                      required
                    />
                  </div>
                </label>
              )}

              {/* EMAIL */}

              <label className="auth-modal-field">
                <span>Email</span>

                <div>
                  <Mail size={16} />

                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => update("email", e.target.value)}
                    placeholder="you@gmail.com"
                    autoComplete="email"
                    required
                  />
                </div>

                {!isLogin && (
                  <small className="auth-modal-field-hint">
                    Please use a Gmail address.
                  </small>
                )}
              </label>

              {/* PASSWORD */}

              <label className="auth-modal-field">
                <span>Password</span>

                <div>
                  <LockKeyhole size={16} />

                  <input
                    type="password"
                    value={form.password}
                    onChange={(e) => update("password", e.target.value)}
                    placeholder={
                      isLogin ? "Your password" : "At least 6 characters"
                    }
                    autoComplete={isLogin ? "current-password" : "new-password"}
                    required
                  />
                </div>
              </label>

              {/* CONFIRM PASSWORD */}

              {!isLogin && (
                <label className="auth-modal-field">
                  <span>Confirm password</span>

                  <div>
                    <LockKeyhole size={16} />

                    <input
                      type="password"
                      value={form.confirmPassword}
                      onChange={(e) =>
                        update("confirmPassword", e.target.value)
                      }
                      placeholder="Repeat your password"
                      autoComplete="new-password"
                      required
                    />
                  </div>
                </label>
              )}

              {/* ERROR */}

              {error && (
                <div className="auth-modal-error" role="alert">
                  {error}
                </div>
              )}

              {/* SUCCESS */}

              {success && (
                <div className="auth-modal-success" role="status">
                  {success}
                </div>
              )}

              {/* SUBMIT */}

              <button
                type="submit"
                className="auth-modal-submit"
                disabled={busy}
              >
                {busy
                  ? isLogin
                    ? "Signing in..."
                    : "Creating account..."
                  : isLogin
                    ? "Sign in"
                    : "Create account"}

                <ArrowRight size={16} />
              </button>
            </form>

            {/* SWITCH */}

            <div className="auth-modal-switch">
              {isLogin ? (
                <>
                  Don't have an account?
                  <button type="button" onClick={() => onModeChange("signup")}>
                    Create one
                  </button>
                </>
              ) : (
                <>
                  Already have an account?
                  <button type="button" onClick={() => onModeChange("login")}>
                    Sign in
                  </button>
                </>
              )}
            </div>

            <p className="auth-modal-privacy">
              Your SmartHire account uses your email and password to securely
              access your career profile.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
