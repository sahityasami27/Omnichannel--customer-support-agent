"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Send,
  Mic,
  Square,
  Volume2,
  Package,
  CreditCard,
  LogOut,
  Lock,
  Mail,
  Clock,
  CheckCircle2,
  AlertCircle,
  MessageSquare,
  Headset,
  UserCircle,
  ChevronRight,
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

interface Message {
  id: string;
  sender: "user" | "agent";
  text: string;
  audioBase64?: string;
}

interface CustomerOrder {
  id: string;
  items: string;
  total: number;
  status: string;
  placed_at: string;
  carrier: string;
  shipment_status: string;
}

interface AccountData {
  profile: {
    id: string;
    name: string;
    email: string;
    tier: string;
  };
  payment_summary: {
    total_billed: number;
    total_refunded: number;
    pending_refund_amount: number;
    net_charged: number;
    payment_method: string;
  };
  orders: CustomerOrder[];
}

export default function CustomerStorefront() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);

  const [account, setAccount] = useState<AccountData | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const savedToken = localStorage.getItem("access_token");
    const savedRole = localStorage.getItem("session_role");
    if (savedToken && savedRole === "admin") {
      router.push("/admin");
    } else if (savedToken) {
      setToken(savedToken);
    }
  }, [router]);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setAuthLoading(true);

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      if (!res.ok) {
        setAuthError(data.detail || "Invalid email or password.");
        return;
      }

      document.cookie = `app_role=${data.user.role}; path=/; SameSite=Strict`;
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("session_role", data.user.role);

      if (data.user.role === "admin") {
        router.push("/admin");
      } else {
        setToken(data.access_token);
      }
    } catch {
      setAuthError("Could not connect to authentication server.");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    document.cookie = "app_role=; Max-Age=0; path=/";
    localStorage.removeItem("access_token");
    localStorage.removeItem("session_role");
    setToken(null);
    setAccount(null);
    setMessages([]);
    setEmail("");
    setPassword("");
  };

  const fetchAccount = async (bearerToken: string) => {
    try {
      const res = await fetch(`${API_BASE}/customer/account`, {
        headers: { Authorization: `Bearer ${bearerToken}` },
      });
      if (res.status === 401) {
        handleLogout();
        return;
      }
      if (res.ok) {
        const data: AccountData = await res.json();
        setAccount(data);
        
        setMessages((prev) => {
          if (prev.length === 0) {
            return [
              {
                id: "welcome",
                sender: "agent",
                text: `Hi ${data.profile.name.split(" ")[0]}! I'm your virtual support assistant. I can help you track shipments, view your payment summary, or process returns for your orders. How can I help today?`,
              },
            ];
          }
          return prev;
        });
      }
    } catch (err) {
      console.error("Failed to load account:", err);
    }
  };

  useEffect(() => {
    if (!token) return;
    fetchAccount(token);
    const interval = setInterval(() => fetchAccount(token), 4000);
    return () => clearInterval(interval);
  }, [token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendTextTicket = async (customText?: string) => {
    if (!token) return;
    const textToSend = customText ?? input;
    if (!textToSend.trim()) return;

    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), sender: "user", text: textToSend },
    ]);
    if (!customText) setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat/support`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ text: textToSend }),
      });
      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "agent",
          text: data.final_reply || "Your request has been processed.",
        },
      ]);
      fetchAccount(token);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          sender: "agent",
          text: "Unable to reach support service right now.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        await sendVoiceTicket(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch {
      alert("Microphone permission is required for voice support.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendVoiceTicket = async (audioBlob: Blob) => {
    if (!token || !account) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("audio", audioBlob, "voice.wav");
    formData.append("customer_id", account.profile.id);

    try {
      const res = await fetch(`${API_BASE}/voice/support`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), sender: "user", text: `🎤 "${data.transcript}"` },
        {
          id: (Date.now() + 1).toString(),
          sender: "agent",
          text: data.spoken_reply,
          audioBase64: data.audio_base64,
        },
      ]);
      fetchAccount(token);

      if (data.audio_base64) {
        const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`);
        audio.play();
      }
    } finally {
      setLoading(false);
    }
  };

  const confirmPickup = async (orderId: string) => {
    if (!token) return;
    await fetch(`${API_BASE}/orders/${orderId}/confirm-pickup`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    fetchAccount(token);
  };

  // ==================== CLEAN SAAS LOGIN SCREEN ====================
  if (!token) {
    return (
      <div className="min-h-screen bg-gray-50 text-gray-900 flex items-center justify-center p-6 font-sans">
        <div className="max-w-md w-full bg-white border border-gray-200 rounded-2xl p-8 space-y-6 shadow-xl">
          <div className="flex flex-col items-center text-center space-y-3">
            <div className="p-3 bg-blue-50 text-blue-600 rounded-full">
              <Headset className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-gray-900">Support Portal</h1>
              <p className="text-sm text-gray-500 mt-1">
                Sign in to manage your orders and get automated help
              </p>
            </div>
          </div>

          {authError && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{authError}</span>
            </div>
          )}

          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-gray-400 absolute left-3.5 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-gray-400 absolute left-3.5 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-white border border-gray-300 rounded-xl pl-10 pr-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={authLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold text-sm py-2.5 rounded-xl transition-all shadow-sm cursor-pointer"
            >
              {authLoading ? "Authenticating..." : "Sign In"}
            </button>
          </form>
          
          <div className="pt-4 border-t border-gray-100">
            <p className="text-xs text-center text-gray-500">
              Test accounts: elena.r@designstudio.co, alice.j@verizon.net (password: password123)
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ==================== AUTHENTICATED CHATBOT & PORTAL ====================
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-4 md:p-8 flex flex-col gap-6 font-sans">
      {/* Clean Navbar */}
      <div className="max-w-6xl w-full mx-auto bg-white border border-gray-200 rounded-2xl px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
            <UserCircle className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-gray-900">My Account</h1>
            <p className="text-sm text-gray-500">
              {account?.profile.name} • {account?.profile.email}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-xs font-semibold px-3 py-1 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
            {account?.profile.tier} Tier
          </span>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-500 hover:text-gray-900 flex items-center gap-1.5 transition cursor-pointer font-medium"
          >
            Sign Out <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="max-w-6xl w-full mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6 h-[80vh]">
        
        {/* Left 5 Columns: Orders & Summary (Clean Cards) */}
        <div className="lg:col-span-5 flex flex-col gap-6 overflow-hidden">
          
          {/* Payment Summary */}
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-gray-900 flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-gray-400" /> Payment Summary
              </h2>
              <span className="text-sm text-gray-500 bg-gray-50 px-2.5 py-1 rounded-md border border-gray-100">
                {account?.payment_summary.payment_method}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="bg-gray-50 rounded-xl p-3 border border-gray-100">
                <p className="text-xs text-gray-500 font-medium">Billed</p>
                <p className="text-base font-bold text-gray-900 mt-0.5">
                  ${account?.payment_summary.total_billed.toLocaleString() ?? "0.00"}
                </p>
              </div>
              <div className="bg-green-50/50 rounded-xl p-3 border border-green-100">
                <p className="text-xs text-green-600 font-medium">Refunded</p>
                <p className="text-base font-bold text-green-700 mt-0.5">
                  ${account?.payment_summary.total_refunded.toLocaleString() ?? "0.00"}
                </p>
              </div>
              <div className="bg-blue-50/50 rounded-xl p-3 border border-blue-100">
                <p className="text-xs text-blue-600 font-medium">Net Charged</p>
                <p className="text-base font-bold text-blue-700 mt-0.5">
                  ${account?.payment_summary.net_charged.toLocaleString() ?? "0.00"}
                </p>
              </div>
            </div>

            {(account?.payment_summary.pending_refund_amount ?? 0) > 0 && (
              <div className="mt-4 bg-orange-50 border border-orange-200 rounded-xl px-4 py-3 flex items-center justify-between text-sm text-orange-800">
                <span className="flex items-center gap-2 font-medium">
                  <Clock className="w-4 h-4" /> Refund Under Review
                </span>
                <span className="font-bold">
                  ${account?.payment_summary.pending_refund_amount.toLocaleString()}
                </span>
              </div>
            )}
          </div>

          {/* Order History */}
          <div className="flex-1 bg-white border border-gray-200 rounded-2xl flex flex-col overflow-hidden shadow-sm">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
              <h2 className="font-bold text-gray-900 flex items-center gap-2">
                <Package className="w-5 h-5 text-gray-400" /> Recent Orders
              </h2>
              <span className="text-sm font-medium text-gray-500 bg-white px-2 py-0.5 rounded-full border border-gray-200 shadow-sm">
                {account?.orders.length ?? 0}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {account?.orders.map((ord) => (
                <div key={ord.id} className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <span className="font-bold text-gray-900 block">Order #{ord.id}</span>
                      <span className="text-xs text-gray-500">{ord.placed_at}</span>
                    </div>
                    <span
                      className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                        ord.status === "Refunded"
                          ? "bg-green-100 text-green-700"
                          : ord.status === "Delayed"
                          ? "bg-red-100 text-red-700"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {ord.status}
                    </span>
                  </div>

                  <p className="text-sm text-gray-600 mb-3">{ord.items}</p>

                  <div className="flex flex-wrap gap-2 pt-3 border-t border-gray-100">
                    <button
                      onClick={() => sendTextTicket(`Where is my order ${ord.id}?`)}
                      className="flex-1 text-xs font-semibold bg-gray-50 hover:bg-gray-100 text-gray-700 py-2 px-3 rounded-lg border border-gray-200 transition cursor-pointer"
                    >
                      Track
                    </button>

                    {ord.status === "Delivered" && (
                      <button
                        onClick={() => sendTextTicket(`I want to return my order ${ord.id}.`)}
                        className="flex-1 text-xs font-semibold bg-white hover:bg-gray-50 text-gray-700 py-2 px-3 rounded-lg border border-gray-200 transition cursor-pointer"
                      >
                        Return
                      </button>
                    )}

                    {ord.status === "Return Initiated" && (
                      <button
                        onClick={() => confirmPickup(ord.id)}
                        className="flex-1 text-xs font-semibold bg-blue-50 hover:bg-blue-100 text-blue-700 py-2 px-3 rounded-lg border border-blue-200 transition cursor-pointer"
                      >
                        Confirm Pickup
                      </button>
                    )}

                    {ord.status !== "Refunded" ? (
                      <button
                        onClick={() => sendTextTicket(`I would like a refund for my order ${ord.id}.`)}
                        className="flex-1 text-xs font-semibold bg-white hover:bg-gray-50 text-gray-700 py-2 px-3 rounded-lg border border-gray-200 transition cursor-pointer"
                      >
                        Refund
                      </button>
                    ) : (
                      <span className="flex-1 text-xs font-medium text-green-600 flex items-center justify-center gap-1.5 py-2">
                        <CheckCircle2 className="w-4 h-4" /> Processed
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 7 Columns: Modern Chatbot Widget */}
        <div className="lg:col-span-7 bg-white border border-gray-200 rounded-2xl flex flex-col overflow-hidden shadow-xl">
          
          {/* Chatbot Header */}
          <div className="p-4 border-b border-gray-100 flex items-center gap-3 bg-white">
            <div className="relative">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center shadow-sm">
                <Headset className="w-5 h-5 text-white" />
              </div>
              <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
            </div>
            <div>
              <h2 className="font-bold text-gray-900 text-sm">Virtual Support Agent</h2>
              <p className="text-xs text-green-600 font-medium flex items-center gap-1">
                Online • Typically replies instantly
              </p>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50/30">
            {messages.map((m) => (
              <div key={m.id} className={`flex gap-3 ${m.sender === "user" ? "justify-end" : "justify-start"}`}>
                
                {m.sender === "agent" && (
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-1 shadow-sm">
                    <Headset className="w-4 h-4 text-blue-700" />
                  </div>
                )}

                <div className={`max-w-[75%] px-4 py-3 text-sm shadow-sm ${
                    m.sender === "user"
                      ? "bg-blue-600 text-white rounded-2xl rounded-tr-sm"
                      : "bg-white text-gray-800 border border-gray-100 rounded-2xl rounded-tl-sm"
                  }`}
                >
                  <p className="leading-relaxed whitespace-pre-wrap">{m.text}</p>
                  
                  {m.sender === "agent" && m.audioBase64 && (
                    <button
                      onClick={() => {
                        const audio = new Audio(`data:audio/mp3;base64,${m.audioBase64}`);
                        audio.play();
                      }}
                      className="mt-3 text-xs font-semibold px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 hover:bg-blue-100 flex items-center gap-1.5 transition cursor-pointer"
                    >
                      <Volume2 className="w-3.5 h-3.5" /> Play Audio
                    </button>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-1">
                  <Headset className="w-4 h-4 text-blue-700" />
                </div>
                <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm flex items-center gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-gray-100 bg-white">
            <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-full pr-2 pl-4 py-1.5 focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-all">
              <MessageSquare className="w-5 h-5 text-gray-400 shrink-0" />
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendTextTicket()}
                placeholder="Type your message here..."
                className="flex-1 bg-transparent border-none px-2 py-2 text-sm text-gray-900 placeholder-gray-500 focus:outline-none"
              />
              
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`p-2 rounded-full transition cursor-pointer ${
                  isRecording
                    ? "bg-red-100 text-red-600 animate-pulse"
                    : "bg-white hover:bg-gray-200 text-gray-500 shadow-sm border border-gray-200"
                }`}
                title="Voice Support"
              >
                {isRecording ? <Square className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>

              <button
                onClick={() => sendTextTicket()}
                disabled={loading || !input.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 text-white p-2 rounded-full transition cursor-pointer shadow-sm ml-1"
              >
                <Send className="w-4 h-4 translate-x-px translate-y-px" />
              </button>
            </div>
            <p className="text-center text-[10px] text-gray-400 mt-3 font-medium">
              Powered by LangGraph Agentic Intelligence
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}