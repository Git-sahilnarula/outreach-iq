import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, CheckCheck, Trash2, X, Briefcase, Brain, ThumbsUp, ThumbsDown, Star, FileText, CheckCircle2, Send } from 'lucide-react';
import { notificationsAPI } from '../services/api';
import type { Notification, NotificationType } from '../types';

// Poll the unread count every 30 seconds
const POLL_INTERVAL_MS = 30_000;

const typeIcon = (type: NotificationType) => {
  const cls = 'w-4 h-4 flex-shrink-0';
  switch (type) {
    case 'NEW_JOB':           return <Briefcase className={`${cls} text-blue-500`} />;
    case 'ANALYSIS_COMPLETE': return <Brain className={`${cls} text-purple-500`} />;
    case 'REVIEW_REQUIRED':   return <Star className={`${cls} text-yellow-500`} />;
    case 'JOB_APPROVED':      return <ThumbsUp className={`${cls} text-green-500`} />;
    case 'JOB_REJECTED':      return <ThumbsDown className={`${cls} text-red-500`} />;
    case 'PROPOSAL_READY':    return <FileText className={`${cls} text-indigo-500`} />;
    case 'PROPOSAL_APPROVED': return <CheckCircle2 className={`${cls} text-emerald-600`} />;
    case 'OUTREACH_SENT':     return <Send className={`${cls} text-teal-600`} />;
    default:                  return <Bell className={`${cls} text-gray-400`} />;
  }
};



const timeAgo = (iso: string) => {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1)  return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
};

const NotificationBell = () => {
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Poll unread count
  const pollCount = useCallback(async () => {
    try {
      const res = await notificationsAPI.getCount();
      setUnread(res.data.unread);
    } catch {
      // Silently fail — user may not be logged in yet
    }
  }, []);

  useEffect(() => {
    pollCount();
    const interval = setInterval(pollCount, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [pollCount]);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const res = await notificationsAPI.getAll({ limit: 20 });
      setNotifications(res.data.notifications);
      setUnread(res.data.unread);
    } catch {
      // noop
    } finally {
      setLoading(false);
    }
  };

  const handleOpen = () => {
    setOpen(o => !o);
    if (!open) loadNotifications();
  };

  const handleMarkAllRead = async () => {
    await notificationsAPI.markAllRead();
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnread(0);
  };

  const handleClearAll = async () => {
    await notificationsAPI.clearAll();
    setNotifications([]);
    setUnread(0);
  };

  const handleClickNotification = async (n: Notification) => {
    if (!n.read) {
      await notificationsAPI.markRead(n.id);
      setNotifications(prev => prev.map(x => x.id === n.id ? { ...x, read: true } : x));
      setUnread(c => Math.max(0, c - 1));
    }
    if (n.job_id) {
      navigate(`/jobs/${n.job_id}`);
      setOpen(false);
    }
  };

  return (
    <div className="relative" ref={panelRef}>
      {/* Bell button */}
      <button
        id="notification-bell-btn"
        onClick={handleOpen}
        className="relative p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
        aria-label={`Notifications${unread > 0 ? ` (${unread} unread)` : ''}`}
      >
        <Bell className="w-5 h-5" />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-bold leading-none">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {/* Dropdown panel */}
      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-gray-200 z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
            <div className="flex items-center gap-1">
              {unread > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  title="Mark all read"
                  className="p-1.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                >
                  <CheckCheck className="w-4 h-4" />
                </button>
              )}
              {notifications.length > 0 && (
                <button
                  onClick={handleClearAll}
                  title="Clear all"
                  className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => setOpen(false)}
                className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="max-h-80 overflow-y-auto divide-y divide-gray-50">
            {loading ? (
              <div className="py-8 text-center text-sm text-gray-400">Loading…</div>
            ) : notifications.length === 0 ? (
              <div className="py-8 text-center">
                <Bell className="w-8 h-8 text-gray-200 mx-auto mb-2" />
                <p className="text-sm text-gray-400">No notifications yet</p>
              </div>
            ) : (
              notifications.map(n => (
                <button
                  key={n.id}
                  onClick={() => handleClickNotification(n)}
                  className={`w-full text-left px-4 py-3 flex gap-3 items-start hover:bg-gray-50 transition-colors ${
                    !n.read ? 'bg-blue-50/40' : ''
                  }`}
                >
                  <div className="mt-0.5">{typeIcon(n.type as NotificationType)}</div>
                  <div className="min-w-0 flex-1">
                    <p className={`text-sm ${!n.read ? 'font-semibold text-gray-900' : 'text-gray-700'} leading-snug`}>
                      {n.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5 leading-snug line-clamp-2">{n.message}</p>
                    <p className="text-[11px] text-gray-400 mt-1">{timeAgo(n.created_at)}</p>
                  </div>
                  {!n.read && (
                    <span className="mt-1.5 w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
