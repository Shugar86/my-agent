import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  listTeams,
  createTeam,
  acceptInvite,
  listTemplates,
  installTemplate,
  completeOnboarding,
  getIntegrationAuthUrl,
} from '../api/appClient';

export default function OnboardingPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [step, setStep] = useState(1);
  const [teamName, setTeamName] = useState('');
  const [teams, setTeams] = useState<Array<{ id: string; name: string }>>([]);
  const [templates, setTemplates] = useState<Array<{ id: string; name: string; description: string }>>([]);
  const [status, setStatus] = useState('');

  useEffect(() => {
    const invite = params.get('invite');
    if (invite) {
      acceptInvite(invite)
        .then(() => setStatus('Invite accepted!'))
        .catch(() => setStatus('Invalid invite'));
    }
    listTeams().then((d) => setTeams(d.teams)).catch(() => {});
    listTemplates(undefined, 'popular').then((t) => setTemplates(t.slice(0, 6))).catch(() => {});
  }, [params]);

  const handleCreateTeam = async () => {
    if (!teamName.trim()) return;
    await createTeam(teamName.trim());
    setStep(2);
  };

  const handleConnectGoogle = async () => {
    try {
      const data = await getIntegrationAuthUrl('google');
      if (data.auth_url) window.location.href = data.auth_url;
    } catch {
      setStatus('Google OAuth not configured');
    }
  };

  const handleInstall = async (id: string) => {
    await installTemplate(id);
    await completeOnboarding();
    navigate(`/workflows`);
  };

  const finish = async () => {
    await completeOnboarding();
    navigate('/');
  };

  return (
    <div style={{ padding: 30, maxWidth: 640, margin: '0 auto' }}>
      <h1 style={{ marginBottom: 8 }}>Welcome to My Agent</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>Step {step} of 3</p>
      {status && <p style={{ color: 'var(--accent)', marginBottom: 16 }}>{status}</p>}

      {step === 1 && (
        <div className="card">
          <h2 style={{ fontSize: 16, marginBottom: 12 }}>Your workspace</h2>
          {teams.length > 0 ? (
            <>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>
                You're in: <strong>{teams[0].name}</strong>
              </p>
              <button type="button" className="btn btn-primary" onClick={() => setStep(2)}>Continue</button>
            </>
          ) : (
            <>
              <input className="input" placeholder="Team name" value={teamName} onChange={(e) => setTeamName(e.target.value)} style={{ marginBottom: 12 }} />
              <button type="button" className="btn btn-primary" onClick={handleCreateTeam}>Create team</button>
            </>
          )}
        </div>
      )}

      {step === 2 && (
        <div className="card">
          <h2 style={{ fontSize: 16, marginBottom: 12 }}>Connect services</h2>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>Link Gmail, Sheets, and more for workflow actions.</p>
          <button type="button" className="btn" onClick={handleConnectGoogle} style={{ marginRight: 8 }}>Connect Google</button>
          <button type="button" className="btn btn-primary" onClick={() => setStep(3)}>Skip for now</button>
        </div>
      )}

      {step === 3 && (
        <div className="card">
          <h2 style={{ fontSize: 16, marginBottom: 12 }}>Install your first workflow</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {templates.map((t) => (
              <button key={t.id} type="button" className="btn" style={{ textAlign: 'left' }} onClick={() => handleInstall(t.id)}>
                <strong>{t.name}</strong>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t.description.slice(0, 80)}</div>
              </button>
            ))}
          </div>
          <button type="button" className="btn btn-primary" style={{ marginTop: 16 }} onClick={finish}>Finish without template</button>
        </div>
      )}
    </div>
  );
}
