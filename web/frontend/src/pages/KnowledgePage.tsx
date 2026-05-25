import { useEffect, useState } from 'react';
import {
  uploadKnowledge,
  searchKnowledge,
  listKnowledgeDocs,
  deleteKnowledgeDoc,
  type KnowledgeDoc,
} from '../api/appClient';
import PageHeader from '../components/ui/PageHeader';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import EmptyState from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';
import { t } from '../i18n';

/** RAG knowledge base — migrated from legacy knowledge.html. */
export default function KnowledgePage() {
  const { showToast } = useToast();
  const [docs, setDocs] = useState<KnowledgeDoc[]>([]);
  const [source, setSource] = useState('');
  const [content, setContent] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Array<{ content: string; source: string; score: number }>>([]);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = () => {
    listKnowledgeDocs().then(setDocs).catch(() => setDocs([]));
  };

  useEffect(() => { refresh(); }, []);

  const handleAdd = async () => {
    if (!content.trim()) {
      showToast(t('knowledge.enterContent'), 'error');
      return;
    }
    setBusy(true);
    try {
      await uploadKnowledge(content.trim(), source.trim());
      showToast(t('knowledge.docAdded'));
      setSource('');
      setContent('');
      refresh();
    } catch {
      showToast(t('common.error'), 'error');
    } finally {
      setBusy(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setBusy(true);
    try {
      const results = await searchKnowledge(searchQuery.trim());
      setSearchResults(results);
    } catch {
      showToast(t('common.error'), 'error');
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await deleteKnowledgeDoc(deleteId);
      refresh();
      showToast(t('common.success'));
    } catch {
      showToast(t('common.error'), 'error');
    } finally {
      setDeleteId(null);
    }
  };

  return (
    <div className="page-content">
      <PageHeader title={t('knowledge.title')} subtitle={t('knowledge.subtitle')} />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20 }}>
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <h3 style={{ fontSize: 15, marginBottom: 12, color: 'var(--accent)' }}>{t('knowledge.addTitle')}</h3>
            <input
              className="input"
              placeholder={t('knowledge.sourcePlaceholder')}
              value={source}
              onChange={(e) => setSource(e.target.value)}
              style={{ marginBottom: 8 }}
            />
            <textarea
              className="input"
              rows={6}
              placeholder={t('knowledge.contentPlaceholder')}
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
            <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
              <button type="button" className="btn btn-primary" onClick={handleAdd} disabled={busy}>{t('knowledge.add')}</button>
              <button type="button" className="btn" onClick={() => { setSource(''); setContent(''); }}>{t('knowledge.clear')}</button>
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontSize: 15, marginBottom: 12, color: 'var(--accent)' }}>{t('knowledge.searchTitle')}</h3>
            <input
              className="input"
              placeholder={t('knowledge.searchPlaceholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button type="button" className="btn btn-primary" style={{ marginTop: 8 }} onClick={handleSearch} disabled={busy}>
              {t('common.search')}
            </button>
            {searchResults.map((r, i) => (
              <div key={i} className="card" style={{ marginTop: 10, padding: 12 }}>
                <div style={{ fontSize: 11, color: 'var(--accent)' }}>{Math.round(r.score * 100)}% · {r.source}</div>
                <p style={{ fontSize: 13, marginTop: 6, whiteSpace: 'pre-wrap' }}>{r.content.slice(0, 400)}</p>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <h3 style={{ fontSize: 15, marginBottom: 8 }}>{t('knowledge.stats')}</h3>
            <div style={{ fontSize: 32, fontWeight: 700, color: 'var(--accent)' }}>{docs.length}</div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{t('knowledge.documents')}</div>
          </div>

          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 style={{ fontSize: 15 }}>{t('knowledge.allDocs')}</h3>
              <button type="button" className="btn btn-ghost" onClick={refresh} aria-label={t('common.refresh')}>🔄</button>
            </div>
            {docs.length === 0 ? (
              <EmptyState title={t('knowledge.empty')} />
            ) : (
              docs.map((d) => (
                <div key={d.id} className="card" style={{ marginBottom: 8, padding: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                    <span style={{ fontSize: 12, color: 'var(--accent)' }}>{d.source || d.id.slice(0, 8)}</span>
                    <button type="button" className="btn btn-ghost" style={{ color: 'var(--danger)', padding: '2px 6px' }} onClick={() => setDeleteId(d.id)}>×</button>
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>{d.preview?.slice(0, 120)}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={!!deleteId}
        title={t('common.delete')}
        message={t('knowledge.deleteConfirm')}
        confirmLabel={t('common.delete')}
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}
