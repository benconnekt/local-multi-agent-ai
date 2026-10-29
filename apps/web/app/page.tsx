"use client";

import { useState, type CSSProperties } from "react";
import {
  Activity, ArrowRight, Bell, Bot, ChartCandlestick, ChevronDown,
  CircleAlert, ClipboardCheck, Code2, Command, FolderKanban,
  LayoutDashboard, Menu, Plus, Search, Settings2, Shield, X,
} from "lucide-react";
import { agents, type Agent, type DraftTask, type Workspace } from "@/lib/data";
import { useStudioConnection } from "@/lib/use-studio-connection";
import { useEngineeringTask } from "@/lib/use-engineering-task";
import type { StudioTask } from "@/lib/api";

type View = "overview" | "agents" | "tasks" | "approvals" | "settings";
type Connection = ReturnType<typeof useStudioConnection>;

const navigation: { id: View; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "agents", label: "Agents", icon: Bot },
  { id: "tasks", label: "Tasks", icon: FolderKanban },
  { id: "approvals", label: "Approvals", icon: ClipboardCheck },
  { id: "settings", label: "Settings", icon: Settings2 },
];

const localEngineeringAgents = agents.filter((agent) => agent.workspace === "engineering");
const forexAgents = agents.filter((agent) => agent.workspace === "forex");

function getEngineeringAgents(connection: Connection): Agent[] {
  if (connection.status !== "connected") return localEngineeringAgents;

  return connection.agents.map((agent) => {
    const existing = localEngineeringAgents.find(
      (item) => item.name === agent.name,
    );
    return {
      id: agent.id,
      name: agent.name,
      role: agent.role,
      description: existing?.description ?? "Registered engineering agent",
      workspace: "engineering",
      accent: existing?.accent ?? "#79cbb0",
    };
  });
}

function AgentCard({ agent }: { agent: Agent }) {
  return (
    <article className="agent-card">
      <div
        className="avatar"
        style={{ "--accent": agent.accent } as CSSProperties}
      >
        {agent.name.slice(0, 1)}
      </div>
      <div>
        <div className="agent-heading">
          <strong>{agent.name}</strong>
          <span className="pill neutral">Configured role</span>
        </div>
        <p className="role">{agent.role}</p>
        <p className="muted small">{agent.description}</p>
      </div>
    </article>
  );
}

function ConnectionStatus({ connection }: { connection: Connection }) {
  const label =
    connection.status === "connected"
      ? "Engineering API connected"
      : connection.status === "checking"
        ? "Checking Engineering API"
        : "Engineering API disconnected";

  return (
    <div className="side-bottom">
      <div className="local-status" role="status">
        <span className="status-dot" /> {label}
      </div>
      <p>
        {connection.status === "connected"
          ? `${connection.agents.length} registered engineering agents`
          : connection.status === "checking"
            ? "Connecting to local backend…"
            : connection.error ?? "Agent registry unavailable"}
      </p>
      <p className="small">No autonomous execution or live trading</p>
    </div>
  );
}

type SidebarProps = {
  workspace: Workspace;
  view: View;
  open: boolean;
  draftCount: number;
  connection: Connection;
  onWorkspaceChange: (workspace: Workspace) => void;
  onViewChange: (view: View) => void;
  onClose: () => void;
};

function Sidebar({
  workspace, view, open, draftCount, connection,
  onWorkspaceChange, onViewChange, onClose,
}: SidebarProps) {
  return (
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <div className="brand">
        <div className="brand-icon"><Command size={22} /></div>
        <div><strong>LOCAL AGENT</strong><span>STUDIO</span></div>
        <button className="mobile-close icon-button" aria-label="Close menu" onClick={onClose}>
          <X size={18} />
        </button>
      </div>
      <div className="side-label">WORKSPACES</div>
      <button
        className={`workspace-link ${workspace === "engineering" ? "selected" : ""}`}
        onClick={() => onWorkspaceChange("engineering")}
      >
        <Code2 size={19} /> Engineering <ArrowRight size={15} className="push" />
      </button>
      <button
        className={`workspace-link ${workspace === "forex" ? "selected" : ""}`}
        onClick={() => onWorkspaceChange("forex")}
      >
        <ChartCandlestick size={19} /> Forex Research <ArrowRight size={15} className="push" />
      </button>
      <div className="side-label section-space">NAVIGATION</div>
      <nav aria-label="Workspace navigation">
        {navigation.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={`nav-link ${view === id ? "active" : ""}`}
            onClick={() => onViewChange(id)}
          >
            <Icon size={18} /> {label}
            {id === "tasks" && draftCount > 0 && <span className="count">{draftCount}</span>}
          </button>
        ))}
      </nav>
      <ConnectionStatus connection={connection} />
    </aside>
  );
}

