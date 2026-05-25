import { useEffect, useState } from 'react';
import { getMe, listUsers, listTeamMembers, inviteTeamMember, getHealth, type MeUser } from '../api/appClient';

export default function AdminPage() {
  const [loading, setLoading] = useState(true);
  const [me, setMe] = useState<MeUser | null>(null);
  const [users, setUsers] = useState<Array<{ id: string; username: string; role: string; email?: string }>>([]);
  const [members, setMembers] = useState<Array<{ user_id: string; role: string }>>([]);
  const [health, setHealth] = useState<Record<string, unknown>>({});
  const [inviteEmail, setInviteEmail] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    getMe()
      .then(async (user) => {
        setMe(user);
        const tasks: Promise<void>[] = [getHealth().then(setHealth).catch(() => {})];
        if (user.role === 'admin') {
          tasks.push(listUsers().then((u) => setUsers(u)).catch(() => {}));
        }
        if (user.workspace_id && (user.team_role === 'owner' || user.team_role === 'admin')) {
          tasks.push(listTeamMembers(user.workspace_id).then(setMembers).catch(() => {}));
        }
        await Promise.all(tasks);
      })
      .finally(() => setLoading(false));
  }, []);

  const canAdmin = me?.role === 'admin' || me?.team_role === 'owner' || me?.team_role === 'admin';
  if (!loading && !canAdmin) {
    return (
      <div style={{ padding: 30 }}>
        <h1>Admin</h1>
        <p style={{ color: 'var(--text-muted)' }}>You need admin or team owner permissions.</p>
      </div>
    );
  }

  const handleInvite = async () => {
    if (!me?.workspace_id || !inviteEmail.trim()) return;
    try {
      const result = await inviteTeamMember(me.workspace_id, inviteEmail.trim());
      setMessage(`Invite created: ${result.accept_url}`);
      setInviteEmail('');
    } catch {
      setMessage('Invite failed');
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 30 }}>
        <div className="skeleton" style={{ height: 40, width: 160, marginBottom: 16 }} />
        <div className="skeleton" style={{ height: 200 }} />
      </div>
    );
  }

  return (
    <div style={{ padding: 30 }}>
      <h1 style={{ marginBottom: 8 }}>Admin</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 24, fontSize: 13 }}>Users, team, and system health</p>

      <section className="card" style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 14, marginBottom: 12 }}>System health</h2>
        <pre style={{ fontSize: 12, overflow: 'auto', color: 'var(--text-muted)' }}>{JSON.stringify(health, null, 2)}</pre>
        <a href="/metrics" target="_blank" rel="noreferrer" style={{ color: 'var(--accent)', fontSize: 13 }}>Prometheus /metrics →</a>
      </section>

      {me?.workspace_id && (me.team_role === 'owner' || me.team_role === 'admin') && (
        <section className="card" style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 14, marginBottom: 12 }}>Team members</h2>
          {members.map((m) => (
            <div key={m.user_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
              <span style={{ fontSize: 13 }}>{m.user_id}</span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{m.role}</span>
            </div>
          ))}
          <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
            <input className="input" placeholder="email@company.com" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} />
            <button type="button" className="btn btn-primary" onClick={handleInvite}>Invite</button>
          </div>
          {message && <p style={{ fontSize: 12, color: 'var(--accent)', marginTop: 8 }}>{message}</p>}
        </section>
      )}

      {me?.role === 'admin' && (
        <section className="card">
          <h2 style={{ fontSize: 14, marginBottom: 12 }}>All users</h2>
          {users.map((u) => (
            <div key={u.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
              <span style={{ fontSize: 13 }}>{u.username} {u.email ? `(${u.email})` : ''}</span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{u.role}</span>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}
