import React, { useEffect, useMemo, useState } from 'react';
import { FaExpand, FaMinus, FaPlus } from 'react-icons/fa';
import { useAuth } from '../../context/AuthContext';
import './QuantumLabPage.css';

const STATUS_COLORS = {
  active: 'status-active',
  in_progress: 'status-progress',
  planned: 'status-planned',
};

const TRACKS = [
  {
    label: 'Dataset Layer',
    slug: 'scloda-human-review',
    status: 'live now',
    description: 'Trace logs, reviewer outcomes, and operator feedback create the first labeled substrate.',
  },
  {
    label: 'Vector Memory',
    slug: 'scloda-neural-memory',
    status: 'live now',
    description: 'pgvector retrieval in Postgres keeps answers grounded and builds reusable memory.',
  },
  {
    label: 'Neural Training Loop',
    slug: 'scloda-neural-network',
    status: 'next build',
    description: 'The module we want to train: capture, label, assemble datasets, evaluate, and improve.',
  },
  {
    label: 'Research Sandbox',
    slug: 'scloda-quantum-lab',
    status: 'planned',
    description: 'Quantum computing, neural-network experiments, and domain graph work all live here first.',
  },
];

function maturityMeaning(score) {
  if (score >= 75) return 'Production-grade capability with narrower gaps.';
  if (score >= 50) return 'Live and useful, but still incomplete.';
  if (score >= 25) return 'Structured and in progress, not yet a strong finished module.';
  return 'Roadmap or scaffolding stage, not yet operational.';
}

