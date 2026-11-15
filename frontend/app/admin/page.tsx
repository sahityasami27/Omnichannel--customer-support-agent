"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ShieldAlert,
  CheckCircle2,
  Activity,
  Database,
  Terminal,
  RefreshCw,
  LogOut,
  ChevronDown,
  ChevronRight,
  Clock,
  Zap,
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

interface PendingApproval {
  ticket_id: string;
  customer_id: string;
  ticket_text: string;
  order_id: string;
  amount: number;
}

interface CustomerRow {
  id: string;
  name: string;
  email: string;
  tier: string;
}

interface OrderRow {
  id: string;
  customer_id: string;
  items: string;
  total: number;
  status: string;
  carrier: string;
  shipment_status: string;
}

interface AuditLogEntry {
  ticket_id: string;
  timestamp: string;
  customer_id: string;
  order_id: string;
  amount: number;
  text: string;
  intent: string;
  policy_decision: string;
  approval_status: string;
  is_escalated: boolean;
  escalation_summary?: string;
}

interface NodeTrace {
  node: string;
  start_time: string;
  end_time: string;
  duration_ms: number;
  input_keys: string[];
  output_keys: string[];
}

interface LangGraphTrace {
  ticket_id: string;
  timestamp: string;
  customer_id: string;
  ticket_text: string;
  total_duration_ms: number;
  node_traces: NodeTrace[];
}

function getAuthHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

const NODE_COLORS: Record<string, string> = {
  triage_node: "text-cyan-400 border-cyan-500/30 bg-cyan-500/10",
  policy_node: "text-amber-400 border-amber-500/30 bg-amber-500/10",
  resolution_node: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
  approval_gate_node: "text-purple-400 border-purple-500/30 bg-purple-500/10",
  escalation_node: "text-rose-400 border-rose-500/30 bg-rose-500/10",
};

