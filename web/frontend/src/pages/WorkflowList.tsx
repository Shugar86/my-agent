import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listWorkflows } from '../api/workflowClient';
import {
  listScheduleJobs,
  pauseScheduleJob,
  resumeScheduleJob,
  type ScheduleJob,
} from '../api/appClient';
import type { Workflow } from '../types/workflow';
import { t } from '../i18n';

function formatTime(iso: string | null | undefined): string {
  if (!iso) return t('workflows.scheduleNone');
  try {
    return new Date(iso).toLocaleString('ru-RU');
  } catch {
    return iso;
  }
}

export default function WorkflowList() {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [jobs, setJobs] = useState<ScheduleJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<string | null>(null);

  const loadJobs = useCallback(() => {
    return listScheduleJobs()
      .then((data) => setJobs(data.jobs || []))
      .catch(() => setJobs([]));
  }, []);

  useEffect(() => {
    Promise.all([listWorkflows().catch(() => []), loadJobs()])
      .then(([wfList]) => setWorkflows(wfList))
      .finally(() => setLoading(false));
  }, [loadJobs]);

  const handlePause = async (jobId: string) => {
    setActionId(jobId);
    try {
      await pauseScheduleJob(jobId);
      await loadJobs();
    } finally {
      setActionId(null);
    }
  };

  const handleResume = async (jobId: string) => {
    setActionId(jobId);
    try {
      await resumeScheduleJob(jobId);
      await loadJobs();
    } finally {
      setActionId(null);
    }
  };

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
            <div
              key={job.id}
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr auto auto auto',
                gap: 12,
                alignItems: 'center',
                fontSize: 13,
                marginBottom: 10,
                paddingBottom: 10,
                borderBottom: '1px solid var(--border)',
              }}
            >
              <div>
                <div style={{ fontFamily: 'monospace', marginBottom: 4 }}>{job.id}</div>
                {job.trigger && (
                  <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{job.trigger}</div>
                )}
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: 11 }}>{t('workflows.scheduleNext')}</div>
                <div>
                  {job.paused ? t('workflows.schedulePaused') : formatTime(job.next_run_time)}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: 11 }}>{t('workflows.scheduleLast')}</div>
                <div>{formatTime(job.last_run_time)}</div>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                {job.paused ? (
                  <button
                    type="button"
                    className="btn btn-sm"
                    disabled={actionId === job.id}
                    onClick={() => handleResume(job.id)}
                  >
                    {t('workflows.scheduleResume')}
                  </button>
                ) : (
                  <button
                    type="button"
                    className="btn btn-sm"
                    disabled={actionId === job.id}
                    onClick={() => handlePause(job.id)}
                  >
                    {t('workflows.schedulePause')}
                  </button>
                )}
              </div>
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
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate('/marketplace')}>
            {t('workflows.emptyMarketplaceCta')}
          </button>
        </div>
      )}
    </div>
  );
}
