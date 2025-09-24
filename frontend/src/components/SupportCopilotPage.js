import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  Brain,
  CheckCircle2,
  ClipboardCheck,
  Clock,
  FileText,
  Headphones,
  MessageSquare,
  Search,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from 'lucide-react';

const tickets = [
  {
    id: 'CS-8234',
    customer: 'Anika Patel',
    company: 'NimbleHR',
    channel: 'Email',
    time: '09:14 AM',
    status: 'Urgent',
    sentiment: 'Frustrated',
    focus: 'Billing · Renewal · Finance Ops',
    summary: 'Invoice total is higher than the quoted renewal due to unexpected seat add-ons.',
    csatRisk: 'High',
    intent: 'Clarify renewal pricing and reconcile invoice amount',
    conversation: [
      {
        id: 1,
        author: 'Anika',
        role: 'customer',
        timestamp: '09:14 AM',
        text: 'Hi team, the renewal invoice you sent over is $2,430 higher than our approved budget. Can you confirm why we are being charged for 8 additional seats?'
      },
      {
        id: 2,
        author: 'Support Copilot',
        role: 'assistant',
        timestamp: '09:16 AM',
        text: 'I reviewed the account history. The extra cost is caused by a temporary upgrade to the Growth plan on November 2nd. Those seats were automatically provisioned when the sales team granted sandbox access.'
      },
      {
        id: 3,
        author: 'Anika',
        role: 'customer',
        timestamp: '09:18 AM',
        text: "Thanks for digging in. Our sandbox users should not affect renewal pricing—this was supposed to be a complimentary enablement program. Can you help adjust the invoice before finance signs off?"
      }
    ],
    aiSummary: 'Customer noticed unexpected charges related to a temporary Growth plan upgrade. They need the invoice corrected before their finance approval meeting.',
    rootCause: 'Growth plan sandbox seats were provisioned without a billing exception. Finance workflow never received the credit memo from sales.',
    recommendations: [
      'Generate a prorated credit memo for 8 Growth seats from Nov 2 - Nov 30.',
      'Update opportunity CRM notes to flag the sandbox enablement program.',
      'Send customer a confirmation that the adjusted invoice matches the signed order form.'
    ],
    suggestions: [
      {
        title: 'Clarify the plan change',
        body: "Hi Anika, thanks for calling out the discrepancy. I dug into the subscription history and confirmed the invoice picked up 8 temporary Growth seats that were created when your team got sandbox access on November 2. I'm issuing a prorated credit so your renewal reflects the 42 licensed seats in the signed order form."
      },
      {
        title: 'Set next steps',
        body: 'I will send the corrected invoice and a credit memo to you within the next 20 minutes so you have everything for the finance review.'
      },
      {
        title: 'Reassure the customer',
        body: 'We will also add a safeguard so sandbox seats stay complimentary going forward.'
      }
    ],
    knowledgeIds: ['kb-billing-tiers', 'kb-credit-memo', 'kb-sandbox-policy']
  },
  {
    id: 'CS-8235',
    customer: 'Miguel Santos',
    company: 'Brightline Retail',
    channel: 'Chat',
    time: '08:52 AM',
    status: 'In progress',
    sentiment: 'Neutral',
    focus: 'Fulfillment · Shipping · Integrations',
    summary: 'Order management webhook is failing, causing duplicate shipments to trigger.',
    csatRisk: 'Medium',
    intent: 'Stabilize webhook integration and prevent double shipments',
    conversation: [
      {
        id: 1,
        author: 'Miguel',
        role: 'customer',
        timestamp: '08:52 AM',
        text: 'We are still seeing duplicate shipping confirmations firing from the order webhook. Warehouse is now pausing shipments until this is resolved.'
      },
      {
        id: 2,
        author: 'Support Copilot',
        role: 'assistant',
        timestamp: '08:55 AM',
        text: 'Acknowledged. The integration logs show the webhook retries are succeeding because Brightline increased the timeout yesterday. I can deploy the suppression rule we used last quarter and share the monitoring dashboard.'
      },
      {
        id: 3,
        author: 'Miguel',
        role: 'customer',
        timestamp: '08:57 AM',
        text: 'Great, please document the suppression so our devs know how to disable it after the next release.'
      }
    ],
    aiSummary: 'Webhook retries are triggering duplicate shipments. Customer needs a temporary suppression rule and documentation for their engineers.',
    rootCause: 'Retries were multiplied after timeout configuration change. Shipping webhook needs idempotency patch.',
    recommendations: [
      'Activate duplicate suppression automation for webhook retries.',
      'Attach monitoring dashboard and note escalation path if orders queue beyond 10 minutes.',
      'Create follow-up ticket for engineering to implement idempotent webhook handler.'
    ],
    suggestions: [
      {
        title: 'Confirm deployment plan',
        body: 'I will deploy the duplicate suppression rule now and monitor it for the next hour. Your team will receive an alert if any shipments remain queued for more than 10 minutes.'
      },
      {
        title: 'Document next steps',
        body: 'I am adding deployment notes to the ticket so your developers can remove the suppression after the idempotency patch ships.'
      }
    ],
    knowledgeIds: ['kb-webhook-retries', 'kb-duplicate-suppression']
  },
  {
    id: 'CS-8236',
    customer: 'Lauren Chen',
    company: 'Waveform Labs',
    channel: 'Voice call',
    time: 'Yesterday',
    status: 'Ready for follow-up',
    sentiment: 'Positive',
    focus: 'Onboarding · Analytics',
    summary: 'Needs guided setup for the new analytics workspace for marketing leadership.',
    csatRisk: 'Low',
    intent: 'Deliver onboarding session and confirm success criteria',
    conversation: [
      {
        id: 1,
        author: 'Lauren',
        role: 'customer',
        timestamp: '05:12 PM',
        text: 'Our marketing leadership wants to see campaign attribution by next Monday. Can you schedule a working session to help us publish the dashboards?'
      },
      {
        id: 2,
        author: 'Support Copilot',
        role: 'assistant',
        timestamp: '05:15 PM',
        text: 'Absolutely. I drafted a playbook that walks through connecting the marketing data warehouse and building the KPI board. Let me share two time options and prep the workspace now.'
      }
    ],
    aiSummary: 'Customer is requesting collaborative onboarding help to launch analytics dashboards for executives.',
    rootCause: 'New workspace lacks preconfigured marketing KPIs and data sync schedule.',
    recommendations: [
      'Share annotated onboarding playbook with customer champions.',
      'Schedule a 45-minute co-working session and invite marketing leadership.',
      'Enable daily refresh on the marketing data sync and test dashboard filters.'
    ],
    suggestions: [
      {
        title: 'Propose session',
        body: 'I can host a guided onboarding session this Thursday at 2 PM PT or Friday at 9 AM PT. I will prepare the workspace with your marketing KPIs so leadership can see real data during the walkthrough.'
      },
      {
        title: 'Share resources',
        body: 'Attaching the annotated playbook with the exact setup flow we will use during the session.'
      }
    ],
    knowledgeIds: ['kb-onboarding-playbook', 'kb-analytics-kpis']
  }
];

