import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  Bot,
  BriefcaseBusiness,
  CheckCircle2,
  Clock3,
  FileSearch,
  Gauge,
  Inbox,
  Loader2,
  Mail,
  Play,
  RefreshCw,
  Search,
  Send,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Square,
  WandSparkles,
  XCircle
} from "lucide-react";
import "./App.css";

const navItems = [
  { label: "Dashboard", icon: BarChart3 },
  { label: "Jobs", icon: BriefcaseBusiness },
  { label: "Outreach", icon: Send },
  { label: "Replies", icon: Inbox },
  { label: "ATS Optimizer", icon: ShieldCheck },
  { label: "Settings", icon: Settings }
];

const statusFilters = ["all", "new", "queued", "applied", "replied"];

const seedJobs = [
  {
    id: "sample-1",
    title: "Software Engineering Intern",
    company: "Queued once API connects",
    status: "new",
    match_score: 84,
    location: "Remote",
    source: "InternMailer",
    created_at: new Date().toISOString()
  }
];

function apiUrl(path) {
  return path;
}

async function request(path, options = {}) {
  const response = await fetch(apiUrl(path), {
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers
    },
    ...options
  });

  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message =
      typeof body === "string"
        ? body
        : body?.error || body?.message || `${response.status} ${response.statusText}`;
    throw new Error(message);
  }

  return body;
}

async function resource(label, path, options = {}) {
  try {
    return { label, value: await request(path, options) };
  } catch (err) {
    err.resourceLabel = label;
    throw err;
  }
}

function asArray(payload, keys = []) {
  if (Array.isArray(payload)) return payload;
  for (const key of keys) {
    if (Array.isArray(payload?.[key])) return payload[key];
  }
  return [];
}