export default function AdminDashboard() {
  const router = useRouter();
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [customers, setCustomers] = useState<CustomerRow[]>([]);
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [traces, setTraces] = useState<LangGraphTrace[]>([]);
  const [expandedTrace, setExpandedTrace] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  const fetchAdminData = async () => {
    const headers = getAuthHeaders();
    if (!headers.Authorization) {
      setAuthError("No authentication token found. Please sign in first.");
      return;
    }

    try {
      const [appRes, dbRes, tracesRes] = await Promise.all([
        fetch(`${API_BASE}/approvals/pending`, { headers }),
        fetch(`${API_BASE}/db/overview`, { headers }),
        fetch(`${API_BASE}/traces`, { headers }),
      ]);

      if (appRes.status === 401 || dbRes.status === 401) {
        setAuthError("Session expired. Redirecting to login...");
        setTimeout(() => {
          localStorage.removeItem("access_token");
          localStorage.removeItem("session_role");
          router.push("/");
        }, 1500);
        return;
      }

      setAuthError(null);

      if (appRes.ok) setApprovals(await appRes.json());
      if (dbRes.ok) {
        const data = await dbRes.json();
        setCustomers(data.customers || []);
        setOrders(data.orders || []);
        setAuditLogs(data.audit_logs || []);
      }
      if (tracesRes.ok) setTraces(await tracesRes.json());
    } catch (err) {
      console.error("Admin fetch error:", err);
    }
  };

  useEffect(() => {
    fetchAdminData();
    const interval = setInterval(fetchAdminData, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleDecision = async (
    ticketId: string,
    decision: "approved" | "rejected"
  ) => {
    const headers = getAuthHeaders();
    await fetch(`${API_BASE}/approvals/decide`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...headers,
      },
      body: JSON.stringify({ ticket_id: ticketId, decision }),
    });
    fetchAdminData();
  };

  const handleLogout = () => {
    document.cookie = "app_role=; Max-Age=0; path=/";
    localStorage.removeItem("access_token");
    localStorage.removeItem("session_role");
    localStorage.removeItem("session_user_id");
    router.push("/");
  };

  if (authError) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="bg-slate-900 border border-rose-500/30 rounded-2xl p-8 max-w-md text-center space-y-4">
          <ShieldAlert className="w-12 h-12 text-rose-400 mx-auto" />
          <p className="text-rose-300">{authError}</p>
          <button
            onClick={() => router.push("/")}
            className="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-xl text-sm cursor-pointer"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 flex flex-col gap-5">
      {/* Header */}
      <div className="max-w-7xl w-full mx-auto bg-slate-900 border border-slate-800 rounded-2xl px-5 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-6 h-6 text-amber-400" />
          <div>
            <h1 className="font-bold text-base">
              Operations &amp; Guardrail Admin Console
            </h1>
            <p className="text-xs text-slate-400">
              Protected Route (/admin) • LangGraph Telemetry &amp; Refund
              Approvals
            </p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="text-xs bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-xl flex items-center gap-1.5 cursor-pointer"
        >
          <LogOut className="w-3.5 h-3.5" /> Sign Out
        </button>
      </div>

      {/* Stat Cards */}
      <div className="max-w-7xl w-full mx-auto grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase text-slate-400">Customers</p>
            <p className="text-lg font-bold text-emerald-400">
              {customers.length}
            </p>
          </div>
          <CheckCircle2 className="w-6 h-6 text-emerald-500/40" />
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase text-slate-400">Graph Traces</p>
            <p className="text-lg font-bold text-indigo-400">
              {traces.length}
            </p>
          </div>
          <Activity className="w-6 h-6 text-indigo-500/40" />
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase text-slate-400">
              Pending Approvals
            </p>
            <p className="text-lg font-bold text-amber-400">
              {approvals.length}
            </p>
          </div>
          <ShieldAlert className="w-6 h-6 text-amber-500/40" />
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase text-slate-400">
              Total Store Orders
            </p>
            <p className="text-lg font-bold text-slate-200">{orders.length}</p>
          </div>
          <Database className="w-6 h-6 text-slate-500/40" />
        </div>
      </div>

      {/* Main Panels */}
      <div className="max-w-7xl w-full mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6 h-[74vh]">
        {/* Approval Queue */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <h2 className="font-bold text-sm">
              High-Value Refund Queue (&gt;$2,000)
            </h2>
            <button
              onClick={fetchAdminData}
              className="p-1.5 bg-slate-800 rounded-lg cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {approvals.length === 0 && (
              <p className="text-xs text-slate-500 text-center py-8">
                No pending approvals
              </p>
            )}
            {approvals.map((item) => (
              <div
                key={item.ticket_id}
                className="bg-slate-950 border border-amber-500/30 rounded-xl p-4 space-y-2.5"
              >
                <div className="flex justify-between">
                  <span className="text-xs font-mono text-amber-400">
                    {item.order_id} ({item.customer_id})
                  </span>
                  <span className="text-sm font-bold">
                    ${item.amount.toLocaleString()}
                  </span>
                </div>
                <p className="text-xs text-slate-300">
                  &ldquo;{item.ticket_text}&rdquo;
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() =>
                      handleDecision(item.ticket_id, "approved")
                    }
                    className="bg-emerald-600 text-white text-xs py-2 rounded-lg font-medium cursor-pointer"
                  >
                    Approve Refund
                  </button>
                  <button
                    onClick={() =>
                      handleDecision(item.ticket_id, "rejected")
                    }
                    className="bg-rose-600/20 text-rose-300 border border-rose-500/30 text-xs py-2 rounded-lg font-medium cursor-pointer"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* All Store Orders */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-800">
            <h2 className="font-bold text-sm">All Store Orders (SQLite)</h2>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {orders.length === 0 && (
              <p className="text-xs text-slate-500 text-center py-8">
                No orders in the database
              </p>
            )}
            {orders.map((o) => (
              <div
                key={o.id}
                className="bg-slate-950 border border-slate-800 rounded-xl p-3 flex justify-between text-xs"
              >
                <div className="max-w-[65%]">
                  <span className="font-mono text-indigo-400 font-semibold">
                    {o.id}
                  </span>{" "}
                  <span className="text-slate-500">({o.customer_id})</span>
                  <p className="text-slate-300 truncate">{o.items}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold">${o.total.toLocaleString()}</p>
                  <span className="text-[10px] text-slate-400">{o.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* LangGraph Node Traces */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-emerald-400" />
              <h2 className="font-bold text-sm">LangGraph Node Traces</h2>
            </div>
            <button
              onClick={fetchAdminData}
              className="p-1.5 bg-slate-800 rounded-lg cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {traces.length === 0 && (
              <p className="text-xs text-slate-500 text-center py-8">
                No traces yet. Submit a support ticket to generate traces.
              </p>
            )}
            {traces
              .slice()
              .reverse()
              .map((trace) => (
                <div
                  key={trace.ticket_id}
                  className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden"
                >
                  <button
                    onClick={() =>
                      setExpandedTrace(
                        expandedTrace === trace.ticket_id
                          ? null
                          : trace.ticket_id
                      )
                    }
                    className="w-full p-3 flex items-center justify-between text-xs cursor-pointer hover:bg-slate-900/50 transition"
                  >
                    <div className="flex items-center gap-2">
                      {expandedTrace === trace.ticket_id ? (
                        <ChevronDown className="w-3 h-3 text-slate-500" />
                      ) : (
                        <ChevronRight className="w-3 h-3 text-slate-500" />
                      )}
                      <span className="font-mono text-indigo-400">
                        {trace.ticket_id}
                      </span>
                      <span className="text-slate-600">
                        ({trace.customer_id})
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {trace.total_duration_ms}ms
                      </span>
                      <span className="text-emerald-500 flex items-center gap-1">
                        <Zap className="w-3 h-3" />
                        {trace.node_traces.length} nodes
                      </span>
                    </div>
                  </button>

                  {expandedTrace === trace.ticket_id && (
                    <div className="px-3 pb-3 space-y-2">
                      <div className="text-[10px] text-slate-500 font-sans px-1 truncate">
                        &ldquo;{trace.ticket_text}&rdquo;
                      </div>

                      {/* Node flow visualization */}
                      <div className="flex items-center gap-1 px-1 flex-wrap">
                        {trace.node_traces.map((nt, idx) => (
                          <React.Fragment key={idx}>
                            <span
                              className={`text-[9px] px-1.5 py-0.5 rounded border font-mono ${
                                NODE_COLORS[nt.node] ||
                                "text-slate-400 border-slate-700 bg-slate-800"
                              }`}
                            >
                              {nt.node.replace("_node", "")}
                            </span>
                            {idx < trace.node_traces.length - 1 && (
                              <span className="text-slate-600 text-[9px]">
                                →
                              </span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>

                      {/* Per-node detail cards */}
                      {trace.node_traces.map((nt, idx) => (
                        <div
                          key={idx}
                          className={`rounded-lg border p-2 text-[10px] font-mono space-y-0.5 ${
                            NODE_COLORS[nt.node] ||
                            "text-slate-400 border-slate-700 bg-slate-800"
                          }`}
                        >
                          <div className="flex justify-between">
                            <span className="font-bold">{nt.node}</span>
                            <span className="opacity-70">
                              {nt.duration_ms}ms
                            </span>
                          </div>
                          <div className="opacity-60">
                            in: [{nt.input_keys.join(", ")}]
                          </div>
                          <div className="opacity-60">
                            out: [{nt.output_keys.join(", ")}]
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