function EngineeringTaskProgress({ task }: { task: StudioTask }) {
  const active = task.status === "queued" || task.status === "running";
  return (
    <section className="panel" aria-label="Engineering task status" aria-live="polite">
      <div className="panel-header">
        <div>
          <h2>Alex · Engineering execution</h2>
          <p className="muted small">Task {task.id}</p>
        </div>
        <span className="tag">{task.status.toUpperCase()}</span>
      </div>
      <p>{task.task}</p>
      <p className="muted small">
        {active ? "Workflow running; agent outputs appear when it finishes." : "Workflow finished."}
      </p>
      {task.selected_agents.length > 0 && (
        <p className="muted small">Selected roles: {task.selected_agents.join(" · ")}</p>
      )}
      {Object.entries(task.outputs).map(([role, output]) => (
        <details key={role} className="task-row">
          <summary><strong>{role}</strong></summary>
          <p style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{output}</p>
        </details>
      ))}
      {task.feedback && <div className="safety-note"><Shield size={20} /><p>{task.feedback}</p></div>}
      {(task.qa_status || task.review_status) && (
        <p className="muted small">QA: {task.qa_status ?? "pending"} · Review: {task.review_status ?? "pending"}</p>
      )}
    </section>
  );
}

function Overview({
  workspace, visibleAgents, allAgentCount, tasks, draft, onDraftChange,
  onSaveDraft, onViewAgents, engineeringTask, submitting, taskError, onSubmitEngineering, engineeringConnected,
}: {
  workspace: Workspace;
  visibleAgents: Agent[];
  allAgentCount: number;
  tasks: DraftTask[];
  draft: string;
  onDraftChange: (value: string) => void;
  onSaveDraft: () => void;
  onViewAgents: () => void;
  engineeringTask: StudioTask | null;
  submitting: boolean;
  taskError: string | null;
  onSubmitEngineering: () => void;
  engineeringConnected: boolean;
}) {
  const forex = workspace === "forex";
  return (
    <>
      <section className="stats" aria-label="Workspace summary">
        <div className="stat"><span>Configured agents</span><strong>{String(allAgentCount).padStart(2, "0")}</strong><small><Bot size={14} /> Role definitions</small></div>
        <div className="stat"><span>Session drafts</span><strong>{String(tasks.length).padStart(2, "0")}</strong><small><FolderKanban size={14} /> Not submitted</small></div>
        <div className="stat"><span>Active executions</span><strong>{!forex && engineeringTask && ["queued", "running"].includes(engineeringTask.status) ? "01" : "00"}</strong><small><Activity size={14} /> {forex ? "Research not connected" : "Current session"}</small></div>
        <div className="stat"><span>Verified approvals</span><strong>—</strong><small><Shield size={14} /> Evidence unavailable</small></div>
      </section>
      <div className="main-grid">
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>{forex ? "New research task" : "Start a new task"}</h2>
              <p className="muted small">{forex ? "Create a paper-research brief for your agents." : "Describe what you want your engineering agents to work on."}</p>
            </div>
            <span className="tag">{forex ? "Draft only" : "Local execution"}</span>
          </div>
          <textarea
            aria-label="Task description"
            value={draft}
            onChange={(event) => onDraftChange(event.target.value)}
            placeholder={forex
              ? "Analyse EUR/USD market structure, define a testable hypothesis, and evaluate risk…"
              : "Ask Alex to review a repository, implement a feature, or investigate an issue…"}
          />
          <div className="composer-footer">
            <span><Shield size={15} /> {forex ? "No broker execution" : "QA approval remains blocked"}</span>
            <button
              className="primary"
              disabled={!draft.trim() || (!forex && (!engineeringConnected || submitting || (engineeringTask?.status === "queued" || engineeringTask?.status === "running")))}
              onClick={forex ? onSaveDraft : onSubmitEngineering}
            >
              <Plus size={16} /> {forex ? "Save draft" : submitting ? "Submitting…" : "Submit to Alex"}
            </button>
          </div>
        </section>
        <section className="panel activity-panel">
          <div className="panel-header">
            <div><h2>Agent activity</h2><p className="muted small">{forex ? "Research execution unavailable" : "Task state from the local API"}</p></div>
            <span className="tag">{forex ? "Not connected" : engineeringTask?.status ?? "Idle"}</span>
          </div>
          <div className="empty-activity">
            <div className="empty-icon"><Activity size={26} /></div>
            <strong>{!forex && engineeringTask ? `Task ${engineeringTask.status}` : "No live activity yet"}</strong>
            <p>{!forex && engineeringTask ? "Polling task status. Per-agent live streaming is not yet connected." : "Agent steps, tool actions and evidence are not streamed yet."}</p>
          </div>
        </section>
      </div>
      {!forex && taskError && <div className="notice" role="alert"><CircleAlert size={17} /> {taskError}</div>}
      {!forex && engineeringTask && <EngineeringTaskProgress task={engineeringTask} />}
      <section className="panel agent-section">
        <div className="panel-header">
          <div>
            <h2>{forex ? "Forex specialist agents" : "Your engineering team"}</h2>
            <p className="muted small">Configured roles · Not live agent health</p>
          </div>
          <button className="text-button" onClick={onViewAgents}>View all <ArrowRight size={16} /></button>
        </div>
        <div className="agent-grid">{visibleAgents.slice(0, 4).map((agent) => <AgentCard key={agent.id} agent={agent} />)}</div>
      </section>
      {forex && (
        <div className="safety-note">
          <Shield size={20} />
          <div>
            <strong>Paper research only</strong>
            <p>Market feeds, backtests and simulated orders are not connected. No broker credentials, real-money orders or trading signals are generated by this preview.</p>
          </div>
        </div>
      )}
    </>
  );
}