const knowledgeBase = [
  {
    id: 'kb-billing-tiers',
    title: 'Billing Adjustments: Product Tier Changes',
    snippet: 'How to reconcile invoices when customers temporarily change product tiers mid-term. Includes credit memo templates and approval workflow.'
  },
  {
    id: 'kb-credit-memo',
    title: 'Issuing and Tracking Credit Memos',
    snippet: 'Step-by-step guide to issuing prorated credits, linking them to Salesforce opportunities, and notifying finance.'
  },
  {
    id: 'kb-sandbox-policy',
    title: 'Sandbox Seat Policy for Customer Enablement',
    snippet: 'Sandbox seats remain complimentary when tagged as Enablement. Ensure sales marks the opportunity with the Sandbox exception flag.'
  },
  {
    id: 'kb-webhook-retries',
    title: 'Webhook Retries & Idempotency Best Practices',
    snippet: 'Explains how to configure retry logic and add idempotent keys to avoid duplicate downstream operations.'
  },
  {
    id: 'kb-duplicate-suppression',
    title: 'Duplicate Shipment Suppression Runbook',
    snippet: 'Automation script that pauses duplicate shipping confirmations and provides rollback steps for engineering.'
  },
  {
    id: 'kb-onboarding-playbook',
    title: 'Customer Onboarding Playbook',
    snippet: 'A repeatable 4-step workflow for co-building workspaces with new customer champions.'
  },
  {
    id: 'kb-analytics-kpis',
    title: 'Marketing Analytics KPI Templates',
    snippet: 'Pre-built dashboards and filters to accelerate marketing attribution reporting.'
  }
];

