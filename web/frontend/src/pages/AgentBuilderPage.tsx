import { useEffect, useState } from 'react';
import { listAgents, saveAgent, streamChat, type Agent } from '../api/appClient';

const STEPS = ['Role', 'Skills', 'Tools', 'Memory', 'Test'];

export default function AgentBuilderPage() {
  const [step, setStep] = useState(0);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [name, setName] = useState('My Agent');
  const [role, setRole] = useState('You are a helpful AI assistant.');
  const [skills, setSkills] = useState<string[]>([]);
  const [tools, setTools] = useState<string[]>([]);
  const [memoryEnabled, setMemoryEnabled] = useState(true);
  const [testInput, setTestInput] = useState('');
  const [testOutput, setTestOutput] = useState('');
  const [testing, setTesting] = useState(false);
  const [toast, setToast] = useState('');

  useEffect(() => {
    listAgents().then((list) => {
      setAgents(Array.isArray(list) ? list : []);
      const allSkills = new Set<string>();
      const allTools = new Set<string>();
      (Array.isArray(list) ? list : []).forEach((a) => {
        (a.skills || []).forEach((s) => allSkills.add(s));
        (a.tools || []).forEach((t) => allTools.add(t));
      });
      if (allSkills.size) setSkills(Array.from(allSkills).slice(0, 3));
      if (allTools.size) setTools(Array.from(allTools).slice(0, 2));
    });
  }, []);

  const availableSkills = [...new Set(agents.flatMap((a) => a.skills || []))];
  const availableTools = [...new Set(agents.flatMap((a) => a.tools || []))];

  const handleSave = async () => {
    try {
      const config = {
        name,
        role,
        skills,
        tools,
        memory: { enabled: memoryEnabled },
        model: { provider: 'openai', model: 'gpt-4o-mini' },
      };
      const result = await saveAgent(config);
      setToast(`Saved agent: ${result.id}`);
      setTimeout(() => setToast(''), 2500);
    } catch {
      setToast('Save failed');
    }
  };

  const handleTest = async () => {
    if (!testInput.trim()) return;
    setTesting(true);
    setTestOutput('');
    let text = '';
    try {
      await streamChat(testInput, 'universal', (event) => {
        if (event.type === 'token' && typeof event.content === 'string') {
          text += event.content;
          setTestOutput(text);
        }
      });
    } catch {
      setTestOutput('Test failed');
    }
    setTesting(false);
  };

  return (
    <div style={{ padding: 30, maxWidth: 900 }}>
      <h1 style={{ marginBottom: 8 }}>Agent Builder</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>Visual wizard to create AI agents</p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        {STEPS.map((s, i) => (
          <button
            key={s}
            className={`btn ${step === i ? 'btn-primary' : ''}`}
            onClick={() => setStep(i)}
          >
            {i + 1}. {s}
          </button>
        ))}
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        {step === 0 && (
          <>
            <label style={{ display: 'block', marginBottom: 8, fontSize: 13 }}>Agent Name</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} style={{ marginBottom: 16 }} />
            <label style={{ display: 'block', marginBottom: 8, fontSize: 13 }}>Role / System Prompt</label>
            <textarea className="input" value={role} onChange={(e) => setRole(e.target.value)} rows={6} />
          </>
        )}
        {step === 1 && (
          <>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>Select skills</p>
            {availableSkills.map((s) => (
              <label key={s} style={{ display: 'flex', gap: 8, marginBottom: 8, fontSize: 13 }}>
                <input type="checkbox" checked={skills.includes(s)} onChange={(e) => {
                  setSkills(e.target.checked ? [...skills, s] : skills.filter((x) => x !== s));
                }} />
                {s}
              </label>
            ))}
            {availableSkills.length === 0 && <p style={{ color: 'var(--text-muted)' }}>No skills available yet</p>}
          </>
        )}
        {step === 2 && (
          <>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>Select tools</p>
            {availableTools.map((t) => (
              <label key={t} style={{ display: 'flex', gap: 8, marginBottom: 8, fontSize: 13 }}>
                <input type="checkbox" checked={tools.includes(t)} onChange={(e) => {
                  setTools(e.target.checked ? [...tools, t] : tools.filter((x) => x !== t));
                }} />
                {t}
              </label>
            ))}
          </>
        )}
        {step === 3 && (
          <label style={{ display: 'flex', gap: 8, fontSize: 13 }}>
            <input type="checkbox" checked={memoryEnabled} onChange={(e) => setMemoryEnabled(e.target.checked)} />
            Enable conversation memory
          </label>
        )}
        {step === 4 && (
          <>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>Test your agent</p>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <input className="input" value={testInput} onChange={(e) => setTestInput(e.target.value)} placeholder="Ask something..." />
              <button className="btn btn-primary" onClick={handleTest} disabled={testing}>Test</button>
            </div>
            {testOutput && (
              <div style={{ background: 'var(--bg)', padding: 12, borderRadius: 6, fontSize: 13, whiteSpace: 'pre-wrap' }}>{testOutput}</div>
            )}
          </>
        )}
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        {step > 0 && <button className="btn" onClick={() => setStep(step - 1)}>Back</button>}
        {step < STEPS.length - 1 ? (
          <button className="btn btn-primary" onClick={() => setStep(step + 1)}>Next</button>
        ) : (
          <button className="btn btn-primary" onClick={handleSave}>Save Agent</button>
        )}
      </div>
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
