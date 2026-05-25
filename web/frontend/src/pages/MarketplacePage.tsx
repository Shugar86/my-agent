import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  listTemplates,
  installTemplate,
  rateTemplate,
  getMe,
  publishTemplate,
  type Template,
} from '../api/appClient';

const CATEGORIES = ['all', 'sales', 'support', 'marketing', 'ops', 'productivity'];

function Stars({ rating }: { rating: number }) {
  return (
    <span style={{ color: '#f0b429' }}>
      {[1, 2, 3, 4, 5].map((i) => (i <= Math.round(rating) ? '★' : '☆')).join('')}
    </span>
  );
}

export default function MarketplacePage() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [category, setCategory] = useState('all');
  const [sort, setSort] = useState('popular');
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const [showPublish, setShowPublish] = useState(false);
  const [pubName, setPubName] = useState('');
  const [pubDesc, setPubDesc] = useState('');
  const [pubCategory, setPubCategory] = useState('general');
  const [pubTags, setPubTags] = useState('');
  const [pubDefinition, setPubDefinition] = useState('{"nodes":[],"edges":[]}');

  const load = () => {
    setLoading(true);
    listTemplates(category === 'all' ? undefined : category, sort)
      .then(setTemplates)
      .finally(() => setLoading(false));
  };

  useEffect(load, [category, sort]);

  useEffect(() => {
    getMe().then((me) => setIsAdmin(me.role === 'admin')).catch(() => setIsAdmin(false));
  }, []);

  const handleInstall = async (id: string) => {
    try {
      const result = await installTemplate(id);
      setToast('Template installed!');
      setTimeout(() => setToast(''), 2000);
      navigate(`/workflows/${result.workflow.id}`);
    } catch {
      setToast('Install failed');
    }
  };

  const handleRate = async (id: string, score: number) => {
    try {
      await rateTemplate(id, score);
      load();
      setToast('Rating saved');
      setTimeout(() => setToast(''), 2000);
    } catch {
      setToast('Rating failed');
    }
  };

  const handlePublish = async () => {
    try {
      const definition = JSON.parse(pubDefinition);
      await publishTemplate({
        name: pubName,
        description: pubDesc,
        category: pubCategory,
        definition,
        tags: pubTags.split(',').map((t) => t.trim()).filter(Boolean),
      });
      setShowPublish(false);
      setPubName('');
      setPubDesc('');
      load();
      setToast('Template published!');
      setTimeout(() => setToast(''), 2000);
    } catch {
      setToast('Publish failed — check JSON definition');
    }
  };

  return (
    <div style={{ padding: 30 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ marginBottom: 8 }}>Marketplace</h1>
          <p style={{ color: 'var(--text-muted)' }}>25+ workflow templates ready to install</p>
        </div>
        {isAdmin && (
          <button className="btn btn-primary" onClick={() => setShowPublish(true)}>Publish template</button>
        )}
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        {CATEGORIES.map((c) => (
          <button
            key={c}
            className={`btn ${category === c ? 'btn-primary' : ''}`}
            onClick={() => setCategory(c)}
          >
            {c}
          </button>
        ))}
        <select className="input" style={{ width: 'auto' }} value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="popular">Popular</option>
          <option value="recent">Recent</option>
        </select>
      </div>

      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {[1, 2, 3, 4, 5, 6].map((i) => <div key={i} className="skeleton" style={{ height: 140 }} />)}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {templates.map((t) => (
            <div key={t.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 8 }}>
                <h3 style={{ fontSize: 15, color: 'var(--accent)' }}>{t.name}</h3>
                <span style={{ fontSize: 11, background: 'var(--bg-tertiary)', padding: '2px 8px', borderRadius: 12 }}>{t.category}</span>
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12, minHeight: 40 }}>{t.description}</p>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, fontSize: 13 }}>
                <Stars rating={t.rating_avg || 0} />
                <span style={{ color: 'var(--text-muted)' }}>({t.rating_count || 0})</span>
                <span style={{ color: 'var(--text-muted)' }}>· {t.installs} installs</span>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-primary" onClick={() => handleInstall(t.id)}>Install</button>
                <button className="btn" onClick={() => handleRate(t.id, 5)} title="Rate 5 stars">★</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showPublish && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div className="card" style={{ width: 480, maxHeight: '90vh', overflowY: 'auto' }}>
            <h2 style={{ marginBottom: 16 }}>Publish Template</h2>
            <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>Name</label>
            <input className="input" value={pubName} onChange={(e) => setPubName(e.target.value)} style={{ marginBottom: 12 }} />
            <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>Description</label>
            <textarea className="input" value={pubDesc} onChange={(e) => setPubDesc(e.target.value)} rows={3} style={{ marginBottom: 12 }} />
            <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>Category</label>
            <select className="input" value={pubCategory} onChange={(e) => setPubCategory(e.target.value)} style={{ marginBottom: 12 }}>
              {CATEGORIES.filter((c) => c !== 'all').map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>Tags (comma-separated)</label>
            <input className="input" value={pubTags} onChange={(e) => setPubTags(e.target.value)} style={{ marginBottom: 12 }} />
            <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>Definition JSON</label>
            <textarea className="input" value={pubDefinition} onChange={(e) => setPubDefinition(e.target.value)} rows={8} style={{ marginBottom: 16, fontFamily: 'monospace', fontSize: 12 }} />
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-primary" onClick={handlePublish}>Publish</button>
              <button className="btn" onClick={() => setShowPublish(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