const productivityWins = [
  {
    title: 'Auto-summarized context',
    description: 'Copilot captures customer intent, risk, and next best actions the moment a ticket opens.'
  },
  {
    title: 'AI-first reply drafting',
    description: 'Generate empathetic, on-brand responses with one click and tailor them before sending.'
  },
  {
    title: 'Hands-free documentation',
    description: 'Notes, CRM updates, and follow-up tasks sync instantly so agents stay focused on the customer.'
  }
];

const automationPlaybooks = [
  {
    title: 'Billing dispute blueprint',
    impact: 'Cuts escalations by 43%',
    steps: [
      'Validate order history and entitlement tags automatically.',
      'Draft credit memo and notify finance in Slack.',
      'Provide pre-approved language for the customer follow-up.'
    ]
  },
  {
    title: 'Incident stabilization kit',
    impact: 'Reduces MTTR by 38%',
    steps: [
      'Detect severity using call transcript sentiment.',
      'Launch suppression automations based on affected systems.',
      'Summarize resolution timeline for the customer status page.'
    ]
  },
  {
    title: 'Onboarding accelerator',
    impact: 'Boosts activation by 2.3×',
    steps: [
      'Auto-build shared agendas tailored to customer goals.',
      'Assign owners for every milestone and surface blockers.',
      'Publish recap emails with recordings and resource links.'
    ]
  }
];

const performanceSignals = [
  {
    label: 'Resolution time delta',
    value: '−27%',
    description: 'Average handle time decreased after deploying the copilot guidance.',
    icon: Activity
  },
  {
    label: 'Proactive saves',
    value: '18',
    description: 'High-risk renewals recovered this week through invoice coaching.',
    icon: ShieldCheck
  },
  {
    label: 'Knowledge coverage',
    value: '94%',
    description: 'Tickets resolved using approved knowledge assets without escalation.',
    icon: FileText
  }
];

const statusStyles = {
  Urgent: 'bg-rose-500/10 text-rose-200 border border-rose-500/40',
  'In progress': 'bg-amber-500/10 text-amber-200 border border-amber-400/40',
  'Ready for follow-up': 'bg-emerald-500/10 text-emerald-200 border border-emerald-400/40'
};

const roleStyles = {
  customer: 'bg-rose-500/10 border border-rose-500/40',
  assistant: 'bg-emerald-500/10 border border-emerald-400/40'
};