function numberFrom(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function getJobId(job, index) {
  return job.id || job.job_id || job.url || `${job.company || "job"}-${index}`;
}

function getJobStatus(job) {
  return String(job.status || job.state || "new").toLowerCase();
}

function formatDate(value) {
  if (!value) return "Not synced";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(date);
}

function summarizeResult(result) {
  if (!result) return "Completed";
  if (typeof result === "string") return result.slice(0, 180);
  return (
    result.message ||
    result.status ||
    result.summary ||
    result.result ||
    JSON.stringify(result).slice(0, 180)
  );
}

function App() {
  const [activeNav, setActiveNav] = useState("Dashboard");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [replies, setReplies] = useState([]);
  const [daemon, setDaemon] = useState(null);
  const [settingsData, setSettingsData] = useState(null);
  const [emailPreviews, setEmailPreviews] = useState([]);
  const [atsInput, setAtsInput] = useState("");
  const [atsResult, setAtsResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionState, setActionState] = useState({});
  const [activityLog, setActivityLog] = useState([]);

  const addActivity = useCallback((title, detail, tone = "info") => {
    setActivityLog((current) => [
      {
        id: `${Date.now()}-${title}`,
        title,
        detail,
        tone,
        time: new Date().toISOString()
      },
      ...current.slice(0, 9)
    ]);
  }, []);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");

    const calls = await Promise.allSettled([
      resource("health", "/api/health"),
      resource("stats", "/api/stats"),
      resource("jobs", "/api/jobs"),
      resource("replies", "/api/replies"),
      resource("daemon", "/api/daemon/status")
    ]);

    const [healthResult, statsResult, jobsResult, repliesResult, daemonResult] = calls;

    if (healthResult.status === "fulfilled") setHealth(healthResult.value.value);
    if (statsResult.status === "fulfilled") setStats(statsResult.value.value);
    if (jobsResult.status === "fulfilled") {
      setJobs(asArray(jobsResult.value.value, ["jobs", "data", "items"]));
    }
    if (repliesResult.status === "fulfilled") {
      setReplies(asArray(repliesResult.value.value, ["replies", "data", "items"]));
    }
    if (daemonResult.status === "fulfilled") {
      setDaemon(daemonResult.value.value.daemon || daemonResult.value.value);
    }
    const failed = calls.filter((call) => call.status === "rejected");
    if (failed.length) {
      setError(
        failed
          .map((call) => {
            const label = call.reason?.resourceLabel || "resource";
            const message = call.reason?.message || "request failed";
            return `${label}: ${message}`;
          })
          .join(" | ")
      );
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  async function runAction(key, label, path, options = {}, refresh = true) {
    setActionState((current) => ({ ...current, [key]: true }));
    try {
      const result = await request(path, options);
      addActivity(label, summarizeResult(result), "success");
      if (refresh) await loadDashboard();
      return result;
    } catch (err) {
      addActivity(label, err.message, "error");
      setError(err.message);
      return null;
    } finally {
      setActionState((current) => ({ ...current, [key]: false }));
    }
  }

  async function discoverJobs() {
    await runAction("discover", "Discover Jobs", "/api/jobs/discover", {
      method: "POST",
      body: JSON.stringify({})
    });
  }

  async function applyQueue() {
    await runAction("apply", "Apply Queue", "/api/jobs/apply", {
      method: "POST",
      body: JSON.stringify({ limit: 50 })
    });
  }

  async function sendPreviewEmails() {
    const previewResult = await runAction("preview", "Preview Emails", "/preview-emails?count=3", {
      method: "GET"
    }, false);
    setEmailPreviews(asArray(previewResult, ["previews"]));
    await runAction("send", "Send Preview Emails", "/send-emails", {
      method: "POST",
      body: JSON.stringify({ count: 3, preview: true })
    });
  }

  async function toggleDaemon(nextState) {
    await runAction(
      nextState,
      nextState === "start" ? "Start Daemon" : "Stop Daemon",
      `/api/daemon/${nextState}`,
      { method: "POST" }
    );
  }

  async function optimizeResume() {
    const selectedJob = filteredJobs[0] || jobs[0] || seedJobs[0];
    const jobDescription =
      atsInput.trim() ||
      selectedJob.description ||
      selectedJob.summary ||
      `${selectedJob.title || "Internship"} at ${selectedJob.company || "target company"}`;
    const payload = {
      role: selectedJob.title || selectedJob.role || "Software Engineering Intern",
      company: selectedJob.company || "Target Company",
      skills: "Python, JavaScript, React",
      job_description: jobDescription,
      resume_text: settingsData?.resume_path || ""
    };

    setActionState((current) => ({ ...current, optimize: true }));
    try {
      const [analysis, coverLetter, interviewGuide] = await Promise.all([
        request("/api/ai/analyze-resume", {
          method: "POST",
          body: JSON.stringify(payload)
        }),
        request("/api/ai/cover-letter", {
          method: "POST",
          body: JSON.stringify(payload)
        }),
        request("/api/ai/interview-guide", {
          method: "POST",
          body: JSON.stringify(payload)
        })
      ]);

      addActivity(
        "Optimize Resume",
        [analysis, coverLetter, interviewGuide].map(summarizeResult).join(" | "),
        "success"
      );
      setAtsResult({ analysis, coverLetter, interviewGuide });
    } catch (err) {
      addActivity("Optimize Resume", err.message, "error");
      setError(err.message);
    } finally {
      setActionState((current) => ({ ...current, optimize: false }));
    }
  }

  const filteredJobs = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return jobs.filter((job) => {
      const text = `${job.title || job.role || ""} ${job.company || ""} ${
        job.location || ""
      } ${job.source || ""}`.toLowerCase();
      const statusMatches = filter === "all" || getJobStatus(job) === filter;
      return statusMatches && (!normalizedQuery || text.includes(normalizedQuery));
    });
  }, [jobs, query, filter]);

  const displayJobs = filteredJobs.length ? filteredJobs : loading ? [] : seedJobs;
  const appliedCount = jobs.filter((job) => getJobStatus(job) === "applied").length;
  const queuedCount = jobs.filter((job) => ["queued", "ready"].includes(getJobStatus(job))).length;
  const replyCount = replies.length || numberFrom(stats?.replies || stats?.reply_count);
  const daemonRunning =
    daemon?.running === true ||
    daemon?.status === "running" ||
    daemon?.daemon_status === "running" ||
    health?.daemon === "running";
  const healthy =
    health?.ok === true ||
    health?.status === "ok" ||
    health?.status === "healthy" ||
    health?.healthy === true;

  const activeTitle = activeNav === "ATS Optimizer" ? "ATS Optimizer" : activeNav;

  const kpis = [
    {
      label: "Tracked jobs",
      value: numberFrom(stats?.jobs || stats?.total_jobs, jobs.length),
      delta: `${displayJobs.length} visible`,
      icon: BriefcaseBusiness
    },
    {
      label: "Queued",
      value: numberFrom(stats?.queued || stats?.queued_jobs, queuedCount),
      delta: "ready to apply",
      icon: Clock3
    },
    {
      label: "Applied",
      value: numberFrom(stats?.applied || stats?.applications_sent, appliedCount),
      delta: "pipeline output",
      icon: CheckCircle2
    },
    {
      label: "Replies",
      value: replyCount,
      delta: "inbox signals",
      icon: Mail
    }
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            IM
          </div>
          <div>
            <p>InternMailer</p>
            <span>Ops console</span>
          </div>
        </div>

        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                type="button"
                className={activeNav === item.label ? "nav-item active" : "nav-item"}
                onClick={() => setActiveNav(item.label)}
                aria-current={activeNav === item.label ? "page" : undefined}
              >
                <Icon size={18} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <div className="search-wrap">
            <Search size={18} aria-hidden="true" />
            <label className="sr-only" htmlFor="job-search">
              Search jobs
            </label>
            <input
              id="job-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search company, role, source"
            />
          </div>

          <div className="topbar-controls">
            <label className="filter-label" htmlFor="status-filter">
              <SlidersHorizontal size={16} aria-hidden="true" />
              <span>Status</span>
            </label>
            <select
              id="status-filter"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            >
              {statusFilters.map((status) => (
                <option key={status} value={status}>
                  {status === "all" ? "All jobs" : status}
                </option>
              ))}
            </select>

            <div className={daemonRunning ? "daemon online" : "daemon"}>
              <Activity size={16} aria-hidden="true" />
              <span>{daemonRunning ? "Daemon online" : "Daemon idle"}</span>
            </div>

            <button
              type="button"
              className="button secondary icon-button"
              onClick={loadDashboard}
              disabled={loading}
              aria-label="Refresh dashboard"
            >
              <RefreshCw size={17} aria-hidden="true" />
            </button>
            <button
              type="button"
              className="button primary"
              onClick={() => toggleDaemon(daemonRunning ? "stop" : "start")}
              disabled={actionState.start || actionState.stop}
            >
              {daemonRunning ? (
                <Square size={16} aria-hidden="true" />
              ) : (
                <Play size={16} aria-hidden="true" />
              )}
              <span>Run Cycle</span>
            </button>
          </div>
        </header>

        <main className="content">
          <section className="page-heading" aria-labelledby="dashboard-title">
            <div>
              <h1 id="dashboard-title">{activeTitle}</h1>
              <p>Monitor discovery, applications, outreach, replies, and ATS prep from one dense operations view.</p>
            </div>
            <div className="sync-state" aria-live="polite">
              {loading ? (
                <>
                  <Loader2 className="spin" size={16} aria-hidden="true" />
                  <span>Syncing</span>
                </>
              ) : (
                <>
                  <Gauge size={16} aria-hidden="true" />
                  <span>Last refresh {formatDate(new Date().toISOString())}</span>
                </>
              )}
            </div>
          </section>

          {error ? (
            <div className="alert error" role="alert">
              <XCircle size={18} aria-hidden="true" />
              <span>{error}</span>
            </div>
          ) : null}

          <section className="kpi-grid" aria-label="Key performance indicators">
            {kpis.map((kpi) => {
              const Icon = kpi.icon;
              return (
                <article className="kpi-card" key={kpi.label}>
                  <div className="kpi-icon">
                    <Icon size={18} aria-hidden="true" />
                  </div>
                  <div>
                    <p>{kpi.label}</p>
                    <strong>{kpi.value}</strong>
                    <span>{kpi.delta}</span>
                  </div>
                </article>
              );
            })}
          </section>

          <section className="action-strip" aria-label="Primary actions">
            <ActionButton
              icon={FileSearch}
              label="Discover Jobs"
              busy={actionState.discover}
              onClick={discoverJobs}
            />
            <ActionButton
              icon={BriefcaseBusiness}
              label="Apply Queue"
              busy={actionState.apply}
              onClick={applyQueue}
            />
            <ActionButton
              icon={Send}
              label="Send Preview Emails"
              busy={actionState.preview || actionState.send}
              onClick={sendPreviewEmails}
            />
            <ActionButton
              icon={WandSparkles}
              label="Optimize Resume"
              busy={actionState.optimize}
              onClick={optimizeResume}
            />
          </section>

          {["Dashboard", "Jobs"].includes(activeNav) ? (
          <div className="dashboard-grid">
            <JobPipelinePanel
              displayJobs={displayJobs}
              loading={loading}
              title={activeNav === "Jobs" ? "Jobs" : "Job pipeline"}
            />

            {activeNav === "Dashboard" ? (
            <aside className="side-panel" aria-label="Activity and health">
              <HealthPanel
                health={health}
                healthy={healthy}
                daemonRunning={daemonRunning}
                replyCount={replyCount}
                actionState={actionState}
                toggleDaemon={toggleDaemon}
              />
              <ActivityPanel activityLog={activityLog} />
              <section className="panel ai-panel">
                <div className="panel-heading">
                  <div>
                    <h2>ATS tools</h2>
                    <p>Resume and interview prep</p>
                  </div>
                  <Bot size={18} aria-hidden="true" />
                </div>
                <button
                  type="button"
                  className="button full"
                  onClick={optimizeResume}
                  disabled={actionState.optimize}
                >
                  {actionState.optimize ? (
                    <Loader2 className="spin" size={16} aria-hidden="true" />
                  ) : (
                    <WandSparkles size={16} aria-hidden="true" />
                  )}
                  Generate ATS pack
                </button>
              </section>
            </aside>
            ) : null}
          </div>
          ) : null}

          {activeNav === "Outreach" ? (
            <OutreachView
              emailPreviews={emailPreviews}
              actionState={actionState}
              sendPreviewEmails={sendPreviewEmails}
              stats={stats}
            />
          ) : null}

          {activeNav === "Replies" ? <RepliesView replies={replies} /> : null}

          {activeNav === "ATS Optimizer" ? (
            <ATSView
              atsInput={atsInput}
              setAtsInput={setAtsInput}
              atsResult={atsResult}
              actionState={actionState}
              optimizeResume={optimizeResume}
            />
          ) : null}

          {activeNav === "Settings" ? (
            <SettingsView settingsData={settingsData} health={health} daemon={daemon} />
          ) : null}
        </main>
      </div>
    </div>
  );
}

