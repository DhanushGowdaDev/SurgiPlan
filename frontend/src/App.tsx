
import { useEffect, useState, type ReactNode } from "react";
import {
  Activity,
  AlertCircle,
  Bed,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  LayoutDashboard,
  MessageSquare,
  RefreshCw,
  Settings,
  Stethoscope,
  Users,
} from "lucide-react";
import "./App.css";

const API = "https://surgiplan.onrender.com";
type Surgery = {
  id: string;
  procedure: string;
  specialty: string;
  priority: string;
  duration: number;
  surgeon: string;
  anesthetist: string;
};

type Room = {
  id: string;
  specialties: string[];
};

type StaffMember = {
  id: string;
  role: string;
};

type Equipment = {
  id: string;
  equipment_type: string;
};

type RecoveryBed = {
  id: string;
  available: boolean;
};

type Resources = {
  staff: StaffMember[];
  equipment: Equipment[];
  recovery_beds: RecoveryBed[];
};

type ScheduleItem = {
  surgery_id: string;
  procedure: string;
  priority: string;
  room: string;
  start: number;
  end: number;
};

type ScheduleResult = {
  run_id?: string;
  status?: string;
  schedule: ScheduleItem[];
  unscheduled_surgeries: unknown[];
};

type ChatMessage = {
  role: "You" | "Copilot";
  text: string;
};

const navItems = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Surgeries", icon: ClipboardList },
  { label: "Operating Rooms", icon: Bed },
  { label: "Resources", icon: Users },
  { label: "Optimized Schedule", icon: CalendarDays },
  { label: "Copilot", icon: MessageSquare },
];