const SupportCopilotPage = () => {
  const [selectedTicketId, setSelectedTicketId] = useState(tickets[0].id);
  const [replyDraft, setReplyDraft] = useState('');
  const [selectedArticleId, setSelectedArticleId] = useState(knowledgeBase[0].id);
  const [copyFeedback, setCopyFeedback] = useState('');

  const selectedTicket = useMemo(
    () => tickets.find((ticket) => ticket.id === selectedTicketId),
    [selectedTicketId]
  );

  const filteredArticles = useMemo(() => {
    if (!selectedTicket) {
      return knowledgeBase;
    }
    return knowledgeBase.filter((article) => selectedTicket.knowledgeIds.includes(article.id));
  }, [selectedTicket]);

  useEffect(() => {
    if (selectedTicket && selectedTicket.suggestions.length > 0) {
      setReplyDraft(selectedTicket.suggestions[0].body);
    }
    if (selectedTicket && selectedTicket.knowledgeIds.length > 0) {
      const firstArticleId = selectedTicket.knowledgeIds[0];
      setSelectedArticleId(firstArticleId);
    }
  }, [selectedTicket]);

  useEffect(() => {
    if (copyFeedback) {
      const timeout = setTimeout(() => setCopyFeedback(''), 2000);
      return () => clearTimeout(timeout);
    }
    return undefined;
  }, [copyFeedback]);

  const selectedArticle = useMemo(() => {
    const articleFromSelection = filteredArticles.find((article) => article.id === selectedArticleId);
    return articleFromSelection || filteredArticles[0];
  }, [filteredArticles, selectedArticleId]);

  const handleApplySuggestion = (suggestion) => {
    if (!selectedTicket) return;
    setReplyDraft((current) => {
      if (!current) {
        return suggestion.body;
      }
      if (current.includes(suggestion.body)) {
        return current;
      }
      return `${current}\n\n${suggestion.body}`;
    });
  };

  const handleGenerateOutline = () => {
    if (!selectedTicket) return;
    const greetingName = selectedTicket.customer.split(' ')[0];
    const outline = [
      `Hi ${greetingName},`,
      '',
      `Thanks for your patience while I reviewed ${selectedTicket.intent.toLowerCase()}.`,
      selectedTicket.recommendations[0],
      selectedTicket.recommendations[1],
      selectedTicket.recommendations[2],
      '',
      'Let me know if there is anything else I can clarify!',
      '— Your dedicated support team'
    ].join('\n');
    setReplyDraft(outline);
  };

  const handleCopyReply = async () => {
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(replyDraft);
        setCopyFeedback('Reply copied to clipboard');
      } else {
        setCopyFeedback('Clipboard not available in this browser');
      }
    } catch (error) {
      setCopyFeedback('Unable to copy reply');
    }
  };

  if (!selectedTicket) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-white/10 bg-gradient-to-br from-indigo-950 via-slate-900 to-slate-950">
        <div className="mx-auto flex max-w-7xl flex-col gap-10 px-6 py-16 lg:flex-row lg:items-center">
          <div className="flex-1 space-y-6">
            <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-sm font-medium text-indigo-100">
              <Sparkles className="h-4 w-4" /> Customer Support Copilot
            </span>
            <h1 className="text-4xl font-semibold text-white sm:text-5xl">
              Turn every agent into a revenue-saving hero
            </h1>
            <p className="max-w-2xl text-lg text-slate-300">
              Real-time context, confident replies, and instant follow-up plans—delivered by an AI copilot that understands your customers as well as you do.
            </p>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-sm text-slate-400">Average handle time</p>
                <p className="mt-1 text-2xl font-semibold text-emerald-300">−27%</p>
                <p className="text-xs text-slate-500">week over week</p>
              </div>
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-sm text-slate-400">At-risk renewals saved</p>
                <p className="mt-1 text-2xl font-semibold text-indigo-200">18</p>
                <p className="text-xs text-slate-500">this quarter</p>
              </div>
              <div className="rounded-2xl bg-white/5 p-4">
                <p className="text-sm text-slate-400">Knowledge coverage</p>
                <p className="mt-1 text-2xl font-semibold text-sky-200">94%</p>
                <p className="text-xs text-slate-500">of tickets resolved in-channel</p>
              </div>
            </div>
          </div>
          <div className="flex w-full max-w-sm flex-col gap-4 rounded-3xl border border-white/10 bg-white/5 p-6">
            <div className="flex items-center gap-3">
              <Brain className="h-10 w-10 text-indigo-200" />
              <div>
                <p className="text-sm uppercase tracking-wider text-indigo-200/80">Live intelligence</p>
                <p className="text-lg font-medium text-white">What agents see when the copilot opens a ticket</p>
              </div>
            </div>
            <div className="space-y-3 text-sm text-slate-200">
              <div className="flex items-center gap-2 rounded-xl bg-slate-900/60 p-3">
                <MessageSquare className="h-4 w-4 text-emerald-300" />
                <span>Instant tone & intent analysis for every message.</span>
              </div>
              <div className="flex items-center gap-2 rounded-xl bg-slate-900/60 p-3">
                <ClipboardCheck className="h-4 w-4 text-sky-300" />
                <span>Recommended actions synced to CRM, Jira, and Slack.</span>
              </div>
              <div className="flex items-center gap-2 rounded-xl bg-slate-900/60 p-3">
                <Clock className="h-4 w-4 text-indigo-200" />
                <span>Automated follow-ups so nothing slips through the cracks.</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-12 px-6 py-12">
        <section className="grid gap-6 lg:grid-cols-[320px,1fr,320px]">
          <aside className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Ticket queue</h2>
              <span className="text-xs text-slate-500">3 active</span>
            </div>
            <div className="space-y-3">
              {tickets.map((ticket) => (
                <button
                  key={ticket.id}
                  type="button"
                  onClick={() => setSelectedTicketId(ticket.id)}
                  className={`w-full rounded-2xl border p-4 text-left transition ${
                    ticket.id === selectedTicketId
                      ? 'border-indigo-400/60 bg-indigo-500/10 shadow-lg shadow-indigo-900/40'
                      : 'border-white/5 bg-white/5 hover:border-indigo-400/40 hover:bg-indigo-500/5'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{ticket.channel}</span>
                    <span className="text-xs text-slate-500">{ticket.time}</span>
                  </div>
                  <p className="mt-2 text-sm font-medium text-white">{ticket.customer} · {ticket.company}</p>
                  <p className="mt-1 text-xs text-slate-400">{ticket.summary}</p>
                  <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                    <span className={`rounded-full px-3 py-1 font-medium ${statusStyles[ticket.status] || 'bg-white/10 text-slate-200'}`}>
                      {ticket.status}
                    </span>
                    <span className="rounded-full bg-white/5 px-3 py-1 text-slate-300">
                      Sentiment: {ticket.sentiment}
                    </span>
                    <span className="rounded-full bg-white/5 px-3 py-1 text-slate-300">
                      CSAT risk: {ticket.csatRisk}
                    </span>
                  </div>
                </button>
              ))}
            </div>

            <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-5">
              <div className="flex items-center gap-3">
                <Headphones className="h-5 w-5 text-indigo-200" />
                <div>
                  <p className="text-sm font-semibold text-white">Coaching pulse</p>
                  <p className="text-xs text-slate-500">How the copilot improves each conversation</p>
                </div>
              </div>
              <ul className="mt-4 space-y-2 text-sm text-slate-300">
                {productivityWins.map((item) => (
                  <li key={item.title} className="rounded-2xl bg-white/5 px-3 py-2">
                    <p className="font-medium text-white/90">{item.title}</p>
                    <p className="text-xs text-slate-400">{item.description}</p>
                  </li>
                ))}
              </ul>
            </div>
          </aside>

          <section className="space-y-6">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-widest text-slate-400">AI brief</p>
                  <h3 className="mt-1 text-2xl font-semibold text-white">{selectedTicket.intent}</h3>
                  <p className="mt-2 max-w-2xl text-sm text-slate-300">{selectedTicket.aiSummary}</p>
                </div>
                <div className="flex items-center gap-3 rounded-2xl bg-slate-900/60 px-4 py-3 text-sm text-slate-300">
                  <Sparkles className="h-4 w-4 text-indigo-200" />
                  <span>{selectedTicket.focus}</span>
                </div>
              </div>
              <div className="mt-6 grid gap-4 sm:grid-cols-3">
                <div className="rounded-2xl bg-slate-900/60 p-4">
                  <p className="text-xs uppercase tracking-widest text-indigo-200/80">Root cause</p>
                  <p className="mt-2 text-sm text-slate-200">{selectedTicket.rootCause}</p>
                </div>
                <div className="rounded-2xl bg-slate-900/60 p-4">
                  <p className="text-xs uppercase tracking-widest text-indigo-200/80">Recommended actions</p>
                  <ul className="mt-2 space-y-2 text-sm text-slate-200">
                    {selectedTicket.recommendations.map((recommendation) => (
                      <li key={recommendation} className="flex items-start gap-2">
                        <CheckCircle2 className="mt-1 h-4 w-4 flex-shrink-0 text-emerald-300" />
                        <span>{recommendation}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-2xl bg-slate-900/60 p-4">
                  <p className="text-xs uppercase tracking-widest text-indigo-200/80">Outcome confidence</p>
                  <p className="mt-3 text-3xl font-semibold text-emerald-300">96%</p>
                  <p className="text-xs text-slate-500">Model confidence that this plan will resolve the issue</p>
                </div>
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">Live conversation</h3>
                  <p className="text-xs uppercase tracking-widest text-slate-500">Real-time transcript with tone analysis</p>
                </div>
                <button
                  type="button"
                  onClick={handleGenerateOutline}
                  className="inline-flex items-center gap-2 rounded-full bg-indigo-500/80 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
                >
                  <Sparkles className="h-4 w-4" /> Compose fresh reply
                </button>
              </div>
              <div className="mt-6 space-y-4">
                {selectedTicket.conversation.map((message) => (
                  <div
                    key={message.id}
                    className={`rounded-2xl p-4 text-sm leading-relaxed text-slate-200 ${roleStyles[message.role]}`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-white">{message.author}</span>
                      <span className="text-xs text-slate-400">{message.timestamp}</span>
                    </div>
                    <p className="mt-2 whitespace-pre-line">{message.text}</p>
                  </div>
                ))}
              </div>
              <div className="mt-6 grid gap-4 lg:grid-cols-[1fr,220px]">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-white">Suggested responses</span>
                    {copyFeedback && <span className="text-xs text-emerald-300">{copyFeedback}</span>}
                  </div>
                  <div className="flex flex-wrap gap-3">
                    {selectedTicket.suggestions.map((suggestion) => (
                      <button
                        key={suggestion.title}
                        type="button"
                        onClick={() => handleApplySuggestion(suggestion)}
                        className="rounded-2xl border border-indigo-400/40 bg-indigo-500/10 px-4 py-2 text-left text-sm text-indigo-100 transition hover:bg-indigo-500/20"
                      >
                        <p className="font-semibold">{suggestion.title}</p>
                        <p className="text-xs text-indigo-100/80">Tap to add to the draft</p>
                      </button>
                    ))}
                  </div>
                  <textarea
                    value={replyDraft}
                    onChange={(event) => setReplyDraft(event.target.value)}
                    rows={5}
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/60 p-4 text-sm text-slate-200 placeholder:text-slate-500 focus:border-indigo-400/60 focus:outline-none"
                    placeholder="Draft your response with the copilot..."
                  />
                  <div className="flex flex-wrap gap-3">
                    <button
                      type="button"
                      onClick={handleCopyReply}
                      className="inline-flex items-center gap-2 rounded-full bg-emerald-500/80 px-4 py-2 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400"
                    >
                      <ClipboardCheck className="h-4 w-4" /> Copy reply
                    </button>
                    <button
                      type="button"
                      className="inline-flex items-center gap-2 rounded-full border border-white/10 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-indigo-400/60 hover:text-white"
                    >
                      <Clock className="h-4 w-4" /> Schedule follow-up
                    </button>
                  </div>
                </div>
                <div className="space-y-3 rounded-2xl bg-slate-900/60 p-4 text-sm text-slate-300">
                  <h4 className="text-sm font-semibold text-white">Signal boosters</h4>
                  <p className="text-xs text-slate-500">Copilot tracks empathy, clarity, and policy alignment as you edit.</p>
                  <ul className="space-y-2 text-xs">
                    <li className="flex items-center gap-2 rounded-xl bg-emerald-500/10 px-3 py-2 text-emerald-200">
                      <TrendingUp className="h-4 w-4" /> Empathy score: <span className="font-semibold">Strong</span>
                    </li>
                    <li className="flex items-center gap-2 rounded-xl bg-indigo-500/10 px-3 py-2 text-indigo-200">
                      <ShieldCheck className="h-4 w-4" /> Policy alignment: <span className="font-semibold">On track</span>
                    </li>
                    <li className="flex items-center gap-2 rounded-xl bg-sky-500/10 px-3 py-2 text-sky-200">
                      <Search className="h-4 w-4" /> Knowledge coverage: <span className="font-semibold">Complete</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          <aside className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Knowledge spotlight</h2>
              <Search className="h-4 w-4 text-slate-500" />
            </div>
            <div className="space-y-3">
              {filteredArticles.map((article) => (
                <button
                  key={article.id}
                  type="button"
                  onClick={() => setSelectedArticleId(article.id)}
                  className={`w-full rounded-2xl border p-4 text-left transition ${
                    article.id === selectedArticle?.id
                      ? 'border-indigo-400/60 bg-indigo-500/10'
                      : 'border-white/5 bg-white/5 hover:border-indigo-400/40 hover:bg-indigo-500/5'
                  }`}
                >
                  <p className="text-sm font-semibold text-white">{article.title}</p>
                  <p className="mt-2 text-xs text-slate-400">{article.snippet}</p>
                </button>
              ))}
            </div>
            {selectedArticle && (
              <div className="rounded-3xl border border-white/10 bg-slate-900/60 p-5 text-sm text-slate-300">
                <p className="text-xs uppercase tracking-widest text-indigo-200/80">Preview</p>
                <p className="mt-2 text-base font-semibold text-white">{selectedArticle.title}</p>
                <p className="mt-2 text-sm leading-relaxed text-slate-300">
                  {selectedArticle.snippet} Download the full playbook to copy the approved language into your response.
                </p>
                <button
                  type="button"
                  className="mt-4 inline-flex items-center gap-2 rounded-full bg-indigo-500/80 px-4 py-2 text-xs font-semibold text-white transition hover:bg-indigo-500"
                >
                  <FileText className="h-4 w-4" /> Open full article
                </button>
              </div>
            )}

            <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <div className="flex items-center gap-3">
                <Clock className="h-5 w-5 text-indigo-200" />
                <div>
                  <p className="text-sm font-semibold text-white">Next best actions</p>
                  <p className="text-xs text-slate-500">Autonomously orchestrated by the copilot</p>
                </div>
              </div>
              <ul className="mt-4 space-y-2 text-sm text-slate-300">
                {selectedTicket.recommendations.map((recommendation) => (
                  <li key={recommendation} className="flex items-start gap-2 rounded-2xl bg-slate-900/60 px-3 py-2">
                    <Sparkles className="mt-1 h-4 w-4 text-indigo-200" />
                    <span>{recommendation}</span>
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.2fr,1fr]">
          <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
            <div className="flex items-center gap-3">
              <ClipboardCheck className="h-5 w-5 text-indigo-200" />
              <h3 className="text-lg font-semibold text-white">Automation playbooks</h3>
            </div>
            <p className="mt-2 text-sm text-slate-300">Pre-built workflows orchestrate approvals, notifications, and system updates in seconds.</p>
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              {automationPlaybooks.map((playbook) => (
                <div key={playbook.title} className="rounded-2xl border border-white/10 bg-slate-900/60 p-4 text-sm text-slate-300">
                  <p className="text-xs uppercase tracking-widest text-indigo-200/80">{playbook.impact}</p>
                  <p className="mt-2 text-base font-semibold text-white">{playbook.title}</p>
                  <ul className="mt-3 space-y-2 text-xs">
                    {playbook.steps.map((step) => (
                      <li key={step} className="flex items-start gap-2 text-slate-300">
                        <CheckCircle2 className="mt-1 h-4 w-4 flex-shrink-0 text-emerald-300" />
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
            <div className="flex items-center gap-3">
              <TrendingUp className="h-5 w-5 text-indigo-200" />
              <h3 className="text-lg font-semibold text-white">Performance signals</h3>
            </div>
            <p className="mt-2 text-sm text-slate-300">Leadership dashboards quantify the impact of AI-assisted workflows across the team.</p>
            <div className="mt-6 space-y-3">
              {performanceSignals.map((signal) => (
                <div key={signal.label} className="flex items-start gap-3 rounded-2xl bg-slate-900/60 p-4">
                  <signal.icon className="h-6 w-6 text-indigo-200" />
                  <div>
                    <p className="text-sm font-semibold text-white">{signal.label}</p>
                    <p className="text-2xl font-bold text-indigo-100">{signal.value}</p>
                    <p className="text-xs text-slate-400">{signal.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-white/10 bg-slate-950/80">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-8 text-sm text-slate-400 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-base font-semibold text-white">Ready to give every agent a copilot?</p>
            <p>Connect your help desk, CRM, and product telemetry in under 30 minutes.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-full bg-indigo-500/80 px-5 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500"
            >
              <Sparkles className="h-4 w-4" /> Launch pilot workspace
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-full border border-white/10 px-5 py-2 text-sm font-semibold text-slate-200 transition hover:border-indigo-400/60 hover:text-white"
            >
              <Headphones className="h-4 w-4" /> Talk to an expert
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default SupportCopilotPage;