function AgentDirectory({ agents: visibleAgents, query, onQueryChange }: {
  agents: Agent[];
  query: string;
  onQueryChange: (value: string) => void;
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div><h2>Agent directory</h2><p className="muted small">Agent role catalogue for this workspace</p></div>
        <div className="search"><Search size={16} />
          <input value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="Search agents" aria-label="Search agents" />
        </div>
      </div>
      <div className="agent-grid">{visibleAgents.map((agent) => <AgentCard key={agent.id} agent={agent} />)}</div>
      {visibleAgents.length === 0 && <p className="muted">No matching agents.</p>}
    </section>
  );
}

function TaskDrafts({ tasks, onNewDraft, onDelete }: {
  tasks: DraftTask[];
  onNewDraft: () => void;
  onDelete: (id: string) => void;
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div><h2>Task drafts</h2><p className="muted small">Stored in browser memory for this session only</p></div>
        <button className="secondary" onClick={onNewDraft}><Plus size={16} /> New draft</button>
      </div>
      {tasks.length > 0 ? (
        <div className="task-list">
          {tasks.map((task) => (
            <article key={task.id} className="task-row">
              <div className="task-icon"><FolderKanban size={18} /></div>
              <div className="task-body">
                <strong>{task.text}</strong>
                <p className="muted small">{task.createdAt} · Draft · Not executed</p>
              </div>
              <button className="icon-button" title="Delete draft" aria-label="Delete draft" onClick={() => onDelete(task.id)}><X size={17} /></button>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state"><FolderKanban size={30} /><h3>No task drafts yet</h3><p>Create one from the workspace overview.</p></div>
      )}
    </section>
  );
}

function Approvals() {
  return (
    <section className="panel">
      <div className="panel-header">
        <div><h2>Approval queue</h2><p className="muted small">Evidence-based human review</p></div>
        <span className="tag">Unavailable</span>
      </div>
      <div className="empty-state">
        <ClipboardCheck size={30} /><h3>Approval service not connected</h3>
        <p>We will not fabricate approvals or enable one-click execution until trusted backend verification is available.</p>
      </div>
    </section>
  );
}

function Settings({ connection, engineeringTask }: { connection: Connection; engineeringTask: StudioTask | null }) {
  return (
    <section className="panel">
      <div className="panel-header"><div><h2>Connection settings</h2><p className="muted small">Frontend integration status</p></div></div>
      <div className="settings-list">
        <div><strong>Engineering API</strong><span>{connection.status}</span></div>
        <div><strong>LangGraph execution</strong><span>{engineeringTask ? engineeringTask.status : "No task this session"}</span></div>
        <div><strong>Agent activity stream</strong><span>Not connected</span></div>
        <div><strong>QA evidence service</strong><span>Not connected</span></div>
        <div><strong>Broker execution</strong><span>Disabled</span></div>
        <div><strong>Trading mode</strong><span>Research / paper only</span></div>
      </div>
    </section>
  );
}

export default function Home() {
  const [workspace, setWorkspace] = useState<Workspace>("engineering");
  const [view, setView] = useState<View>("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [draft, setDraft] = useState("");
  const [tasks, setTasks] = useState<DraftTask[]>([]);
  const [notice, setNotice] = useState("");
  const connection = useStudioConnection();
  const engineering = useEngineeringTask();

  const workspaceAgents = workspace === "engineering"
    ? getEngineeringAgents(connection)
    : forexAgents;
  const search = query.trim().toLowerCase();
  const visibleAgents = workspaceAgents.filter((agent) =>
    `${agent.name} ${agent.role} ${agent.description}`.toLowerCase().includes(search),
  );
  const workspaceTasks = tasks.filter((task) => task.workspace === workspace);
  const forex = workspace === "forex";
  const heading = forex ? "Forex Research Workspace" : "Engineering Workspace";

  function saveDraft() {
    const text = draft.trim();
    if (!text) return;
    setTasks((previous) => [
      {
        id: crypto.randomUUID(),
        workspace,
        text,
        createdAt: new Date().toLocaleString("en-GB"),
        status: "draft",
      },
      ...previous,
    ]);
    setDraft("");
    setNotice("Task saved locally in this session as a draft. No agent was run.");
    setView("tasks");
  }

  async function submitEngineering() {
    if (workspace !== "engineering" || connection.status !== "connected") return;
    const submitted = await engineering.submit(draft);
    if (submitted) {
      setDraft("");
      setView("tasks");
      setNotice("Task submitted to Alex. Results remain subject to the QA gate.");
    }
  }

  function switchWorkspace(next: Workspace) {
    setWorkspace(next);
    setView("overview");
    setQuery("");
    setNotice("");
    setSidebarOpen(false);
  }

  function changeView(next: View) {
    setView(next);
    setSidebarOpen(false);
    setNotice("");
  }

  return (
    <div className="app-shell">
      <Sidebar
        workspace={workspace}
        view={view}
        open={sidebarOpen}
        draftCount={workspaceTasks.length}
        connection={connection}
        onWorkspaceChange={switchWorkspace}
        onViewChange={changeView}
        onClose={() => setSidebarOpen(false)}
      />
      {sidebarOpen && <button className="scrim" aria-label="Close sidebar" onClick={() => setSidebarOpen(false)} />}
      <main className="main">
        <header className="topbar">
          <div className="top-left">
            <button className="icon-button menu-button" aria-label="Open menu" onClick={() => setSidebarOpen(true)}><Menu size={22} /></button>
            <span className="breadcrumb">Workspaces</span><span className="breadcrumb-sep">/</span>
            <strong>{forex ? "Forex Research" : "Engineering"}</strong><ChevronDown size={14} className="muted" />
          </div>
          <div className="top-actions">
            <span className="preview-label">{forex || connection.status !== "connected" ? "DEMO DATA" : "AGENT REGISTRY LIVE"}</span>
            <button className="icon-button" aria-label="Notifications" onClick={() => setNotice("Notifications are not connected yet.")}><Bell size={19} /></button>
            <div className="user-avatar">LA</div>
          </div>
        </header>
        <div className="content">
          <div className="page-intro">
            <div>
              <div className="eyebrow">{forex ? "RESEARCH & SIMULATION" : "MULTI-AGENT DEVELOPMENT"}</div>
              <h1>{view === "overview" ? heading : navigation.find((item) => item.id === view)?.label}</h1>
              <p className="muted">
                {view === "overview"
                  ? forex
                    ? "Explore strategies and risk controls in a paper-only environment."
                    : "Coordinate your agents, track work and review execution evidence."
                  : `Manage ${view} within the ${forex ? "Forex" : "Engineering"} workspace.`}
              </p>
            </div>
            <span className="environment"><span className="status-dot" /> Local preview</span>
          </div>
          {notice && (
            <div className="notice" role="status">
              <CircleAlert size={17} /> {notice}
              <button aria-label="Dismiss message" onClick={() => setNotice("")}><X size={16} /></button>
            </div>
          )}
          {view === "overview" && (
            <Overview
              workspace={workspace}
              visibleAgents={workspaceAgents}
              allAgentCount={workspaceAgents.length}
              tasks={workspaceTasks}
              draft={draft}
              onDraftChange={setDraft}
              onSaveDraft={saveDraft}
              onViewAgents={() => changeView("agents")}
              engineeringTask={engineering.task}
              submitting={engineering.submitting}
              taskError={engineering.error}
              onSubmitEngineering={() => { void submitEngineering(); }}
              engineeringConnected={connection.status === "connected"}
            />
          )}
          {view === "agents" && <AgentDirectory agents={visibleAgents} query={query} onQueryChange={setQuery} />}
          {view === "tasks" && (
            <>
              {!forex && engineering.error && <div className="notice" role="alert"><CircleAlert size={17} /> {engineering.error}</div>}
              {!forex && engineering.task && <EngineeringTaskProgress task={engineering.task} />}
              <TaskDrafts
                tasks={workspaceTasks}
                onNewDraft={() => changeView("overview")}
                onDelete={(id) => setTasks((previous) => previous.filter((task) => task.id !== id))}
              />
            </>
          )}
          {view === "approvals" && <Approvals />}
          {view === "settings" && <Settings connection={connection} engineeringTask={engineering.task} />}
          <footer className="footer">
            <span>Local Agent Studio · Frontend foundation</span>
            <span>Engineering: local API · Forex: draft-only · QA fail-closed</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
