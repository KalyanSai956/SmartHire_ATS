import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useNavigate } from "react-router-dom";
import {
  AlertCircle,
  ArrowRight,
  BriefcaseBusiness,
  CheckCircle2,
  FileText,
  GraduationCap,
  Sparkles,
  Target,
  TrendingUp,
  Trophy,
  Upload,
  UserRound,
  Zap,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getHistory, getProfile } from "../services/api";

import { useAuth } from "../context/AuthContext";

import { getAtsScore, getJdMatch, normalizeHistory } from "../utils/analysis";

import AnalysisTable from "../components/AnalysisTable";

function StatCard({ label, value, suffix = "", helper, tone, icon: Icon }) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        <span className="stat-label">{label}</span>
      </div>

      <div className="stat-value">
        {value}
        <span>{suffix}</span>
      </div>

      <div className="stat-bottom">
        <span>{helper}</span>
      </div>
    </div>
  );
}

function ProfileTag({ children }) {
  return <span className="career-tag">{children}</span>;
}

function QuickAction({ icon: Icon, title, text, to, disabled = false }) {
  if (disabled) {
    return (
      <div className="quick-action disabled">
        <span className="quick-action-icon">
          <Icon size={18} />
        </span>

        <div>
          <strong>{title}</strong>
          <span>{text}</span>
        </div>

        <span className="coming-soon">Soon</span>
      </div>
    );
  }

  return (
    <Link to={to} className="quick-action">
      <span className="quick-action-icon">
        <Icon size={18} />
      </span>

      <div>
        <strong>{title}</strong>
        <span>{text}</span>
      </div>

      <ArrowRight size={16} className="quick-action-arrow" />
    </Link>
  );
}

function ProfileProgress({ profile }) {
  const checks = [
    {
      label: "Username",
      complete: Boolean(profile?.username?.trim()),
    },
    {
      label: "Skills",
      complete: Array.isArray(profile?.skills) && profile.skills.length > 0,
    },
    {
      label: "Target roles",
      complete:
        Array.isArray(profile?.target_roles) && profile.target_roles.length > 0,
    },
    {
      label: "Experience",
      complete: Boolean(profile?.experience?.trim()),
    },
    {
      label: "Resume",
      complete: Boolean(profile?.resume_filename),
    },
  ];

  const completed = checks.filter((item) => item.complete).length;

  const percentage = Math.round((completed / checks.length) * 100);

  return {
    checks,
    completed,
    percentage,
  };
}

