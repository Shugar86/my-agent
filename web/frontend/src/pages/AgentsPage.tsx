import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  listAgents,
  saveAgent,
  deleteAgent,
  duplicateAgent,
  type Agent,
} from '../api/appClient';
import PageHeader from '../components/ui/PageHeader';
import Modal from '../components/ui/Modal';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import EmptyState from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';
import { t } from '../i18n';

const EMPTY_FORM = {
  id: '',
  name: '',
  icon: '🤖',
  description: '',
  role: '',
  skills: '',
  tools: '',
};

/** Agent CRUD page — migrated from legacy agents.html. */
export default function AgentsPage() {
  const { showToast } = useToast();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const load = () => {
    listAgents()
      .then((list) => setAgents(Array.isArray(list) ? list : []))
      .catch(() => setAgents([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setModalOpen(true);
  };

  const openEdit = (agent: Agent) => {
    setForm({
      id: agent.id,
      name: agent.name || '',
      icon: agent.icon || '🤖',
      description: agent.description || '',
      role: agent.role || '',
      skills: (agent.skills || []).join(', '),
      tools: (agent.tools || []).join(', '),
    });
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) return;
    const id = form.id || form.name.toLowerCase().replace(/\s+/g, '-');
    try {
      await saveAgent({
        id,
        name: form.name,
        icon: form.icon || '🤖',
        description: form.description,
        role: form.role,
        model: 'kimi',
        skills: form.skills.split(',').map((s) => s.trim()).filter(Boolean),
        tools: form.tools.split(',').map((s) => s.trim()).filter(Boolean),
        sub_agents: [],
        memory: { enabled: true, scope: 'agent' },
        output: { format: 'markdown', path: '' },
      });
      showToast(t('common.success'));
      setModalOpen(false);
      load();
    } catch {
      showToast(t('settings.saveFailed'), 'error');
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await deleteAgent(deleteId);
      showToast(t('common.success'));
      load();
    } catch {
      showToast(t('common.error'), 'error');
    } finally {
      setDeleteId(null);
    }
  };

  const handleDuplicate = async (id: string) => {
    try {
      await duplicateAgent(id);
      showToast(t('common.success'));
      load();
    } catch {
      showToast(t('common.error'), 'error');
    }
  };

  if (loading) {
    return (
      <div className="page-content">
        <div className="skeleton" style={{ height: 40, width: 240, marginBottom: 24 }} />
        <div className="cards-grid">
          {[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 140 }} />)}
        </div>
      </div>
    );
  }

  return (
    <div className="page-content">
      <PageHeader
        title={t('agents.title')}
        actions={<button type="button" className="btn btn-primary" onClick={openCreate}>{t('agents.newAgent')}</button>}
      />

      {agents.length === 0 ? (
        <EmptyState
          title={t('agents.empty')}
          actionLabel={t('agents.emptyCta')}
          onAction={openCreate}
        />
      ) : (
        <div className="cards-grid">
          {agents.map((a) => (
            <div key={a.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <span style={{ fontSize: 28 }}>{a.icon || '🤖'}</span>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button type="button" className="btn" onClick={() => openEdit(a)} aria-label={t('common.edit')}>✏️</button>
                  <button type="button" className="btn" onClick={() => handleDuplicate(a.id)} aria-label={t('common.duplicate')}>📋</button>
                  <button type="button" className="btn btn-danger" onClick={() => setDeleteId(a.id)} aria-label={t('common.delete')}>🗑</button>
                </div>
              </div>
              <h3 style={{ marginTop: 8, fontSize: 15 }}>{a.name}</h3>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: '6px 0 12px' }}>{a.description || a.role?.slice(0, 80)}</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {(a.skills || []).slice(0, 4).map((s) => (
                  <span key={s} className="badge">{s}</span>
                ))}
              </div>
              <Link to={`/chat?agent=${a.id}`} className="btn" style={{ marginTop: 12, width: '100%', justifyContent: 'center' }}>
                {t('nav.chat')}
              </Link>
            </div>
          ))}
        </div>
      )}

      <Modal
        open={modalOpen}
        title={form.id ? t('agents.editAgent') : t('agents.newAgent')}
        onClose={() => setModalOpen(false)}
        footer={
          <>
            <button type="button" className="btn" onClick={() => setModalOpen(false)}>{t('common.cancel')}</button>
            <button type="button" className="btn btn-primary" onClick={handleSave}>{t('common.save')}</button>
          </>
        }
      >
        <div className="form-group">
          <label>{t('agents.name')}</label>
          <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div className="form-group">
          <label>{t('agents.icon')}</label>
          <input className="input" value={form.icon} onChange={(e) => setForm({ ...form, icon: e.target.value })} />
        </div>
        <div className="form-group">
          <label>{t('agents.description')}</label>
          <input className="input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </div>
        <div className="form-group">
          <label>{t('agents.role')}</label>
          <textarea className="input" rows={3} value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} />
        </div>
        <div className="form-group">
          <label>{t('agents.skills')}</label>
          <input className="input" value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} />
        </div>
        <div className="form-group">
          <label>{t('agents.tools')}</label>
          <input className="input" value={form.tools} onChange={(e) => setForm({ ...form, tools: e.target.value })} />
        </div>
      </Modal>

      <ConfirmDialog
        open={!!deleteId}
        title={t('common.delete')}
        message={t('agents.deleteConfirm')}
        confirmLabel={t('common.delete')}
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}
