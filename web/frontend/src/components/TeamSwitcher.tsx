import { useEffect, useState } from 'react';
import { getMe, listTeams, setActiveTeam, type Team, type MeUser } from '../api/appClient';

export default function TeamSwitcher() {
  const [me, setMe] = useState<MeUser | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);

  useEffect(() => {
    Promise.all([getMe(), listTeams()])
      .then(([user, teamData]) => {
        setMe(user);
        setTeams(teamData.teams);
      })
      .catch(() => {});
  }, []);

  const activeId = me?.workspace_id || teams[0]?.id;

  const onSwitch = async (teamId: string) => {
    await setActiveTeam(teamId);
    window.location.reload();
  };

  if (teams.length <= 1) {
    return teams[0] ? (
      <div style={{ padding: '8px 20px', fontSize: 12, color: 'var(--text-muted)', borderBottom: '1px solid var(--border)' }}>
        {teams[0].name}
      </div>
    ) : null;
  }

  return (
    <div style={{ padding: '8px 20px', borderBottom: '1px solid var(--border)' }}>
      <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>Workspace</label>
      <select
        className="input"
        value={activeId || ''}
        onChange={(e) => onSwitch(e.target.value)}
        style={{ fontSize: 12, padding: '6px 8px' }}
      >
        {teams.map((t) => (
          <option key={t.id} value={t.id}>{t.name}</option>
        ))}
      </select>
    </div>
  );
}
