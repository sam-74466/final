import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  Archive,
  Check,
  Clock,
  Eye,
  EyeOff,
  Fingerprint,
  HeartPulse,
  KeyRound,
  LockKeyhole,
  LogOut,
  Mail,
  Play,
  Plus,
  RefreshCw,
  Save,
  ShieldCheck,
  Trash2,
  UserPlus,
  Users,
  Vault,
} from 'lucide-react'
import api, { clearSession, hasSession, saveSession } from './api'
import './App.css'

const categories = [
  { value: 'credentials', label: 'Credentials' },
  { value: 'documents', label: 'Documents' },
  { value: 'finance', label: 'Finance' },
  { value: 'recovery', label: 'Recovery' },
  { value: 'personal', label: 'Personal' },
]

const emptySecret = {
  title: '',
  category: 'credentials',
  content: '',
}

const emptyNominee = {
  name: '',
  email: '',
  relationship: '',
}

function App() {
  const [session, setSession] = useState(hasSession())
  const [authMode, setAuthMode] = useState('login')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [dashboard, setDashboard] = useState(null)
  const [secrets, setSecrets] = useState([])
  const [nominees, setNominees] = useState([])
  const [activeTab, setActiveTab] = useState('overview')
  const [secretForm, setSecretForm] = useState(emptySecret)
  const [nomineeForm, setNomineeForm] = useState(emptyNominee)
  const [profileDays, setProfileDays] = useState(30)
  const [visibleSecrets, setVisibleSecrets] = useState({})
  const [releaseOutput, setReleaseOutput] = useState(null)

  const profile = dashboard?.user?.profile

  const statusLabel = useMemo(() => {
    if (!profile) return 'Loading'
    return profile.vault_released ? 'Released' : 'Active'
  }, [profile])

  useEffect(() => {
    if (session) {
      loadVault()
    }
  }, [session])

  async function loadVault({ clearMessage = false } = {}) {
    setLoading(true)
    if (clearMessage) {
      setMessage('')
    }
    try {
      const [dashboardRes, secretsRes, nomineesRes] = await Promise.all([
        api.get('/dashboard/'),
        api.get('/secrets/'),
        api.get('/nominees/'),
      ])
      setDashboard(dashboardRes.data)
      if (dashboardRes.data?.user?.profile?.inactivity_days) {
        setProfileDays(dashboardRes.data.user.profile.inactivity_days)
      }
      setSecrets(secretsRes.data)
      setNominees(nomineesRes.data)
    } catch (error) {
      if (error.response?.status === 401) {
        clearSession()
        setSession(false)
      } else {
        setMessage(readError(error))
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleAuth(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const payload = Object.fromEntries(form.entries())
    payload.username = payload.username?.trim()
    if (payload.email) {
      payload.email = payload.email.trim().toLowerCase()
    }
    setLoading(true)
    setMessage('')
    setReleaseOutput(null)
    clearSession()
    try {
      const endpoint = authMode === 'register' ? '/register/' : '/token/'
      const response = await api.post(endpoint, payload)
      saveSession(response.data)
      setSession(true)
      setMessage('Vault session opened.')
    } catch (error) {
      setMessage(readError(error))
    } finally {
      setLoading(false)
    }
  }

  async function saveSecret(event) {
    event.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      await api.post('/secrets/', secretForm)
      setSecretForm(emptySecret)
      setMessage('Secret sealed into the vault.')
      await loadVault()
    } catch (error) {
      setMessage(readError(error))
    } finally {
      setLoading(false)
    }
  }

  async function deleteSecret(id) {
    setLoading(true)
    setMessage('')
    try {
      await api.delete(`/secrets/${id}/`)
      setMessage('Secret removed.')
      await loadVault()
    } catch (error) {
      setMessage(readError(error))
    } finally {
      setLoading(false)
    }
  }

  async function saveNominee(event) {
    event.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      await api.post('/nominees/', nomineeForm)
      setNomineeForm(emptyNominee)
      setMessage('Nominee added.')
      await loadVault()
    } catch (error) {
      setMessage(readError(error))
    } finally {
      setLoading(false)
    }
  }

  async function deleteNominee(id) {
    setLoading(true)
    setMessage('')
    try {
      await api.delete(`/nominees/${id}/`)
      setMessage('Nominee removed.')
      await loadVault()
    } catch (error) {
      setMessage(readError(error))
    } finally {
      setLoading(false)
    }
  }

  async function sendHeartbeat() {
    setLoading(true)
    setMessage('')
    setReleaseOutput(null)
    try {
      await api.post('/heartbeat/')
      setMessage('Heartbeat confirmed.')
      await loadVault()
    } catch (error) {
      setMessage(readError(error))
    } finally {
      setLoading(false)
    }
  }

  async function saveProfile(event) {
    event.preventDefault()
    setLoading(true)
    setMessage('')
    try {
      await api.patch('/profile/', { inactivity_days: Number(profileDays) })
      setMessage('Inactivity window updated.')
      await loadVault()
    } catch (error) {
      setMessage(readError(error))
    } finally {
      setLoading(false)
    }
  }

  async function simulateInactivity() {
    setLoading(true)
    setMessage('')
    setReleaseOutput(null)
    try {
      await api.post('/simulate-inactivity/', {
        days: Number(profileDays) + 1,
      })
      setMessage('Heartbeat moved into demo inactivity.')
      await loadVault()
    } catch (error) {
      setMessage(readError(error))
    } finally {
      setLoading(false)
    }
  }

  async function runInactivityCheck() {
    setLoading(true)
    setMessage('')
    try {
      const response = await api.post('/check-inactivity/')
      const output = {
        ...response.data,
        checked_at: new Date().toISOString(),
      }
      setReleaseOutput(output)
      setMessage(formatReleaseMessage(output))
      await loadVault()
    } catch (error) {
      setMessage(readError(error))
    } finally {
      setLoading(false)
    }
  }

  function logout() {
    clearSession()
    setSession(false)
    setDashboard(null)
    setSecrets([])
    setNominees([])
    setMessage('')
    setReleaseOutput(null)
  }

  if (!session) {
    return (
      <main className="auth-shell">
        <section className="auth-visual" aria-label="Digital Inheritance Vault">
          <div className="brand-mark">
            <Vault size={32} />
          </div>
          <h1>Digital Inheritance Vault</h1>
          <p>Encrypted digital assets, heartbeat monitoring, nominee release.</p>
          <div className="signal-strip">
            <span><ShieldCheck size={18} /> Encryption</span>
            <span><HeartPulse size={18} /> Heartbeat</span>
            <span><Mail size={18} /> Release</span>
          </div>
        </section>

        <section className="auth-panel">
          <div className="auth-card">
            <div className="section-heading">
              <span className="eyebrow"><Fingerprint size={16} /> Secure access</span>
              <h2>{authMode === 'login' ? 'Open your vault' : 'Create your vault'}</h2>
            </div>

            <div className="segmented-control" role="tablist" aria-label="Authentication mode">
              <button
                type="button"
                className={authMode === 'login' ? 'active' : ''}
                onClick={() => setAuthMode('login')}
              >
                Login
              </button>
              <button
                type="button"
                className={authMode === 'register' ? 'active' : ''}
                onClick={() => setAuthMode('register')}
              >
                Register
              </button>
            </div>

            <form className="stack-form" onSubmit={handleAuth}>
              <label>
                Username
                <input name="username" autoComplete="username" required />
              </label>
              {authMode === 'register' && (
                <label>
                  Email
                  <input name="email" type="email" autoComplete="email" required />
                </label>
              )}
              <label>
                Password
                <input name="password" type="password" autoComplete={authMode === 'login' ? 'current-password' : 'new-password'} required minLength={8} />
              </label>
              {authMode === 'register' && (
                <label>
                  Inactivity window
                  <input name="inactivity_days" type="number" min="1" max="365" defaultValue="30" required />
                </label>
              )}
              <button className="primary-button" type="submit" disabled={loading}>
                <LockKeyhole size={18} />
                {authMode === 'login' ? 'Unlock vault' : 'Create vault'}
              </button>
            </form>
            {message && <p className="status-message">{message}</p>}
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark small">
            <Vault size={24} />
          </div>
          <div>
            <strong>Inheritance Vault</strong>
            <span>{dashboard?.user?.username || 'Vault owner'}</span>
          </div>
        </div>

        <nav className="nav-list" aria-label="Vault sections">
          <NavButton icon={Activity} label="Overview" active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} />
          <NavButton icon={KeyRound} label="Secrets" active={activeTab === 'secrets'} onClick={() => setActiveTab('secrets')} />
          <NavButton icon={Users} label="Nominees" active={activeTab === 'nominees'} onClick={() => setActiveTab('nominees')} />
          <NavButton icon={Play} label="Demo" active={activeTab === 'demo'} onClick={() => setActiveTab('demo')} />
        </nav>

        <button className="ghost-button logout-button" type="button" onClick={logout}>
          <LogOut size={18} />
          Logout
        </button>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow"><ShieldCheck size={16} /> {statusLabel}</span>
            <h1>Vault Control Room</h1>
          </div>
          <div className="topbar-actions">
            <button className="icon-button" type="button" onClick={() => loadVault({ clearMessage: true })} disabled={loading} title="Refresh vault">
              <RefreshCw size={18} />
            </button>
            <button className="primary-button" type="button" onClick={sendHeartbeat} disabled={loading}>
              <HeartPulse size={18} />
              I am alive
            </button>
          </div>
        </header>

        {message && <p className="status-message app-message">{message}</p>}

        {activeTab === 'overview' && (
          <Overview
            dashboard={dashboard}
            secrets={secrets}
            nominees={nominees}
            profileDays={profileDays}
            setProfileDays={setProfileDays}
            saveProfile={saveProfile}
            loading={loading}
          />
        )}

        {activeTab === 'secrets' && (
          <SecretsPanel
            secrets={secrets}
            secretForm={secretForm}
            setSecretForm={setSecretForm}
            saveSecret={saveSecret}
            deleteSecret={deleteSecret}
            visibleSecrets={visibleSecrets}
            setVisibleSecrets={setVisibleSecrets}
            loading={loading}
          />
        )}

        {activeTab === 'nominees' && (
          <NomineesPanel
            nominees={nominees}
            nomineeForm={nomineeForm}
            setNomineeForm={setNomineeForm}
            saveNominee={saveNominee}
            deleteNominee={deleteNominee}
            loading={loading}
          />
        )}

        {activeTab === 'demo' && (
          <DemoPanel
            dashboard={dashboard}
            simulateInactivity={simulateInactivity}
            runInactivityCheck={runInactivityCheck}
            releaseOutput={releaseOutput}
            loading={loading}
          />
        )}
      </section>
    </main>
  )
}

function Overview({ dashboard, secrets, nominees, profileDays, setProfileDays, saveProfile, loading }) {
  const stats = dashboard?.stats || {}
  const profile = dashboard?.user?.profile

  return (
    <div className="page-grid">
      <section className="metrics-grid">
        <Metric icon={Archive} label="Secrets" value={stats.secret_count ?? 0} tone="teal" />
        <Metric icon={Users} label="Nominees" value={stats.nominee_count ?? 0} tone="amber" />
        <Metric icon={Clock} label="Days left" value={profile?.days_until_release ?? 0} tone="green" />
        <Metric icon={AlertTriangle} label="Releases" value={stats.release_count ?? 0} tone="coral" />
      </section>

      <section className="panel wide">
        <div className="section-heading">
          <span className="eyebrow"><Activity size={16} /> Heartbeat status</span>
          <h2>Owner activity monitor</h2>
        </div>
        <div className="heartbeat-row">
          <div className="pulse-ring">
            <HeartPulse size={36} />
          </div>
          <div>
            <strong>{formatDate(profile?.last_heartbeat)}</strong>
            <span>Next release review: {formatDate(stats.release_deadline)}</span>
          </div>
        </div>
        <form className="inline-form" onSubmit={saveProfile}>
          <label>
            Inactivity days
            <input
              type="number"
              min="1"
              max="365"
              value={profileDays}
              onChange={(event) => setProfileDays(event.target.value)}
            />
          </label>
          <button className="secondary-button" type="submit" disabled={loading}>
            <Save size={18} />
            Save
          </button>
        </form>
      </section>

      <section className="panel">
        <div className="section-heading">
          <span className="eyebrow"><KeyRound size={16} /> Latest secrets</span>
          <h2>Vault items</h2>
        </div>
        <div className="compact-list">
          {secrets.slice(0, 4).map((secret) => (
            <div className="compact-row" key={secret.id}>
              <span>{secret.title}</span>
              <small>{labelForCategory(secret.category)}</small>
            </div>
          ))}
          {secrets.length === 0 && <EmptyState icon={KeyRound} text="No secrets stored yet." />}
        </div>
      </section>

      <section className="panel">
        <div className="section-heading">
          <span className="eyebrow"><UserPlus size={16} /> Trusted people</span>
          <h2>Nominees</h2>
        </div>
        <div className="compact-list">
          {nominees.slice(0, 4).map((nominee) => (
            <div className="compact-row" key={nominee.id}>
              <span>{nominee.name}</span>
              <small>{nominee.relationship}</small>
            </div>
          ))}
          {nominees.length === 0 && <EmptyState icon={Users} text="No nominees assigned yet." />}
        </div>
      </section>
    </div>
  )
}

function SecretsPanel({ secrets, secretForm, setSecretForm, saveSecret, deleteSecret, visibleSecrets, setVisibleSecrets, loading }) {
  return (
    <div className="split-grid">
      <section className="panel">
        <div className="section-heading">
          <span className="eyebrow"><LockKeyhole size={16} /> Encrypted note</span>
          <h2>Add secret</h2>
        </div>
        <form className="stack-form" onSubmit={saveSecret}>
          <label>
            Title
            <input
              value={secretForm.title}
              onChange={(event) => setSecretForm({ ...secretForm, title: event.target.value })}
              required
              placeholder="Gmail recovery key"
            />
          </label>
          <label>
            Category
            <select
              value={secretForm.category}
              onChange={(event) => setSecretForm({ ...secretForm, category: event.target.value })}
            >
              {categories.map((category) => (
                <option key={category.value} value={category.value}>{category.label}</option>
              ))}
            </select>
          </label>
          <label>
            Content
            <textarea
              value={secretForm.content}
              onChange={(event) => setSecretForm({ ...secretForm, content: event.target.value })}
              required
              rows="7"
              placeholder="Account recovery instructions, document location, or private note"
            />
          </label>
          <button className="primary-button" type="submit" disabled={loading}>
            <Plus size={18} />
            Seal secret
          </button>
        </form>
      </section>

      <section className="records-panel">
        {secrets.map((secret) => {
          const isVisible = visibleSecrets[secret.id]
          return (
            <article className="record-card" key={secret.id}>
              <div className="record-header">
                <div>
                  <strong>{secret.title}</strong>
                  <span>{labelForCategory(secret.category)} - Updated {formatDate(secret.updated_at)}</span>
                </div>
                <div className="record-actions">
                  <button
                    className="icon-button"
                    type="button"
                    onClick={() => setVisibleSecrets({ ...visibleSecrets, [secret.id]: !isVisible })}
                    title={isVisible ? 'Hide secret' : 'Show secret'}
                  >
                    {isVisible ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                  <button className="icon-button danger" type="button" onClick={() => deleteSecret(secret.id)} title="Delete secret">
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
              <pre className={isVisible ? 'secret-content visible' : 'secret-content'}>{isVisible ? secret.content : 'Encrypted content hidden'}</pre>
            </article>
          )
        })}
        {secrets.length === 0 && <EmptyState icon={Archive} text="Your vault is waiting for its first secret." />}
      </section>
    </div>
  )
}

function NomineesPanel({ nominees, nomineeForm, setNomineeForm, saveNominee, deleteNominee, loading }) {
  return (
    <div className="split-grid">
      <section className="panel">
        <div className="section-heading">
          <span className="eyebrow"><UserPlus size={16} /> Release recipient</span>
          <h2>Add nominee</h2>
        </div>
        <form className="stack-form" onSubmit={saveNominee}>
          <label>
            Name
            <input
              value={nomineeForm.name}
              onChange={(event) => setNomineeForm({ ...nomineeForm, name: event.target.value })}
              required
              placeholder="Asha Mehta"
            />
          </label>
          <label>
            Email
            <input
              value={nomineeForm.email}
              onChange={(event) => setNomineeForm({ ...nomineeForm, email: event.target.value })}
              required
              type="email"
              placeholder="asha@example.com"
            />
          </label>
          <label>
            Relationship
            <input
              value={nomineeForm.relationship}
              onChange={(event) => setNomineeForm({ ...nomineeForm, relationship: event.target.value })}
              required
              placeholder="Sister"
            />
          </label>
          <button className="primary-button" type="submit" disabled={loading}>
            <UserPlus size={18} />
            Add nominee
          </button>
        </form>
      </section>

      <section className="records-panel">
        {nominees.map((nominee) => (
          <article className="record-card nominee-card" key={nominee.id}>
            <div className="avatar">{initials(nominee.name)}</div>
            <div className="nominee-main">
              <strong>{nominee.name}</strong>
              <span>{nominee.email}</span>
              <small>{nominee.relationship}</small>
            </div>
            <button className="icon-button danger" type="button" onClick={() => deleteNominee(nominee.id)} title="Delete nominee">
              <Trash2 size={18} />
            </button>
          </article>
        ))}
        {nominees.length === 0 && <EmptyState icon={Users} text="No nominees assigned yet." />}
      </section>
    </div>
  )
}

function DemoPanel({ dashboard, simulateInactivity, runInactivityCheck, releaseOutput, loading }) {
  const results = releaseOutput?.results || []
  const checkedCount = releaseOutput?.checked_count ?? results.length
  const releasedCount = releaseOutput?.released_count ?? results.filter((item) => item.released).length
  const emailCount = releaseOutput?.emails_sent ?? results.reduce((total, item) => total + Number(item.emails_sent || 0), 0)

  return (
    <div className="demo-grid">
      <section className="panel wide">
        <div className="section-heading">
          <span className="eyebrow"><Play size={16} /> Presentation flow</span>
          <h2>Manual release trigger</h2>
        </div>
        <div className="demo-actions">
          <button className="secondary-button" type="button" onClick={simulateInactivity} disabled={loading}>
            <Clock size={18} />
            Simulate inactivity
          </button>
          <button className="primary-button" type="button" onClick={runInactivityCheck} disabled={loading}>
            <Mail size={18} />
            Run check
          </button>
        </div>
        <div className="timeline">
          <TimelineItem icon={Check} title="Vault active" text={`Heartbeat: ${formatDate(dashboard?.user?.profile?.last_heartbeat)}`} />
          <TimelineItem icon={Clock} title="Threshold crossed" text={`${dashboard?.user?.profile?.inactivity_days || 0} day inactivity window`} />
          <TimelineItem icon={Mail} title="Nominees notified" text="Released emails print in the Django console." />
        </div>
      </section>

      <section className="panel release-panel">
        <div className="section-heading">
          <span className="eyebrow"><Archive size={16} /> Last check</span>
          <h2>Result</h2>
        </div>
        {releaseOutput ? (
          <div className="release-result">
            <div className="result-summary" aria-label="Release check summary">
              <div>
                <span>Checked</span>
                <strong>{checkedCount}</strong>
              </div>
              <div>
                <span>Released</span>
                <strong>{releasedCount}</strong>
              </div>
              <div>
                <span>Emails</span>
                <strong>{emailCount}</strong>
              </div>
            </div>

            {results.length > 0 ? (
              <div className="result-list">
                {results.map((item, index) => (
                  <div className="release-result-row" key={`${item.username || 'vault'}-${index}`}>
                    <div>
                      <span className={item.released ? 'result-pill released' : 'result-pill skipped'}>
                        {item.released ? 'Released' : 'No release'}
                      </span>
                      <strong>{item.username || 'Vault owner'}</strong>
                      <p>{item.reason}</p>
                    </div>
                    <div className="result-counts">
                      <span>{pluralize(item.secret_count, 'secret')}</span>
                      <span>{pluralize(item.nominee_count, 'nominee', 'nominees')}</span>
                      <span>{pluralize(item.emails_sent, 'email')}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState icon={Check} text="Check completed. No inactive vaults were ready for release." />
            )}

            <details className="raw-result">
              <summary>Raw response</summary>
              <pre className="json-output">{JSON.stringify(releaseOutput, null, 2)}</pre>
            </details>
          </div>
        ) : (
          <EmptyState icon={Play} text="Run the check to see release results." />
        )}
      </section>
    </div>
  )
}

function Metric({ icon: Icon, label, value, tone }) {
  return (
    <article className={`metric-card ${tone}`}>
      <Icon size={22} />
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  )
}

function NavButton({ icon: Icon, label, active, onClick }) {
  return (
    <button className={active ? 'nav-button active' : 'nav-button'} type="button" onClick={onClick}>
      <Icon size={18} />
      {label}
    </button>
  )
}

function TimelineItem({ icon: Icon, title, text }) {
  return (
    <div className="timeline-item">
      <span><Icon size={16} /></span>
      <div>
        <strong>{title}</strong>
        <small>{text}</small>
      </div>
    </div>
  )
}

function EmptyState({ icon: Icon, text }) {
  return (
    <div className="empty-state">
      <Icon size={24} />
      <span>{text}</span>
    </div>
  )
}

function formatReleaseMessage(output) {
  const results = output.results || []
  const releasedCount = Number(output.released_count || 0)
  const emailCount = Number(
    output.emails_sent ?? results.reduce((total, item) => total + Number(item.emails_sent || 0), 0),
  )

  if (releasedCount > 0) {
    return `Inactivity check finished: ${pluralize(releasedCount, 'vault')} released, ${pluralize(emailCount, 'email')} printed in the Django console.`
  }

  return `Inactivity check finished: ${results[0]?.reason || 'No inactive vaults were ready for release.'}`
}

function pluralize(count, singular, plural = `${singular}s`) {
  const value = Number(count || 0)
  return `${value} ${value === 1 ? singular : plural}`
}

function readError(error) {
  if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
    return `Cannot reach backend at ${api.defaults.baseURL}. Start the Django server and try again.`
  }
  const data = error.response?.data
  if (!data) return 'Something went wrong.'
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  const [firstKey] = Object.keys(data)
  const value = data[firstKey]
  if (Array.isArray(value)) return `${firstKey}: ${value[0]}`
  return JSON.stringify(data)
}

function labelForCategory(value) {
  return categories.find((category) => category.value === value)?.label || value
}

function formatDate(value) {
  if (!value) return 'Not available'
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function initials(name) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

export default App
