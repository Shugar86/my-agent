import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  listTemplates,
  installTemplate,
  rateTemplate,
  getMe,
  publishTemplate,
  getTemplate,
  type Template,
} from '../api/appClient';
import WorkflowThumbnail from '../components/WorkflowThumbnail';

const CATEGORIES = ['all', 'sales', 'support', 'marketing', 'ops', 'productivity', 'finance', 'hr'];

function Stars({ rating, onRate }: { rating: number; onRate?: (n: number) => void }) {
  return (
    <span style={{ color: '#f0b429', cursor: onRate ? 'pointer' : 'default' }}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} onClick={() => onRate?.(i)} style={{ marginRight: 1 }}>
          {i <= Math.round(rating) ? '★' : '☆'}
        </span>
      ))}
    </span>
  );
}

export default function MarketplacePage() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [category, setCategory] = useState('all');
  const [sort, setSort] = useState('popular');
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const [showPublish, setShowPublish] = useState(false);
  const [pubName, setPubName] = useState('');
  const [pubDesc, setPubDesc] = useState('');
  const [pubCategory, setPubCategory] = useState('general');
  const [pubTags, setPubTags] = useState('');
  const [pubDefinition, setPubDefinition] = useState('{"nodes":[],"edges":[]}');
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 250);
    return () => clearTimeout(t);
  }, [search]);

  useEffect(() => {
    setLoading(true);
    listTemplates(
      category === 'all' ? undefined : category,
      sort,
      debouncedSearch || undefined,
    )
      .then(setTemplates)
      .finally(() => setLoading(false));
  }, [category, sort, debouncedSearch]);

  useEffect(() => {
    getMe().then((me) => setIsAdmin(me.role === 'admin')).catch(() => setIsAdmin(false));
  }, []);

  const stats = useMemo(() => {
    const total = templates.length;
    const installs = templates.reduce((sum, t) => sum + (t.installs || 0), 0);
    const avgRating =
      templates.filter((t) => (t.rating_count || 0) > 0).reduce((s, t) => s + t.rating_avg, 0) /
      Math.max(1, templates.filter((t) => (t.rating_count || 0) > 0).length);
    return { total, installs, avgRating: avgRating || 0 };
  }, [templates]);

  const featured = useMemo(
    () => templates.filter((t) => (t.tags || []).includes('featured')).slice(0, 3),
    [templates],
  );

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

  const handlePreview = async (id: string) => {
    try {
      const full = await getTemplate(id);
      setPreviewTemplate(full);
    } catch {
      setToast('Preview failed');
    }
  };

  const handleRate = async (id: string, score: number) => {
    try {
      await rateTemplate(id, score);
      const refreshed = await listTemplates(
        category === 'all' ? undefined : category,
        sort,
        debouncedSearch || undefined,
      );
      setTemplates(refreshed);
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
      const refreshed = await listTemplates(
        category === 'all' ? undefined : category,
        sort,
        debouncedSearch || undefined,
      );
      setTemplates(refreshed);
      setToast('Template published!');
      setTimeout(() => setToast(''), 2000);
    } catch {
      setToast('Publish failed — check JSON definition');
    }
  };

  return (
    <div style={{ padding: 30 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, gap: 16, flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ marginBottom: 4 }}>Marketplace</h1>
          <p style={{ color: 'var(--text-muted)' }}>
            {stats.total} templates · {stats.installs.toLocaleString()} total installs
            {stats.avgRating > 0 ? ` · avg ${stats.avgRating.toFixed(1)}` : ''}
          </p>
        </div>
        {isAdmin && (
          <button className="btn btn-primary" onClick={() => setShowPublish(true)}>+ Publish template</button>
        )}
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          className="input"
          placeholder="Search templates by name, tag, or description..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: 200, maxWidth: 360 }}
        />
        <select className="input" style={{ width: 'auto' }} value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="popular">Popular</option>
          <option value="recent">Recent</option>
        </select>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {CATEGORIES.map((c) => (
          <button
            key={c}
            className={`btn ${category === c ? 'btn-primary' : ''}`}
            onClick={() => setCategory(c)}
          >
            {c}
          </button>
        ))}
      </div>

      {!loading && featured.length > 0 && category === 'all' && !debouncedSearch && (
        <section style={{ marginBottom: 28 }}>
          <h2 style={{ fontSize: 14, marginBottom: 12, color: 'var(--text-muted)', letterSpacing: 0.6, textTransform: 'uppercase' }}>
            Featured
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 16 }}>
            {featured.map((t) => (
              <div
                key={t.id}
                className="card"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  position: 'relative',
                  background: 'linear-gradient(135deg, rgba(31,111,235,0.10) 0%, rgba(234,75,113,0.08) 100%)',
                  border: '1px solid rgba(31,111,235,0.35)',
                }}
              >
                <span className="badge-featured" style={{ position: 'absolute', top: 14, right: 14 }}>Featured</span>
                <WorkflowThumbnail definition={t.definition} height={120} />
                <h3 style={{ fontSize: 17, color: 'var(--accent)', marginTop: 14, marginBottom: 6 }}>{t.name}</h3>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16, flex: 1 }}>{t.description}</p>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-primary" onClick={() => handleInstall(t.id)} style={{ flex: 1 }}>
                    Try in 1 click
                  </button>
                  <button className="btn" onClick={() => handlePreview(t.id)}>Preview</button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {[1, 2, 3, 4, 5, 6].map((i) => <div key={i} className="skeleton" style={{ height: 220 }} />)}
        </div>
      ) : templates.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 40 }}>
          <h3 style={{ marginBottom: 8 }}>No templates match your filters</h3>
          <p style={{ color: 'var(--text-muted)' }}>Try clearing search or selecting a different category.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {templates.map((t) => (
            <div key={t.id} className="card" style={{ display: 'flex', flexDirection: 'column', position: 'relative' }}>
              {(t.tags || []).includes('featured') && (
                <span className="badge-featured" style={{ position: 'absolute', top: 12, right: 12, zIndex: 1 }}>Featured</span>
              )}
              <WorkflowThumbnail definition={t.definition} height={90} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginTop: 12, marginBottom: 8, gap: 8 }}>
                <h3 style={{ fontSize: 15, color: 'var(--accent)' }}>{t.name}</h3>
                <span style={{ fontSize: 11, background: 'var(--bg-tertiary)', padding: '2px 8px', borderRadius: 12, whiteSpace: 'nowrap' }}>{t.category}</span>
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12, minHeight: 40, flex: 1 }}>{t.description}</p>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, fontSize: 13 }}>
                <Stars rating={t.rating_avg || 0} onRate={(score) => handleRate(t.id, score)} />
                <span style={{ color: 'var(--text-muted)' }}>({t.rating_count || 0})</span>
                <span style={{ color: 'var(--text-muted)', marginLeft: 'auto' }}>↓ {t.installs}</span>
              </div>
              {t.tags && t.tags.length > 0 && (
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 12 }}>
                  {t.tags.slice(0, 4).map((tag) => (
                    <span key={tag} style={{ fontSize: 10, padding: '2px 6px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-muted)' }}>
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-primary" onClick={() => handleInstall(t.id)} style={{ flex: 1 }}>
                  Clone & edit
                </button>
                <button className="btn" onClick={() => handlePreview(t.id)}>Preview</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {previewTemplate && (
        <div
          onClick={() => setPreviewTemplate(null)}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 1000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
          }}
        >
          <div
            className="card"
            onClick={(e) => e.stopPropagation()}
            style={{ width: 640, maxWidth: '100%', maxHeight: '90vh', overflowY: 'auto' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 12 }}>
              <div>
                <h2 style={{ marginBottom: 4 }}>{previewTemplate.name}</h2>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{previewTemplate.category}</span>
              </div>
              <button className="btn" onClick={() => setPreviewTemplate(null)}>Close</button>
            </div>
            <p style={{ marginBottom: 12 }}>{previewTemplate.description}</p>
            <WorkflowThumbnail definition={previewTemplate.definition} height={180} />
            <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-muted)' }}>
              {previewTemplate.definition?.nodes?.length || 0} nodes · {previewTemplate.definition?.edges?.length || 0} edges
            </div>
            <details style={{ marginTop: 12 }}>
              <summary style={{ cursor: 'pointer', fontSize: 12, color: 'var(--text-muted)' }}>View JSON definition</summary>
              <pre style={{ marginTop: 8, padding: 12, background: 'var(--bg)', borderRadius: 6, fontSize: 11, overflowX: 'auto' }}>
                {JSON.stringify(previewTemplate.definition, null, 2)}
              </pre>
            </details>
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button className="btn btn-primary" onClick={() => handleInstall(previewTemplate.id)} style={{ flex: 1 }}>
                Clone & edit
              </button>
              <button
                className="btn"
                onClick={() => {
                  const url = `${window.location.origin}/app/share/templates/${previewTemplate.id}`;
                  navigator.clipboard?.writeText(url).then(
                    () => setToast('Share link copied'),
                    () => setToast('Copy failed'),
                  );
                  setTimeout(() => setToast(''), 2000);
                }}
              >
                Copy share link
              </button>
            </div>
          </div>
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
