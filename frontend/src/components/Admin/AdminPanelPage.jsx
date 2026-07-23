import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import './AdminPanelPage.css';

function SummaryCard({ label, value, meta }) {
  return (
    <div className="admin-summary-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {meta ? <small>{meta}</small> : null}
    </div>
  );
}

export default function AdminPanelPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [knowledge, setKnowledge] = useState(null);
  const [traces, setTraces] = useState([]);
  const [reviewItems, setReviewItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [claimingId, setClaimingId] = useState(null);

  useEffect(() => {
    if (!user?.is_admin) return;
    let mounted = true;

    Promise.all([
      fetch('/api/v1/scloda/observability/summary', { credentials: 'include' }).then((res) => res.json()),
      fetch('/api/v1/scloda/knowledge/status', { credentials: 'include' }).then((res) => res.json()),
      fetch('/api/v1/scloda/observability/traces?limit=12', { credentials: 'include' }).then((res) => res.json()),
      fetch('/api/v1/scloda/review-queue?limit=12', { credentials: 'include' }).then((res) => res.json()),
    ])
      .then(([summaryData, knowledgeData, traceData, reviewData]) => {
        if (!mounted) return;
        setSummary(summaryData);
        setKnowledge(knowledgeData);
        setTraces(traceData.traces || []);
        setReviewItems(reviewData.items || []);
      })
      .catch(() => {
        if (!mounted) return;
        setError('Admin observability is unavailable.');
      })
      .finally(() => mounted && setLoading(false));

    return () => {
      mounted = false;
    };
  }, [user]);

  if (!user?.is_admin) {
    return <div className="admin-panel-page"><div className="admin-empty">Admin access only.</div></div>;
  }

  const traceSummary = summary?.summary || {};
  const reviewSummary = summary?.review_queue || {};
  const sourceBreakdown = knowledge?.source_breakdown || {};

  const claimItem = async (itemId) => {
    setClaimingId(itemId);
    try {
      const response = await fetch(`/api/v1/scloda/review-queue/${itemId}/claim`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!response.ok) {
        throw new Error('Claim failed');
      }
      const updated = await response.json();
      setReviewItems((current) => current.map((item) => (item.id === itemId ? updated : item)));
    } catch {
      setError('Could not claim the review item.');
    } finally {
      setClaimingId(null);
    }
  };

  return (
    <div className="admin-panel-page">
      <div className="admin-hero">
        <span className="admin-kicker">Scloda Operations</span>
        <h1>Admin Panel</h1>
        <p>Observe traces, review low-confidence answers, and inspect where the agent still needs tightening.</p>
      </div>

      {loading && <div className="admin-empty">Loading admin telemetry...</div>}
      {error && <div className="admin-empty">{error}</div>}

      {!loading && !error && (
        <>
          <section className="admin-summary-grid">
            <SummaryCard label="Traces (7d)" value={traceSummary.total_traces || 0} meta="Recent Scloda runs" />
            <SummaryCard label="Avg latency" value={`${traceSummary.avg_latency_ms || 0} ms`} meta="Observed across recent traces" />
            <SummaryCard label="Avg tokens" value={traceSummary.avg_tokens || 0} meta="Per request average" />
            <SummaryCard label="Pending reviews" value={reviewSummary.pending || 0} meta={`${reviewSummary.assigned_pending || 0} assigned / ${reviewSummary.unassigned_pending || 0} unassigned`} />
            <SummaryCard label="Knowledge chunks" value={knowledge?.chunks || 0} meta={knowledge?.embedding_model || 'No embeddings'} />
          </section>

          <section className="admin-section">
            <div className="admin-section-header">
              <h2>Recent traces</h2>
              <p>Most recent agent responses with routing and confidence.</p>
            </div>
            <div className="admin-table">
              {traces.map((trace) => (
                <div key={trace.trace_id} className="admin-row">
                  <div>
                    <strong>{trace.task_type || 'general'}</strong>
                    <p>{trace.user_message}</p>
                  </div>
                  <div>
                    <span className="admin-pill">{trace.response_status}</span>
                    <small>{trace.confidence || 'n/a'}</small>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="admin-section">
            <div className="admin-section-header">
              <h2>Review queue</h2>
              <p>Answers escalated because confidence dropped or the judge flagged grounding risk.</p>
            </div>
            <div className="admin-table">
              {reviewItems.length === 0 && <div className="admin-empty compact">No review items right now.</div>}
              {reviewItems.map((item) => (
                <div key={item.id} className="admin-row">
                  <div>
                    <strong>{item.reason}</strong>
                    <p>{item.user_message}</p>
                    <small>{item.assignee_email ? `Assigned to ${item.assignee_email}` : 'Unassigned'}</small>
                  </div>
                  <div>
                    <span className="admin-pill">{item.status}</span>
                    <small>{item.priority}</small>
                    {!item.assignee_user_id && item.status === 'pending' ? (
                      <button
                        type="button"
                        className="admin-action"
                        onClick={() => claimItem(item.id)}
                        disabled={claimingId === item.id}
                      >
                        {claimingId === item.id ? 'Claiming...' : 'Claim'}
                      </button>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="admin-section">
            <div className="admin-section-header">
              <h2>Knowledge mix</h2>
              <p>What the retrieval layer is actually embedding from the product and database.</p>
            </div>
            <div className="admin-table">
              {Object.keys(sourceBreakdown).length === 0 && <div className="admin-empty compact">No indexed chunks yet.</div>}
              {Object.entries(sourceBreakdown).map(([kind, count]) => (
                <div key={kind} className="admin-row">
                  <div>
                    <strong>{kind}</strong>
                    <p>Indexed retrieval chunks for this source type.</p>
                  </div>
                  <div>
                    <span className="admin-pill">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