function App() {
  const [page, setPage] = useState("Overview");
  const [surgeries, setSurgeries] = useState<Surgery[]>([]);
  const [rooms, setRooms] = useState<Room[]>([]);
  const [resources, setResources] = useState<Resources | null>(null);
  const [schedule, setSchedule] = useState<ScheduleResult | null>(null);

  const [loading, setLoading] = useState(true);
  const [optimizing, setOptimizing] = useState(false);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [apiOnline, setApiOnline] = useState(false);
  const [error, setError] = useState("");

  const [chatInput, setChatInput] = useState("");
  const [chat, setChat] = useState<ChatMessage[]>([]);

  async function loadData() {
    setLoading(true);
    setError("");

    try {
      const [healthRes, surgeryRes, roomRes, resourceRes] =
        await Promise.all([
          fetch(`${API}/api/health`),
          fetch(`${API}/api/surgeries`),
          fetch(`${API}/api/operating-rooms`),
          fetch(`${API}/api/resources`),
        ]);

      if (
        !healthRes.ok ||
        !surgeryRes.ok ||
        !roomRes.ok ||
        !resourceRes.ok
      ) {
        throw new Error("A backend endpoint returned an error.");
      }

      const [surgeryData, roomData, resourceData] = await Promise.all([
        surgeryRes.json(),
        roomRes.json(),
        resourceRes.json(),
      ]);

      setSurgeries(surgeryData);
      setRooms(roomData);
      setResources(resourceData);
      setApiOnline(true);
    } catch {
      setApiOnline(false);
      setError(
        "Cannot connect to the backend. Make sure FastAPI is running at http://127.0.0.1:8000."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  async function optimize() {
    setOptimizing(true);
    setError("");

    try {
      const response = await fetch(`${API}/api/schedule/optimize`, {
        method: "POST",
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail || "Optimization request failed.");
      }

      const result: ScheduleResult = await response.json();

      if (
        !Array.isArray(result.schedule) ||
        !Array.isArray(result.unscheduled_surgeries)
      ) {
        throw new Error("The optimizer returned an unexpected response.");
      }

      setSchedule(result);
      setPage("Optimized Schedule");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Optimization failed. Check the backend terminal."
      );
    } finally {
      setOptimizing(false);
    }
  }

  async function sendMessage(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const message = chatInput.trim();
    if (!message || sendingMessage) return;

    setChat((previous) => [...previous, { role: "You", text: message }]);
    setChatInput("");
    setSendingMessage(true);

    try {
      const response = await fetch(`${API}/api/copilot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Copilot request failed.");
      }

      setChat((previous) => [
        ...previous,
        {
          role: "Copilot",
          text: data.reply || "Copilot returned an empty response.",
        },
      ]);
    } catch (err) {
      setChat((previous) => [
        ...previous,
        {
          role: "Copilot",
          text:
            err instanceof Error
              ? err.message
              : "Unable to reach Copilot. Check the backend.",
        },
      ]);
    } finally {
      setSendingMessage(false);
    }
  }

  const scheduledCount = schedule?.schedule.length ?? 0;
  const unscheduledCount = schedule?.unscheduled_surgeries.length ?? 0;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Activity size={23} />
          </div>
          <div>
            <strong>SurgiPlan</strong>
            <span>THEATRE MANAGEMENT</span>
          </div>
        </div>

        <div className="nav-heading">WORKSPACE</div>

        <nav className="navigation">
          {navItems.map(({ label, icon: Icon }) => (
            <button
              key={label}
              className={`nav-item ${page === label ? "active" : ""}`}
              onClick={() => setPage(label)}
            >
              <Icon size={18} strokeWidth={1.8} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="facility-label">FACILITY</div>
          <div className="facility-name">General Hospital</div>
          <div className="facility-subtitle">Operations department</div>

          <button
            className={`nav-item settings-item ${
              page === "Settings" ? "active" : ""
            }`}
            onClick={() => setPage("Settings")}
          >
            <Settings size={18} />
            <span>Settings</span>
          </button>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">
            Operations <span>/</span> {page}
          </div>

          <div className="topbar-right">
            <span
              className={`connection ${
                apiOnline ? "online" : "offline"
              }`}
            >
              <span className="status-dot" />
              {apiOnline ? "Backend connected" : "Backend disconnected"}
            </span>

            <button
              className="icon-button"
              title="Refresh data"
              aria-label="Refresh data"
              onClick={() => void loadData()}
              disabled={loading}
            >
              <RefreshCw size={17} />
            </button>

            <div className="avatar" title="Operations">OP</div>
          </div>
        </header>

        <div className="page-content">
          {error && (
            <div className="error-banner">
              <AlertCircle size={18} />
              <span>{error}</span>
              <button
                className="dismiss-button"
                onClick={() => setError("")}
                aria-label="Dismiss error"
              >
                ×
              </button>
            </div>
          )}

          {page === "Overview" && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">HOSPITAL OPERATIONS</div>
                  <h1>Overview</h1>
                  <p className="subtitle">
                    Operating theatre activity and resource status.
                  </p>
                </div>

                <button
                  className="primary-button"
                  onClick={() => void optimize()}
                  disabled={optimizing || loading}
                >
                  <Activity size={16} />
                  {optimizing ? "Optimizing..." : "Optimize schedule"}
                </button>
              </div>

              <div className="metric-grid">
                <Metric
                  title="Total surgeries"
                  value={loading ? "—" : surgeries.length}
                  note="Cases in the current queue"
                  icon={<ClipboardList size={19} />}
                />
                <Metric
                  title="Operating rooms"
                  value={loading ? "—" : rooms.length}
                  note="Registered theatre rooms"
                  icon={<Bed size={19} />}
                />
                <Metric
                  title="Staff members"
                  value={loading ? "—" : resources?.staff.length ?? "—"}
                  note="Across listed roles"
                  icon={<Users size={19} />}
                />
                <Metric
                  title="Recovery beds"
                  value={
                    loading ? "—" : resources?.recovery_beds.length ?? "—"
                  }
                  note="Registered bed records"
                  icon={<Activity size={19} />}
                />
              </div>

              <div className="section-grid">
                <section className="panel">
                  <div className="panel-header">
                    <div>
                      <h2>Priority cases</h2>
                      <p>Cases requiring closer operational attention</p>
                    </div>
                    <button
                      className="text-button"
                      onClick={() => setPage("Surgeries")}
                    >
                      View all
                    </button>
                  </div>

                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>PROCEDURE</th>
                          <th>SURGEON</th>
                          <th>PRIORITY</th>
                          <th>DURATION</th>
                        </tr>
                      </thead>
                      <tbody>
                        {surgeries
                          .filter((surgery) =>
                            ["Emergency", "Critical", "High"].includes(
                              surgery.priority
                            )
                          )
                          .slice(0, 7)
                          .map((surgery) => (
                            <tr key={surgery.id}>
                              <td>
                                <strong>{surgery.procedure}</strong>
                                <small>
                                  {surgery.id} · {surgery.specialty}
                                </small>
                              </td>
                              <td>{surgery.surgeon}</td>
                              <td>
                                <Priority value={surgery.priority} />
                              </td>
                              <td>{surgery.duration} min</td>
                            </tr>
                          ))}

                        {!loading && surgeries.length === 0 && (
                          <tr>
                            <td colSpan={4} className="empty-cell">
                              No surgery records found.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section className="panel">
                  <div className="panel-header">
                    <div>
                      <h2>System status</h2>
                      <p>Service and data availability</p>
                    </div>
                  </div>

                  <div className="status-list">
                    <StatusRow label="Scheduling API" ok={apiOnline} />
                    <StatusRow
                      label="Surgery records"
                      ok={surgeries.length > 0}
                    />
                    <StatusRow
                      label="Operating rooms"
                      ok={rooms.length > 0}
                    />
                    <StatusRow label="Resource records" ok={!!resources} />
                  </div>

                  <div className="resource-summary">
                    <h3>Resource inventory</h3>
                    <div>
                      <span>Equipment records</span>
                      <strong>{resources?.equipment.length ?? "—"}</strong>
                    </div>
                    <div>
                      <span>Recovery bed records</span>
                      <strong>{resources?.recovery_beds.length ?? "—"}</strong>
                    </div>
                  </div>
                </section>
              </div>

              <section className="panel recent-panel">
                <div className="panel-header">
                  <div>
                    <h2>Recent surgery cases</h2>
                    <p>Cases loaded from the scheduling database</p>
                  </div>
                  <button
                    className="text-button"
                    onClick={() => setPage("Surgeries")}
                  >
                    Open surgery list →
                  </button>
                </div>

                <SurgeryTable
                  surgeries={surgeries.slice(0, 5)}
                  loading={loading}
                />
              </section>
            </>
          )}

          {page === "Surgeries" && (
            <>
              <PageHeading
                title="Surgeries"
                description="Review procedures, assigned teams and priority levels."
              />
              <section className="panel">
                <SurgeryTable surgeries={surgeries} loading={loading} />
              </section>
            </>
          )}

          {page === "Operating Rooms" && (
            <>
              <PageHeading
                title="Operating rooms"
                description="Registered rooms and supported surgical specialties."
              />

              <section className="panel">
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>ROOM ID</th>
                        <th>SUPPORTED SPECIALTIES</th>
                        <th>STATUS</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rooms.map((room) => (
                        <tr key={room.id}>
                          <td><strong>{room.id}</strong></td>
                          <td>
                            {room.specialties?.join(", ") || "Not specified"}
                          </td>
                          <td>
                            <span className="plain-status">
                              <span className="status-dot green" />
                              Registered
                            </span>
                          </td>
                        </tr>
                      ))}

                      {!loading && rooms.length === 0 && (
                        <tr>
                          <td colSpan={3} className="empty-cell">
                            No operating rooms found.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}

          {page === "Resources" && (
            <>
              <PageHeading
                title="Resources"
                description="Staff, equipment and recovery bed inventory."
              />

              <div className="metric-grid">
                <Metric
                  title="Staff members"
                  value={resources?.staff.length ?? "—"}
                  note="Registered personnel"
                  icon={<Users size={19} />}
                />
                <Metric
                  title="Equipment records"
                  value={resources?.equipment.length ?? "—"}
                  note="Registered equipment"
                  icon={<Stethoscope size={19} />}
                />
                <Metric
                  title="Recovery beds"
                  value={resources?.recovery_beds.length ?? "—"}
                  note="Registered bed records"
                  icon={<Bed size={19} />}
                />
              </div>

              <section className="panel">
                <div className="panel-header">
                  <div>
                    <h2>Equipment inventory</h2>
                    <p>Equipment registered in the database</p>
                  </div>
                </div>

                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr><th>EQUIPMENT ID</th><th>TYPE</th></tr>
                    </thead>
                    <tbody>
                      {resources?.equipment.map((item) => (
                        <tr key={item.id}>
                          <td>{item.id}</td>
                          <td>{item.equipment_type}</td>
                        </tr>
                      ))}
                      {!loading && resources?.equipment.length === 0 && (
                        <tr>
                          <td colSpan={2} className="empty-cell">
                            No equipment records found.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>

              <section className="panel section-gap">
                <div className="panel-header">
                  <div>
                    <h2>Staff directory</h2>
                    <p>Registered team members and roles</p>
                  </div>
                </div>

                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr><th>STAFF ID</th><th>ROLE</th></tr>
                    </thead>
                    <tbody>
                      {resources?.staff.map((member) => (
                        <tr key={member.id}>
                          <td>{member.id}</td>
                          <td>{member.role}</td>
                        </tr>
                      ))}
                      {!loading && resources?.staff.length === 0 && (
                        <tr>
                          <td colSpan={2} className="empty-cell">
                            No staff records found.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}

          {page === "Optimized Schedule" && (
            <>
              <div className="page-heading">
                <div>
                  <div className="eyebrow">OPERATIONS PLANNING</div>
                  <h1>Optimized schedule</h1>
                  <p className="subtitle">
                    Room assignments returned by the constraint optimizer.
                  </p>
                </div>

                <button
                  className="primary-button"
                  onClick={() => void optimize()}
                  disabled={optimizing}
                >
                  <Activity size={16} />
                  {optimizing ? "Optimizing..." : "Run optimizer"}
                </button>
              </div>

              {schedule ? (
                <>
                  <div className="metric-grid">
                    <Metric
                      title="Scheduled cases"
                      value={scheduledCount}
                      note="Returned by optimizer"
                      icon={<CheckCircle2 size={19} />}
                    />
                    <Metric
                      title="Unscheduled cases"
                      value={unscheduledCount}
                      note="Require review"
                      icon={<AlertCircle size={19} />}
                    />
                    <Metric
                      title="Solver status"
                      value={schedule.status ?? "Unknown"}
                      note="Optimization result"
                      icon={<Activity size={19} />}
                    />
                    <Metric
                      title="Operating rooms"
                      value={rooms.length}
                      note="Registered rooms"
                      icon={<Bed size={19} />}
                    />
                  </div>

                  <section className="panel">
                    <div className="panel-header">
                      <div>
                        <h2>Room assignments</h2>
                        <p>
                          Times are elapsed hours and minutes from the start of
                          the scheduling horizon.
                        </p>
                      </div>
                    </div>

                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>START</th>
                            <th>END</th>
                            <th>ROOM</th>
                            <th>SURGERY</th>
                            <th>PRIORITY</th>
                            <th>DURATION</th>
                          </tr>
                        </thead>
                        <tbody>
                          {[...schedule.schedule]
                            .sort((a, b) => a.start - b.start)
                            .map((item, index) => (
                              <tr key={`${item.surgery_id}-${index}`}>
                                <td>{formatElapsedTime(item.start)}</td>
                                <td>{formatElapsedTime(item.end)}</td>
                                <td><strong>{item.room}</strong></td>
                                <td>
                                  <strong>{item.procedure}</strong>
                                  <small>{item.surgery_id}</small>
                                </td>
                                <td><Priority value={item.priority} /></td>
                                <td>{item.end - item.start} min</td>
                              </tr>
                            ))}

                          {schedule.schedule.length === 0 && (
                            <tr>
                              <td colSpan={6} className="empty-cell">
                                No cases were scheduled. Check the solver
                                status and unscheduled cases.
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </section>

                  <section className="panel">
                    <div className="panel-header">
                      <div>
                        <h2>Unscheduled cases</h2>
                        <p>
                          Cases the optimizer did not assign to a room.
                        </p>
                      </div>
                    </div>
                    {unscheduledCount > 0 ? (
                      <ul className="unscheduled-list">
                        {schedule.unscheduled_surgeries.map((item, index) => (
                          <li key={index}>
                            {typeof item === "string"
                              ? item
                              : JSON.stringify(item)}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="success-note">
                        No unscheduled cases were returned by the optimizer.
                      </p>
                    )}
                  </section>

                  <p className="footnote">
                    Run ID: {schedule.run_id ?? "Not provided"}. This prototype
                    supports operational planning only and is not a clinical
                    decision-making tool.
                  </p>
                </>
              ) : (
                <section className="panel empty-state">
                  <CalendarDays size={32} />
                  <h2>No optimization run loaded</h2>
                  <p>
                    Run the optimizer to view its room assignments and
                    unscheduled cases.
                  </p>
                  <button
                    className="primary-button"
                    onClick={() => void optimize()}
                    disabled={optimizing}
                  >
                    {optimizing ? "Optimizing..." : "Optimize schedule"}
                  </button>
                </section>
              )}
            </>
          )}

          {page === "Copilot" && (
            <>
              <PageHeading
                title="SurgiPlan Copilot"
                description="Ask about scheduling concepts and operational planning."
              />

              <section className="panel copilot-panel">
                <div className="copilot-note">
                  <AlertCircle size={17} />
                  <span>
                    AI-generated explanations may not reflect the live schedule
                    unless current schedule data is explicitly supplied.
                  </span>
                </div>

                <div className="chat-messages">
                  {chat.length === 0 && (
                    <div className="empty-state">
                      <MessageSquare size={28} />
                      <h2>How can I help?</h2>
                      <p>
                        Ask about operating-room scheduling, priorities or
                        resource planning.
                      </p>
                    </div>
                  )}

                  {chat.map((message, index) => (
                    <div
                      key={index}
                      className={`chat-message ${
                        message.role === "You" ? "user-message" : ""
                      }`}
                    >
                      <strong>{message.role}</strong>
                      <p>{message.text}</p>
                    </div>
                  ))}

                  {sendingMessage && (
                    <div className="chat-message">
                      <strong>Copilot</strong>
                      <p>Generating response...</p>
                    </div>
                  )}
                </div>

                <form className="chat-form" onSubmit={sendMessage}>
                  <input
                    value={chatInput}
                    onChange={(event) => setChatInput(event.target.value)}
                    placeholder="Ask about operating-room scheduling..."
                    aria-label="Message Copilot"
                  />
                  <button
                    className="primary-button"
                    type="submit"
                    disabled={!chatInput.trim() || sendingMessage}
                  >
                    {sendingMessage ? "Sending..." : "Send"}
                  </button>
                </form>
              </section>
            </>
          )}

          {page === "Settings" && (
            <>
              <PageHeading
                title="Settings"
                description="Application and service information."
              />

              <section className="panel">
                <div className="status-list">
                  <StatusRow label="Backend API" ok={apiOnline} />
                  <StatusRow
                    label="Surgery data"
                    ok={apiOnline && surgeries.length > 0}
                  />
                  <StatusRow
                    label="Operating room data"
                    ok={apiOnline && rooms.length > 0}
                  />
                </div>
                <p className="footnote settings-footnote">
                  API base URL: {API}. Configure environment-specific URLs
                  before deployment.
                </p>
              </section>
            </>
          )}
        </div>

        <footer className="footer">
          <span>SurgiPlan · Operational scheduling prototype</span>
          <span>Not for clinical decision-making</span>
        </footer>
      </main>
    </div>
  );
}

function Metric({
  title,
  value,
  note,
  icon,
}: {
  title: string;
  value: string | number;
  note: string;
  icon: ReactNode;
}) {
  return (
    <section className="metric-card">
      <div className="metric-top">
        <span>{title}</span>
        <span className="metric-icon">{icon}</span>
      </div>
      <div className="metric-value">{value}</div>
      <div className="metric-note">{note}</div>
    </section>
  );
}

function PageHeading({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">HOSPITAL OPERATIONS</div>
        <h1>{title}</h1>
        <p className="subtitle">{description}</p>
      </div>
    </div>
  );
}

function Priority({ value }: { value: string }) {
  const className = value.toLowerCase().replace(/\s+/g, "-");

  return (
    <span className={`priority priority-${className}`}>
      {value}
    </span>
  );
}

function StatusRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="status-row">
      <span>{label}</span>
      <span className={`service-state ${ok ? "is-online" : "is-offline"}`}>
        <span className={`status-dot ${ok ? "green" : "red"}`} />
        {ok ? "Available" : "Unavailable"}
      </span>
    </div>
  );
}

function SurgeryTable({
  surgeries,
  loading,
}: {
  surgeries: Surgery[];
  loading: boolean;
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>CASE</th>
            <th>SPECIALTY</th>
            <th>SURGEON</th>
            <th>PRIORITY</th>
            <th>DURATION</th>
          </tr>
        </thead>
        <tbody>
          {surgeries.map((surgery) => (
            <tr key={surgery.id}>
              <td>
                <strong>{surgery.procedure}</strong>
                <small>{surgery.id}</small>
              </td>
              <td>{surgery.specialty}</td>
              <td>{surgery.surgeon}</td>
              <td><Priority value={surgery.priority} /></td>
              <td>{surgery.duration} min</td>
            </tr>
          ))}

          {loading && (
            <tr>
              <td colSpan={5} className="empty-cell">
                Loading surgery records...
              </td>
            </tr>
          )}

          {!loading && surgeries.length === 0 && (
            <tr>
              <td colSpan={5} className="empty-cell">
                No records available.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function formatElapsedTime(minutes: number) {
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;

  return `+${String(hours).padStart(2, "0")}:${String(
    remainingMinutes
  ).padStart(2, "0")}`;
}

export default App;