function JobPipelinePanel({ displayJobs, loading, title }) {
  return (
    <section className="panel pipeline-panel" aria-labelledby="pipeline-title">
              <div className="panel-heading">
                <div>
                  <h2 id="pipeline-title">{title}</h2>
                  <p>{displayJobs.length} rows in current view</p>
                </div>
              </div>

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Role</th>
                      <th scope="col">Company</th>
                      <th scope="col">Status</th>
                      <th scope="col">Match</th>
                      <th scope="col">Source</th>
                      <th scope="col">Updated</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr>
                        <td colSpan="6">
                          <div className="empty-state">
                            <Loader2 className="spin" size={18} aria-hidden="true" />
                            Loading jobs
                          </div>
                        </td>
                      </tr>
                    ) : displayJobs.length ? (
                      displayJobs.map((job, index) => (
                        <tr key={getJobId(job, index)}>
                          <td>
                            <strong>{job.title || job.role || "Untitled role"}</strong>
                            <span>{job.location || job.remote || "Location not listed"}</span>
                          </td>
                          <td>{job.company || job.organization || "Unknown company"}</td>
                          <td>
                            <span className={`status-pill ${getJobStatus(job)}`}>
                              {getJobStatus(job)}
                            </span>
                          </td>
                          <td>
                            <div className="score">
                              <span
                                style={{
                                  width: `${Math.min(
                                    100,
                                    Math.max(0, numberFrom(job.match_score || job.score, 0))
                                  )}%`
                                }}
                              />
                            </div>
                            {numberFrom(job.match_score || job.score, 0)}%
                          </td>
                          <td>{job.source || job.platform || "Direct"}</td>
                          <td>{formatDate(job.updated_at || job.created_at || job.date_found)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="6">
                          <div className="empty-state">
                            No jobs match the current search and filter.
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
  );
}

function HealthPanel({ health, healthy, daemonRunning, replyCount, actionState, toggleDaemon }) {
  const apiState = healthy ? "Healthy" : "Unknown";
  return (
    <section className="panel health-panel">
                <div className="panel-heading">
                  <div>
                    <h2>Health</h2>
                    <p>Service readiness</p>
                  </div>
                  <span className={healthy ? "health-dot good" : "health-dot"} aria-hidden="true" />
                </div>

                <dl className="health-list">
                  <div>
                    <dt>API</dt>
                    <dd>{apiState}</dd>
                  </div>
                  <div>
                    <dt>Daemon</dt>
                    <dd>{daemonRunning ? "Running" : "Stopped"}</dd>
                  </div>
                  <div>
                    <dt>Replies</dt>
                    <dd>{replyCount}</dd>
                  </div>
                </dl>

                <div className="daemon-actions">
                  <button
                    type="button"
                    className="button secondary"
                    onClick={() => toggleDaemon("start")}
                    disabled={actionState.start}
                  >
                    <Play size={15} aria-hidden="true" />
                    Start
                  </button>
                  <button
                    type="button"
                    className="button secondary"
                    onClick={() => toggleDaemon("stop")}
                    disabled={actionState.stop}
                  >
                    <Square size={15} aria-hidden="true" />
                    Stop
                  </button>
                </div>
              </section>
  );
}

function ActivityPanel({ activityLog }) {
  return (
    <section className="panel activity-panel">
                <div className="panel-heading">
                  <div>
                    <h2>Activity</h2>
                    <p>Recent operations</p>
                  </div>
                </div>

                <ol className="activity-list">
                  {(activityLog.length
                    ? activityLog
                    : [
                        {
                          id: "empty",
                          title: "Ready",
                          detail: "Run an operation to populate this feed.",
                          tone: "info",
                          time: new Date().toISOString()
                        }
                      ]
                  ).map((item) => (
                    <li key={item.id} className={item.tone}>
                      <span className="activity-marker" aria-hidden="true" />
                      <div>
                        <strong>{item.title}</strong>
                        <p>{item.detail}</p>
                        <time dateTime={item.time}>{formatDate(item.time)}</time>
                      </div>
                    </li>
                  ))}
                </ol>
              </section>
  );
}

function OutreachView({ emailPreviews, actionState, sendPreviewEmails, stats }) {
  return (
    <section className="panel view-panel">
      <div className="panel-heading">
        <div>
          <h2>Outreach queue</h2>
          <p>{numberFrom(stats?.emails_sent)} sent emails recorded</p>
        </div>
        <button
          type="button"
          className="button primary"
          onClick={sendPreviewEmails}
          disabled={actionState.preview || actionState.send}
        >
          <Send size={16} aria-hidden="true" />
          Preview batch
        </button>
      </div>
      <div className="preview-list">
        {(emailPreviews.length ? emailPreviews : [{ email: "No previews loaded", subject: "Click Preview batch" }]).map(
          (preview, index) => (
            <article key={`${preview.email}-${index}`} className="preview-item">
              <strong>{preview.subject || "Untitled email"}</strong>
              <span>{preview.email || preview.name || "Recipient unavailable"}</span>
            </article>
          )
        )}
      </div>
    </section>
  );
}

function RepliesView({ replies }) {
  return (
    <section className="panel view-panel">
      <div className="panel-heading">
        <div>
          <h2>Replies</h2>
          <p>{replies.length} inbox signals</p>
        </div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Sender</th>
              <th>Subject</th>
              <th>Category</th>
              <th>Sentiment</th>
              <th>Received</th>
            </tr>
          </thead>
          <tbody>
            {replies.length ? replies.map((reply, index) => (
              <tr key={`${reply.sender}-${index}`}>
                <td>{reply.sender || "Unknown"}</td>
                <td>{reply.subject || "No subject"}</td>
                <td><span className="status-pill replied">{reply.category || "unclassified"}</span></td>
                <td>{reply.sentiment || "neutral"}</td>
                <td>{formatDate(reply.received_date || reply.date)}</td>
              </tr>
            )) : (
              <tr><td colSpan="5"><div className="empty-state">No replies found yet.</div></td></tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ATSView({ atsInput, setAtsInput, atsResult, actionState, optimizeResume }) {
  return (
    <section className="panel view-panel">
      <div className="panel-heading">
        <div>
          <h2>ATS Optimizer</h2>
          <p>Paste a job description and generate the preparation pack</p>
        </div>
        <button type="button" className="button primary" onClick={optimizeResume} disabled={actionState.optimize}>
          <WandSparkles size={16} aria-hidden="true" />
          Optimize
        </button>
      </div>
      <div className="ats-layout">
        <textarea
          value={atsInput}
          onChange={(event) => setAtsInput(event.target.value)}
          placeholder="Paste internship job description here"
        />
        <div className="ats-result">
          <strong>Result</strong>
          <pre>{atsResult ? JSON.stringify(atsResult.analysis?.analysis || atsResult.analysis, null, 2) : "No ATS run yet."}</pre>
        </div>
      </div>
    </section>
  );
}

function SettingsView({ settingsData, health, daemon }) {
  const rows = [
    ["Gmail user", settingsData?.gmail_user || "Not set"],
    ["Resume path", settingsData?.resume_path || "Not set"],
    ["Job sources", settingsData?.job_sources_path || "Not set"],
    ["Jobs DB", settingsData?.jobs_db_path || "Not set"],
    ["API status", health?.status || "unknown"],
    ["Daemon", daemon?.running ? "running" : "stopped"]
  ];

  return (
    <section className="panel view-panel">
      <div className="panel-heading">
        <div>
          <h2>Settings</h2>
          <p>Runtime configuration and integration status</p>
        </div>
      </div>
      <dl className="settings-list">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function ActionButton({ icon: Icon, label, busy, onClick }) {
  return (
    <button type="button" className="action-button" onClick={onClick} disabled={busy}>
      {busy ? (
        <Loader2 className="spin" size={18} aria-hidden="true" />
      ) : (
        <Icon size={18} aria-hidden="true" />
      )}
      <span>{label}</span>
    </button>
  );
}

export default App;
