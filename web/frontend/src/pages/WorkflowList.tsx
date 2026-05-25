import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listWorkflows } from '../api/workflowClient';
import { listScheduleJobs, type ScheduleJob } from '../api/appClient';
import type { Workflow } from '../types/workflow';
import { t } from '../i18n';

export default function WorkflowList() {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [jobs, setJobs] = useState<ScheduleJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      listWorkflows().catch(() => []),
      listScheduleJobs().then((data) => data.jobs || []).catch(() => []),
    ])
      .then(([wfList, jobList]) => {
        setWorkflows(wfList);
        setJobs(jobList);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ padding: 30 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, marginBottom: 4 }}>{t('workflows.title')}</h1>
          <p style={{ color: 'var(--text-muted)' }}>{t('workflows.subtitle')}</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/workflows/new')}>{t('workflows.new')}</button>
      </div>

      {jobs.length > 0 && (
        <section className="card" style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 14, marginBottom: 12 }}>{t('workflows.scheduleNext')}</h2>
          {jobs.map((job) => (
            <div key={job.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 8 }}>
              <span style={{ fontFamily: 'monospace' }}>{job.id}</span>
              <span style={{ color: 'var(--text-muted)' }}>
                {(job as { next_run_time?: string }).next_run_time || t('workflows.scheduleNone')}
              </span>
            </div>
          ))}
        </section>
      )}

      {loading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 100 }} />)}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {workflows.map((wf) => (
          <div
            key={wf.id}
            className="card"
            onClick={() => navigate(`/workflows/${wf.id}`)}
            style={{ cursor: 'pointer' }}
          >
            <h3 style={{ marginBottom: 8 }}>{wf.name}</h3>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              {wf.definition.nodes.length} {t('workflows.nodes')} · <span style={{ color: wf.status === 'active' ? 'var(--success)' : 'var(--text-muted)' }}>{wf.status}</span>
            </p>
          </div>
        ))}
      </div>

      {!loading && workflows.length === 0 && (
        <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-muted)' }}>
          <p>{t('workflows.empty')}</p>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate('/workflows/new')}>
            {t('workflows.emptyCta')}
          </button>
        </div>
      )}
    </div>
  );
}
