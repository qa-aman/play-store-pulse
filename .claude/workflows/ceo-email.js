export const meta = {
  name: 'ceo-email',
  description: 'Draft the leadership email for a month, then a separate CEO agent checks every number and asks "so what?"; rewrite until it passes or 2 review rounds',
  whenToUse: 'After /play-store-pulse has built the month. Input: the month as MM-YYYY (10-2026) or "October 2026". Never creates a Gmail draft.',
  phases: [
    { title: 'Draft', detail: 'write email.json with the draft-email skill and render it' },
    { title: 'CEO review', detail: 'separate agent recomputes every number and asks so what' },
    { title: 'Rewrite', detail: 'fix every point the CEO raised, then review again' },
  ],
}

const ROOT = '/Users/amanparmar/Documents/AI-PM/Projects/NextLeap/sessions/AGB-C9-Nov-2026'
const MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
const MAX_REVIEWS = 2

const raw = String(args || '').trim()
let label = raw
const named = raw.toLowerCase().match(/^([a-z]+)\s+(\d{4})$/)
if (named && MONTHS.includes(named[1])) label = `${String(MONTHS.indexOf(named[1]) + 1).padStart(2, '0')}-${named[2]}`
if (!/^\d{2}-\d{4}$/.test(label)) throw new Error(`ceo-email needs a month as MM-YYYY or "October 2026", got ${JSON.stringify(raw)}`)

const DIR = `${ROOT}/data/report/${label}`
const CTX = `Project root ${ROOT}; run commands from there with ${ROOT}/.venv/bin/python. Period label ${label}. Data: ${DIR}/*.json (kpis, stars, complaints, praise, hours, daily, versions, loudest, narrative.json) and the raw reviews ${ROOT}/data/raw/reviews_${label}.csv. The email lives in ${DIR}/email.json and renders to ${DIR}/email/{subject.txt,email.txt,email.html}.`
const NO_GMAIL = 'Do not run gmail_draft.py, do not create any Gmail draft, do not send anything, and do not edit email-log.md. Stop after rendering.'

phase('Draft')
const draft = await agent(`${CTX}\nDraft the leadership email for ${label}. Follow ${ROOT}/.claude/skills/draft-email/SKILL.md steps 1 to 5 and its references/email-content.md exactly: read the period, write email.json (numbers only as tokens), render with render_email.py, fix and rerender until it renders clean. If ${DIR}/kpis.json is missing, stop and say /play-store-pulse must run first. ${NO_GMAIL}\nWrite for a CEO who asks "so what?" of every line: each number must lead to a consequence or a decision. Return the final subject and email.txt text.`,
  { label: 'draft:email', phase: 'Draft' })
if (!draft) throw new Error('draft agent failed')

const REVIEW = {
  type: 'object',
  properties: {
    pass: { type: 'boolean' },
    number_issues: { type: 'array', items: { type: 'object', properties: {
      shown: { type: 'string' }, where: { type: 'string' }, correct: { type: 'string' }, how_checked: { type: 'string' },
    }, required: ['shown', 'where', 'correct', 'how_checked'] } },
    so_what: { type: 'array', items: { type: 'object', properties: {
      line: { type: 'string' }, question: { type: 'string' }, fix: { type: 'string' },
    }, required: ['line', 'question', 'fix'] } },
    numbers_checked: { type: 'integer' },
    verdict: { type: 'string' },
  },
  required: ['pass', 'number_issues', 'so_what', 'numbers_checked', 'verdict'],
}

const rounds = []
for (let round = 1; round <= MAX_REVIEWS; round++) {
  const review = await agent(`You are the CEO of Zomato reading the ${label} Play Store leadership email from your PM. You have two minutes and no patience for fluff. You are a separate reviewer: read only, change nothing.\n${CTX}\nRead ${DIR}/email/subject.txt and ${DIR}/email/email.txt.\n1. Numbers: list every number in the subject and body. Recompute each from the raw CSV (and the JSON files for context) with your own Python, using the same definitions as ${ROOT}/scripts/build_report_data.py (import load, COMPLAINTS, share from it). A number passes if it matches at the precision shown. Also flag a number that is right but measured on the wrong group or framed misleadingly. Put each failure in number_issues.\n2. So what: for every claim, ask "so what?" Would you know what to decide or who owns it? Is there a reply-by date and a clear ask? Is anything vague, padded, or a finding with no consequence? Is the subject under 70 characters and the body under 200 words? Put each failure in so_what with the question you would ask the PM and the fix.\npass is true only if number_issues is empty and nothing in so_what is serious enough to send it back. Give a one-line verdict in your own voice.`,
    { label: `ceo:round-${round}`, phase: 'CEO review', schema: REVIEW, effort: 'high' })
  if (!review) throw new Error(`CEO review round ${round} failed`)
  rounds.push(review)
  log(`Round ${round}: ${review.pass ? 'PASS' : 'FAIL'}, ${review.numbers_checked} numbers checked, ${review.number_issues.length} number issues, ${review.so_what.length} so-what points. ${review.verdict}`)
  if (review.pass || round === MAX_REVIEWS) break

  await agent(`${CTX}\nThe CEO sent the ${label} leadership email back. Feedback:\n${JSON.stringify({ number_issues: review.number_issues, so_what: review.so_what }, null, 1)}\nFix every point by editing ${DIR}/email.json (and, only if an ask itself is wrong, ${DIR}/narrative.json, keeping its rules in ${ROOT}/.claude/skills/play-store-pulse/references/narrative.md). Keep following ${ROOT}/.claude/skills/draft-email/references/email-content.md: numbers as tokens, subject under 70 characters, body under 200 words. Rerender with render_email.py until clean. ${NO_GMAIL} Return what you changed, point by point.`,
    { label: `rewrite:round-${round}`, phase: 'Rewrite' })
}

const final = rounds[rounds.length - 1]
return {
  label,
  passed: final.pass,
  review_rounds: rounds.length,
  final_verdict: final.verdict,
  open_number_issues: final.number_issues,
  open_so_what: final.so_what,
  rounds,
  files: [`${DIR}/email.json`, `${DIR}/email/subject.txt`, `${DIR}/email/email.txt`, `${DIR}/email/email.html`],
}