export default function Dashboard() {
  const { accessToken, user } = useAuth();

  const [profile, setProfile] = useState(null);

  const [history, setHistory] = useState([]);

  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      setLoading(true);
      setError("");

      try {
        const [profileData, historyData] = await Promise.all([
          getProfile(accessToken),
          getHistory(accessToken),
        ]);

        if (!active) return;

        setProfile(profileData);
        setHistory(normalizeHistory(historyData));
      } catch (err) {
        if (active) {
          setError(err.message || "Could not load your dashboard.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    if (accessToken) {
      loadDashboard();
    }

    return () => {
      active = false;
    };
  }, [accessToken]);

  const displayName =
    profile?.username ||
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email?.split("@")[0] ||
    "there";

  const latest = history.length ? history[0] : null;

  const latestScore = latest ? getAtsScore(latest.result) : 0;

  const latestMatch = latest ? getJdMatch(latest.result) : 0;

  const bestScore = history.length
    ? Math.max(...history.map((item) => getAtsScore(item.result)))
    : 0;

  const averageScore = history.length
    ? Math.round(
        history.reduce((total, item) => total + getAtsScore(item.result), 0) /
          history.length,
      )
    : 0;

  const chartData = useMemo(
    () =>
      history
        .slice(0, 7)
        .reverse()
        .map((item, index) => ({
          name: item.createdAt
            ? new Date(item.createdAt).toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
              })
            : `Scan ${index + 1}`,

          score: getAtsScore(item.result),
        })),
    [history],
  );

  const profileProgress = ProfileProgress({
    profile,
  });

  if (loading) {
    return (
      <div className="page-shell">
        <div className="dashboard-loading">
          <span className="loading-spinner" />
          <span>Preparing your career workspace...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-5 page-shell">
      <section className="career-profile-banner">
        <div className="career-profile-main">
          <div className="career-avatar">
            <UserRound size={23} />
          </div>

          <div>
            <h2>
              {profile?.target_roles?.length
                ? profile.target_roles.join(" · ")
                : "Set your target role"}
            </h2>

            <div className="career-meta">
              <span>
                <GraduationCap size={14} />
                {profile?.experience || "Experience not set"}
              </span>

              {profile?.resume_filename && (
                <span>
                  <FileText size={14} />
                  {profile.resume_filename}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="career-profile-progress">
          <div className="progress-copy">
            <span>Profile completeness</span>
            <strong>{profileProgress.percentage}%</strong>
          </div>

          <div className="progress-track">
            <div
              className="progress-fill"
              style={{
                width: `${profileProgress.percentage}%`,
              }}
            />
          </div>

          <span className="progress-helper">
            {profileProgress.completed}/5 profile sections complete
          </span>
        </div>
      </section>

      {/* =================================================
          ERROR
          ================================================= */}

      {error && (
        <div className="dashboard-error">
          <AlertCircle size={17} />
          <span>{error}</span>
        </div>
      )}

      {/* =================================================
          STATS
          ================================================= */}

      <section className="stats-grid">
        <StatCard
          label="LATEST ATS SCORE"
          value={latestScore || "—"}
          suffix={latestScore ? "/100" : ""}
          helper={
            latestScore ? "Most recent analysis" : "Run your first analysis"
          }
          tone="green"
          icon={Zap}
        />

        <StatCard
          label="BEST ATS SCORE"
          value={bestScore || "—"}
          suffix={bestScore ? "/100" : ""}
          helper="Your personal best"
          tone="gold"
          icon={Trophy}
        />

        <StatCard
          label="TOTAL ANALYSES"
          value={history.length}
          helper="Saved resume analyses"
          tone="purple"
          icon={FileText}
        />

        <StatCard
          label="AVERAGE ATS SCORE"
          value={averageScore || "—"}
          suffix={averageScore ? "/100" : ""}
          helper="Across your analyses"
          tone="orange"
          icon={TrendingUp}
        />
      </section>

      {/* =================================================
          MAIN GRID
          ================================================= */}

      <section className="dashboard-main-grid">
        {/* SCORE TREND */}

        <div className="panel">
          <div className="panel-header">
            <div>
              <h2>Resume Performance</h2>

              <p>See how your ATS score changes across your analyses.</p>
            </div>

            {history.length > 0 && (
              <span className="panel-badge">{history.length} scans</span>
            )}
          </div>

          <div className="chart-wrap">
            {chartData.length ? (
              <ResponsiveContainer width="100%" height={245}>
                <AreaChart
                  data={chartData}
                  margin={{
                    top: 10,
                    right: 4,
                    left: -22,
                    bottom: 0,
                  }}
                >
                  <defs>
                    <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="0%"
                        stopColor="#22c55e"
                        stopOpacity={0.32}
                      />

                      <stop
                        offset="100%"
                        stopColor="#22c55e"
                        stopOpacity={0.02}
                      />
                    </linearGradient>
                  </defs>

                  <CartesianGrid
                    stroke="rgba(255,255,255,0.08)"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="name"
                    axisLine={false}
                    tickLine={false}
                    tick={{
                      fill: "#7A7A85",
                      fontSize: 12,
                    }}
                  />

                  <YAxis
                    domain={[0, 100]}
                    axisLine={false}
                    tickLine={false}
                    tick={{
                      fill: "#7A7A85",
                      fontSize: 12,
                    }}
                  />

                  <Tooltip
                    contentStyle={{
                      background: "#111113",
                      border: "1px solid rgba(255,255,255,0.08)",
                      borderRadius: 10,
                      color: "#F5F5F7",
                      fontSize: 13,
                    }}
                    labelStyle={{ color: "#9A9AA4" }}
                    itemStyle={{ color: "#4ADE80" }}
                  />

                  <Area
                    type="monotone"
                    dataKey="score"
                    stroke="#22c55e"
                    strokeWidth={3}
                    fill="url(#scoreFill)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="chart-empty">
                <span className="empty-icon">
                  <TrendingUp size={18} />
                </span>

                <strong>Your score trend will appear here.</strong>

                <span>Analyze a resume to start tracking your progress.</span>

                <Link to="/analyze" className="outline-button">
                  Analyze Resume
                  <ArrowRight size={15} />
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* PROFILE */}

        <div className="panel career-profile-panel">
          <div className="profile-detail-block">
            <div className="profile-detail-heading">
              {/* <Target size={16} /> */}
              <span> Target Roles</span>
            </div>

            <div className="career-tags">
              {profile?.target_roles?.length ? (
                profile.target_roles.map((role) => (
                  <ProfileTag key={role}> {role}</ProfileTag>
                ))
              ) : (
                <span className="muted">No target roles yet</span>
              )}
            </div>
          </div>

          <div className="profile-detail-block">
            <div className="profile-detail-heading">
              <Zap size={16} />
              <span> Skills</span>
            </div>

            <div className="career-tags">
              {profile?.skills?.length ? (
                profile.skills
                  .slice(0, 10)
                  .map((skill) => <ProfileTag key={skill}>{skill}</ProfileTag>)
              ) : (
                <span className="muted">No skills added</span>
              )}
            </div>

            {profile?.skills?.length > 10 && (
              <span className="profile-more">
                +{profile.skills.length - 10} more
              </span>
            )}
          </div>

          <div className="profile-detail-block">
            <div className="profile-detail-heading">
              <span>Experience</span>
            </div>

            <strong className="experience-value">
              {profile?.experience || "Not specified"}
            </strong>
          </div>

          <div className="profile-resume-status">
            <div className="resume-status-icon">
              <CheckCircle2 size={17} />
            </div>

            <div>
              <strong>Resume connected</strong>

              <span>{profile?.resume_filename || "No resume uploaded"}</span>
            </div>
          </div>
        </div>
      </section>
      <div className="heading-actions">
        <Link to="/analyze" className="button primary">
          <Upload size={17} />
          Analyze Resume
        </Link>
        <button
          type="button"
          className="button primary"
          onClick={() => navigate("/interview/setup")}
        >
          Start Interview
        </button>
      </div>
    </div>
  );
}