export default function QuantumLabPage() {
  const { user } = useAuth();
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedSlug, setSelectedSlug] = useState('scloda-neural-network');
  const [treeZoom, setTreeZoom] = useState(0.88);
  const [mapZoom, setMapZoom] = useState(0.92);

  useEffect(() => {
    let mounted = true;
    fetch('/api/v1/scloda/capabilities', { credentials: 'include' })
      .then((res) => res.json())
      .then((data) => {
        if (!mounted) return;
        setNodes(data.nodes || []);
      })
      .catch(() => {
        if (!mounted) return;
        setError('Quantum Lab is unavailable right now.');
      })
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, []);

  const nodeMap = useMemo(
    () => Object.fromEntries(nodes.map((node) => [node.slug, node])),
    [nodes],
  );

  const rootNodes = nodes.filter((node) => !node.parent_slug);
  const childrenFor = (slug) => nodes.filter((node) => node.parent_slug === slug);
  const quantumChildren = childrenFor('scloda-quantum-lab');
  const selectedNode = nodeMap[selectedSlug] || nodes[0] || null;
  const neuralLoopNode = nodeMap['scloda-neural-network'];

  const architectureColumns = [
    {
      title: 'Inputs',
      items: [
        { label: 'User prompt', slug: 'scloda-core' },
        { label: 'Profile + risk context', slug: 'scloda-core' },
        { label: 'Active page context', slug: 'scloda-core' },
      ],
    },
    {
      title: 'Agent Core',
      items: [
        { label: 'Guardrails', slug: 'scloda-core' },
        { label: 'Task router', slug: 'scloda-core' },
        { label: 'OpenRouter model', slug: 'scloda-core' },
      ],
    },
    {
      title: 'Grounding',
      items: [
        { label: 'pgvector memory', slug: 'scloda-neural-memory' },
        { label: 'Market/real-estate tools', slug: 'scloda-real-estate' },
        { label: 'Knowledge chunks', slug: 'scloda-neural-memory' },
      ],
    },
    {
      title: 'Trust Layer',
      items: [
        { label: 'Confidence scoring', slug: 'scloda-human-review' },
        { label: 'Human review queue', slug: 'scloda-human-review' },
        { label: 'Capability roadmap', slug: 'scloda-agent-topology' },
      ],
    },
  ];

  const renderBranch = (node, depth = 0) => {
    const children = childrenFor(node.slug);
    const isRoot = depth === 0;
    const isSelected = selectedSlug === node.slug;

    return (
      <div key={node.slug} className={`quantum-branch quantum-depth-${Math.min(depth, 2)}`}>
        <button
          type="button"
          className={`quantum-node ${isRoot ? 'quantum-node-root' : ''} ${isSelected ? 'quantum-node-selected' : ''}`}
          onClick={() => setSelectedSlug(node.slug)}
        >
          <div className="quantum-node-top">
            <span className={`quantum-status ${STATUS_COLORS[node.status] || 'status-planned'}`}>
              {node.status.replace('_', ' ')}
            </span>
            <span className="quantum-score">{node.maturity_score}%</span>
          </div>
          {isRoot ? <h3>{node.label}</h3> : <h4>{node.label}</h4>}
          <p>{node.description}</p>
          <small>{node.domain}</small>
        </button>

        {children.length > 0 && (
          <div className="quantum-branches">
            {children.map((child) => renderBranch(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="quantum-lab-page">
      <section className="quantum-hero">
        <span className="quantum-kicker">Scloda Research Layer</span>
        <h1>Quantum Lab</h1>
        <p>
          This is where Scloda stops being only a chatbot and becomes a growing intelligence
          system: memory, review loops, market logic, neural branches, and future Chile real-estate modules.
        </p>
      </section>

      <section className="quantum-grid">
        <article className="quantum-card">
          <h2>What this space is for</h2>
          <p>
            Train Scloda gradually, track capability maturity, and expose what is already live versus what still needs
            data, research, or human validation.
          </p>
        </article>
        <article className="quantum-card">
          <h2>What the percentages mean</h2>
          <p>
            These percentages are maturity scores, not model accuracy. They estimate how operational each capability is:
            data readiness, tooling, grounding, reviewability, and production usefulness.
          </p>
          <div className="quantum-legend-list">
            <div><strong>0-24%</strong><span>roadmap or scaffolding only</span></div>
            <div><strong>25-49%</strong><span>working structure, still partial</span></div>
            <div><strong>50-74%</strong><span>live and useful, with real gaps</span></div>
            <div><strong>75-100%</strong><span>strong production maturity</span></div>
          </div>
        </article>
      </section>

      <section className="quantum-card quantum-spotlight">
        <div className="quantum-spotlight-copy">
          <span className="quantum-section-label">Neural Network Workspace</span>
          <h2>Where Scloda learns next</h2>
          <p>
            Click the tracks below to inspect what already exists, what is only planned, and how the future training loop will work.
          </p>
        </div>

        <div className="quantum-track-grid">
          {TRACKS.map((track) => {
            const linkedNode = nodeMap[track.slug];
            const selected = selectedSlug === track.slug;
            return (
              <button
                key={track.label}
                type="button"
                className={`quantum-track-card quantum-clickable ${selected ? 'quantum-track-card-active' : ''}`}
                onClick={() => setSelectedSlug(track.slug)}
              >
                <div className="quantum-track-status">{track.status}</div>
                <h3>{track.label}</h3>
                <p>{track.description}</p>
                {linkedNode ? <small>{linkedNode.maturity_score}% maturity</small> : null}
              </button>
            );
          })}
        </div>
      </section>

      {selectedNode && (
        <section className="quantum-card quantum-detail-shell">
          <div className="quantum-detail-header">
            <div>
              <span className="quantum-section-label">Selected Module</span>
              <h2>{selectedNode.label}</h2>
              <p>{selectedNode.description}</p>
            </div>
            <div className="quantum-detail-score">
              <span className={`quantum-status ${STATUS_COLORS[selectedNode.status] || 'status-planned'}`}>
                {selectedNode.status.replace('_', ' ')}
              </span>
              <strong>{selectedNode.maturity_score}%</strong>
              <small>{maturityMeaning(selectedNode.maturity_score)}</small>
            </div>
          </div>

          <div className="quantum-detail-grid">
            <div className="quantum-detail-card">
              <h3>Why this score exists</h3>
              <div className="quantum-breakdown">
                {(selectedNode.metadata?.progress_breakdown || []).map((item) => (
                  <div key={item.label} className="quantum-breakdown-row">
                    <div className="quantum-breakdown-head">
                      <strong>{item.label}</strong>
                      <span>{item.value}%</span>
                    </div>
                    <div className="quantum-breakdown-bar">
                      <span style={{ width: `${item.value}%` }} />
                    </div>
                    <p>{item.detail}</p>
                  </div>
                ))}
                {(!selectedNode.metadata?.progress_breakdown || selectedNode.metadata.progress_breakdown.length === 0) && (
                  <p className="quantum-muted">This module does not have a detailed maturity breakdown yet.</p>
                )}
              </div>
            </div>

            <div className="quantum-detail-card">
              <h3>Next actions</h3>
              <div className="quantum-next-list">
                {(selectedNode.metadata?.next_actions || []).map((item) => (
                  <div key={item} className="quantum-next-item">{item}</div>
                ))}
                {(!selectedNode.metadata?.next_actions || selectedNode.metadata.next_actions.length === 0) && (
                  <p className="quantum-muted">No explicit next actions are attached to this node yet.</p>
                )}
              </div>
            </div>
          </div>

          {user?.is_admin && selectedNode.metadata?.mermaid && (
            <div className="quantum-card quantum-admin-only">
              <div className="quantum-admin-header">
                <div>
                  <span className="quantum-section-label">Admin-only Mermaid</span>
                  <h3>Current loop / topology spec</h3>
                  <p>This is the actual map of the current system or the intended training loop as of July 23, 2026.</p>
                </div>
                <div className="quantum-admin-badge">Admin only</div>
              </div>
              <pre className="quantum-mermaid-code">{selectedNode.metadata.mermaid.trim()}</pre>
            </div>
          )}
        </section>
      )}

      {user?.is_admin && neuralLoopNode?.metadata?.loop_steps?.length > 0 && (
        <section className="quantum-card quantum-loop-shell">
          <div className="quantum-tree-header">
            <div>
              <span className="quantum-section-label">Admin-only Training Loop</span>
              <h2>Neural training loop</h2>
              <p>This is not a live neural network yet. It is the supervised loop we are building from captured product behavior.</p>
            </div>
          </div>

          <div className="quantum-loop-steps">
            {neuralLoopNode.metadata.loop_steps.map((step, index) => (
              <div key={step.title} className="quantum-loop-step">
                <div className={`quantum-loop-state quantum-loop-${step.state}`}>{step.state}</div>
                <strong>{String(index + 1).padStart(2, '0')} · {step.title}</strong>
                <p>{step.subtitle}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="quantum-card quantum-diagram-shell">
        <div className="quantum-tree-header">
          <div>
            <span className="quantum-section-label">Current Diagram</span>
            <h2>Scloda System Map</h2>
            <p>The current agent path from user input to grounded output and review. Every node is clickable.</p>
          </div>
          <div className="quantum-zoom-controls">
            <button type="button" onClick={() => setMapZoom((value) => Math.max(0.7, Number((value - 0.08).toFixed(2))))}><FaMinus /></button>
            <button type="button" onClick={() => setMapZoom(0.92)}><FaExpand /></button>
            <button type="button" onClick={() => setMapZoom((value) => Math.min(1.2, Number((value + 0.08).toFixed(2))))}><FaPlus /></button>
          </div>
        </div>

        <div className="quantum-map-viewport">
          <div className="quantum-map-canvas" style={{ transform: `scale(${mapZoom})` }}>
            <div className="quantum-architecture-grid">
              {architectureColumns.map((column) => (
                <div key={column.title} className="quantum-architecture-column">
                  <h3>{column.title}</h3>
                  {column.items.map((item) => (
                    <button
                      key={item.label}
                      type="button"
                      className={`quantum-architecture-node quantum-clickable ${selectedSlug === item.slug ? 'quantum-architecture-node-active' : ''}`}
                      onClick={() => setSelectedSlug(item.slug)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="quantum-tree-shell">
        <div className="quantum-tree-header">
          <div>
            <h2>Scloda Capability Tree</h2>
            <p>Zoom, scroll, and click nodes to inspect how complete each branch really is.</p>
          </div>
          <div className="quantum-zoom-controls">
            <button type="button" onClick={() => setTreeZoom((value) => Math.max(0.68, Number((value - 0.08).toFixed(2))))}><FaMinus /></button>
            <button type="button" onClick={() => setTreeZoom(0.88)}><FaExpand /></button>
            <button type="button" onClick={() => setTreeZoom((value) => Math.min(1.18, Number((value + 0.08).toFixed(2))))}><FaPlus /></button>
          </div>
        </div>

        {loading && <div className="quantum-empty">Loading capability tree...</div>}
        {error && <div className="quantum-empty">{error}</div>}

        {!loading && !error && (
          <div className="quantum-tree-viewport">
            <div className="quantum-tree-canvas" style={{ transform: `scale(${treeZoom})` }}>
              <div className="quantum-tree">
                {rootNodes.map((root) => renderBranch(root))}
              </div>
            </div>
          </div>
        )}
      </section>

      {!loading && !error && quantumChildren.length > 0 && (
        <section className="quantum-card quantum-research-panel">
          <div className="quantum-tree-header">
            <div>
              <span className="quantum-section-label">Research Tracks</span>
              <h2>Quantum Lab Modules</h2>
              <p>These cards are now clickable so the lab can become a real workspace instead of a static roadmap.</p>
            </div>
          </div>

          <div className="quantum-track-grid">
            {quantumChildren.map((node) => (
              <button
                key={node.slug}
                type="button"
                className={`quantum-track-card quantum-clickable ${selectedSlug === node.slug ? 'quantum-track-card-active' : ''}`}
                onClick={() => setSelectedSlug(node.slug)}
              >
                <div className={`quantum-track-status quantum-track-status-${node.status}`}>
                  {node.status.replace('_', ' ')}
                </div>
                <h3>{node.label}</h3>
                <p>{node.description}</p>
                <small>{node.domain} · {node.maturity_score}%</small>
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
