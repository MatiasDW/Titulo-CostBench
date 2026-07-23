import React, { useEffect, useMemo, useState } from 'react';
import { FaBrain, FaDatabase, FaShieldAlt, FaUsers } from 'react-icons/fa';
import { useAuth } from '../../context/AuthContext';
import './AdminPanelPage.css';

function SummaryCard({ label, value, meta, icon }) {
  return (
    <div className="admin-summary-card">
      <div className="admin-summary-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
      {meta ? <small>{meta}</small> : null}
    </div>
  );
}

function formatPercentMeaning(score) {
  if (score >= 75) return 'Production-grade with narrower gaps.';
  if (score >= 50) return 'Live and useful, but still missing depth or automation.';
  if (score >= 25) return 'Structured and in progress, not yet a strong finished capability.';
  return 'Mostly roadmap or scaffolding, not yet operational as a real module.';
}

export default function AdminPanelPage() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [knowledge, setKnowledge] = useState(null);
  const [traces, setTraces] = useState([]);
  const [reviewItems, setReviewItems] = useState([]);
  const [adminUsers, setAdminUsers] = useState([]);
  const [accountSummary, setAccountSummary] = useState(null);
  const [capabilityNodes, setCapabilityNodes] = useState([]);
  const [selectedCapabilitySlug, setSelectedCapabilitySlug] = useState('scloda-neural-network');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [claimingId, setClaimingId] = useState(null);
  const [savingUserId, setSavingUserId] = useState(null);

  useEffect(() => {
    if (!user?.is_admin) return;
    let mounted = true;

    Promise.all([
      fetch('/api/v1/scloda/observability/summary', { credentials: 'include' }).then((res) => res.json()),
      fetch('/api/v1/scloda/knowledge/status', { credentials: 'include' }).then((res) => res.json()),
      fetch('/api/v1/scloda/observability/traces?limit=12', { credentials: 'include' }).then((res) => res.json()),
      fetch('/api/v1/scloda/review-queue?limit=12', { credentials: 'include' }).then((res) => res.json()),
      fetch('/api/v1/auth/admin/users', { credentials: 'include' }).then((res) => res.json()),
      fetch('/api/v1/scloda/capabilities', { credentials: 'include' }).then((res) => res.json()),
    ])
      .then(([summaryData, knowledgeData, traceData, reviewData, adminUserData, capabilityData]) => {
        if (!mounted) return;
        setSummary(summaryData);
        setKnowledge(knowledgeData);
        setTraces(traceData.traces || []);
        setReviewItems(reviewData.items || []);
        setAdminUsers(adminUserData.users || []);
        setAccountSummary(adminUserData.summary || null);
        setCapabilityNodes(capabilityData.nodes || []);
      })
      .catch(() => {
        if (!mounted) return;
        setError('Admin operations are unavailable.');
      })
      .finally(() => mounted && setLoading(false));

    return () => {
      mounted = false;
    };
  }, [user]);

  const selectedCapability = useMemo(() => (
    capabilityNodes.find((node) => node.slug === selectedCapabilitySlug) || capabilityNodes[0] || null
  ), [capabilityNodes, selectedCapabilitySlug]);

  const highlightedCapabilities = useMemo(() => capabilityNodes.filter((node) => [
    'scloda-neural-network',
    'scloda-neural-memory',
    'scloda-agent-topology',
    'scloda-quantum-lab',
  ].includes(node.slug)), [capabilityNodes]);

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
      if (!response.ok) throw new Error('Claim failed');
      const updated = await response.json();
      setReviewItems((current) => current.map((item) => (item.id === itemId ? updated : item)));
    } catch {
      setError('Could not claim the review item.');
    } finally {
      setClaimingId(null);
    }
  };

  const updateUser = async (targetUser, updates) => {
    setSavingUserId(targetUser.id);
    try {
      const response = await fetch(`/api/v1/auth/admin/users/${targetUser.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(updates),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Could not update user');

      setAdminUsers((current) => {
        const nextUsers = current.map((item) => (item.id === targetUser.id ? payload.user : item));
        setAccountSummary({
          total_users: nextUsers.length,
          active_users: nextUsers.filter((item) => item.is_active).length,
          admin_users: nextUsers.filter((item) => item.is_admin).length,
          onboarded_users: nextUsers.filter((item) => item.onboarding_completed).length,
          wallet_users: nextUsers.filter((item) => item.has_wallet).length,
        });
        return nextUsers;
      });
    } catch (err) {
      setError(err.message || 'Could not update user.');
    } finally {
      setSavingUserId(null);
    }
  };

  return (
    <div className="admin-panel-page">
      <div className="admin-hero">
        <span className="admin-kicker">Scloda Operations</span>
        <h1>Admin Panel</h1>
        <p>Manage accounts, inspect the training loop, review weak answers, and understand what Scloda can actually learn from today.</p>
      </div>

      {loading && <div className="admin-empty">Loading admin operations...</div>}
      {error && <div className="admin-empty">{error}</div>}

      {!loading && !error && (
        <>
          <section className="admin-summary-grid">
            <SummaryCard label="Accounts" value={accountSummary?.total_users || 0} meta={`${accountSummary?.active_users || 0} active users`} icon={<FaUsers />} />
            <SummaryCard label="Admin seats" value={accountSummary?.admin_users || 0} meta={`${accountSummary?.onboarded_users || 0} onboarded`} icon={<FaShieldAlt />} />
            <SummaryCard label="Knowledge chunks" value={knowledge?.chunks || 0} meta={knowledge?.embedding_model || 'No embeddings'} icon={<FaDatabase />} />
            <SummaryCard label="Training readiness" value={`${selectedCapability?.maturity_score || 0}%`} meta={selectedCapability ? formatPercentMeaning(selectedCapability.maturity_score) : 'Select a module'} icon={<FaBrain />} />
            <SummaryCard label="Traces (7d)" value={traceSummary.total_traces || 0} meta="Recent Scloda runs" icon={<FaBrain />} />
            <SummaryCard label="Pending reviews" value={reviewSummary.pending || 0} meta={`${reviewSummary.assigned_pending || 0} assigned / ${reviewSummary.unassigned_pending || 0} unassigned`} icon={<FaShieldAlt />} />
          </section>

          <section className="admin-section">
            <div className="admin-section-header">
              <div>
                <h2>Accounts Control</h2>
                <p>Activate, suspend, and promote operator accounts without leaving the admin surface.</p>
              </div>
            </div>
            <div className="admin-table">
              {adminUsers.map((account) => (
                <div key={account.id} className="admin-row admin-row-rich">
                  <div>
                    <strong>{account.email}</strong>
                    <p>{account.first_name || account.last_name ? `${account.first_name || ''} ${account.last_name || ''}`.trim() : 'No profile name yet'}</p>
                    <small>
                      {account.is_active ? 'Active' : 'Suspended'} · {account.onboarding_completed ? 'Onboarded' : 'Onboarding pending'} · {account.has_wallet ? 'Wallet ready' : 'No wallet'}
                    </small>
                  </div>
                  <div className="admin-row-actions">
                    <span className="admin-pill">{account.role}</span>
                    <span className="admin-pill subdued">{account.risk_profile || 'no risk profile'}</span>
                    <small>{account.trace_count} traces · {account.review_count} review items</small>
                    <div className="admin-inline-actions">
                      <button
                        type="button"
                        className="admin-action"
                        disabled={savingUserId === account.id || account.id === user.id}
                        onClick={() => updateUser(account, { role: account.is_admin ? 'user' : 'admin' })}
                      >
                        {savingUserId === account.id ? 'Saving...' : account.is_admin ? 'Make user' : 'Promote admin'}
                      </button>
                      <button
                        type="button"
                        className="admin-action admin-action-secondary"
                        disabled={savingUserId === account.id || account.id === user.id}
                        onClick={() => updateUser(account, { is_active: !account.is_active })}
                      >
                        {savingUserId === account.id ? 'Saving...' : account.is_active ? 'Suspend' : 'Activate'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="admin-section">
            <div className="admin-section-header">
              <div>
                <h2>Neural Training Loop</h2>
                <p>Admin-only map of what already exists for training Scloda and what still needs operator work.</p>
              </div>
              <div className="admin-capability-pills">
                {highlightedCapabilities.map((node) => (
                  <button
                    key={node.slug}
                    type="button"
                    className={`admin-capability-pill ${selectedCapabilitySlug === node.slug ? 'active' : ''}`}
                    onClick={() => setSelectedCapabilitySlug(node.slug)}
                  >
                    {node.label}
                  </button>
                ))}
              </div>
            </div>

            {selectedCapability && (
              <div className="admin-training-layout">
                <div className="admin-training-detail">
                  <div className="admin-node-top">
                    <span className="admin-pill">{selectedCapability.status.replace('_', ' ')}</span>
                    <span className="admin-score">{selectedCapability.maturity_score}%</span>
                  </div>
                  <h3>{selectedCapability.label}</h3>
                  <p>{selectedCapability.description}</p>
                  <small>{formatPercentMeaning(selectedCapability.maturity_score)}</small>

                  {selectedCapability.metadata?.progress_breakdown?.length > 0 && (
                    <div className="admin-breakdown">
                      {selectedCapability.metadata.progress_breakdown.map((item) => (
                        <div key={item.label} className="admin-breakdown-row">
                          <div className="admin-breakdown-header">
                            <strong>{item.label}</strong>
                            <span>{item.value}%</span>
                          </div>
                          <div className="admin-breakdown-bar">
                            <span style={{ width: `${item.value}%` }} />
                          </div>
                          <p>{item.detail}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="admin-training-visuals">
                  {selectedCapability.metadata?.loop_steps?.length > 0 && (
                    <div className="admin-training-card">
                      <h4>Training stages</h4>
                      <div className="admin-stage-list">
                        {selectedCapability.metadata.loop_steps.map((step) => (
                          <div key={step.title} className="admin-stage-item">
                            <span className={`admin-stage-state admin-stage-${step.state}`}>{step.state}</span>
                            <div>
                              <strong>{step.title}</strong>
                              <p>{step.subtitle}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedCapability.metadata?.mermaid && (
                    <div className="admin-training-card">
                      <h4>Mermaid map</h4>
                      <pre className="admin-mermaid-code">{selectedCapability.metadata.mermaid.trim()}</pre>
                    </div>
                  )}
                </div>
              </div>
            )}
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
              <p>Answers escalated because confidence dropped or grounding looked weak.</p>
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
