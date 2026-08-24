#!/usr/bin/env python3
"""Build article pages in the house style, reusing the shared stylesheet.

Source material: a 45-story draft pack. Kept pieces are rewritten here in
the site's own voice; see curation.py for what was cut and why.
"""

import json
import os
import sys

import build_pages
from build_pages import SHARED_CSS, HUB

ARTICLE_CSS = """
  .article-head { padding: 56px 0 8px; }
  h1 {
    font-family: 'Fraunces', serif; font-weight: 700; font-size: clamp(34px, 5vw, 48px);
    line-height: 1.12; letter-spacing: -0.01em; margin: 0 0 18px; text-wrap: balance;
  }
  .dek { font-size: 21px; line-height: 1.6; color: var(--ink-soft); margin: 0 0 22px; max-width: 56ch; }
  .meta { font-size: 15px; color: var(--ink-faint); border-top: 1px solid var(--line); padding-top: 16px; margin-bottom: 8px; }

  .prose { padding: 8px 0 12px; }
  .prose h2 {
    font-family: 'Fraunces', serif; font-weight: 700; font-size: clamp(24px, 3vw, 30px);
    margin: 44px 0 16px; text-wrap: balance;
  }
  .prose h3 { font-family: 'Fraunces', serif; font-weight: 700; font-size: 21px; margin: 30px 0 10px; }
  .prose p { margin: 0 0 20px; max-width: 66ch; }
  .prose ul, .prose ol { margin: 0 0 22px; padding-left: 26px; max-width: 64ch; }
  .prose li { margin-bottom: 10px; }
  .prose strong { color: var(--ink); }

  blockquote.pull {
    margin: 34px 0; padding: 28px 30px; background: var(--surface); border: 1px solid var(--line);
    border-radius: var(--radius); box-shadow: var(--shadow);
  }
  blockquote.pull p {
    font-family: 'Fraunces', serif; font-style: italic; font-weight: 500; font-size: 22px; line-height: 1.5;
    color: var(--ink); margin: 0; max-width: 56ch;
  }

  .callout {
    display: flex; gap: 14px; margin: 34px 0; padding: 22px 24px; background: var(--surface-2);
    border-radius: var(--radius); border-left: 4px solid var(--gold);
  }
  .callout svg { flex: none; width: 24px; height: 24px; stroke: var(--gold); margin-top: 2px; }
  .callout p { margin: 0 0 12px; font-size: 16.5px; color: var(--ink-soft); }
  .callout p:last-child { margin-bottom: 0; }
  .callout strong { color: var(--ink); }

  .checklist { list-style: none; padding: 0; margin: 0 0 22px; display: flex; flex-direction: column; gap: 12px; }
  .checklist li {
    display: flex; gap: 12px; align-items: flex-start; background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; padding: 16px 18px; font-size: 17px;
  }
  .checklist svg { flex: none; width: 22px; height: 22px; stroke: var(--pine-strong); margin-top: 1px; }

  /* At-a-glance fact table: the "facts you need" spine of the site. */
  .facts { margin: 34px 0; border: 1px solid var(--line); border-radius: var(--radius); overflow: hidden; background: var(--surface); }
  .facts-head { background: var(--surface-2); padding: 14px 20px; font-size: 13.5px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--pine-strong); }
  .facts-scroll { overflow-x: auto; }
  .facts table { border-collapse: collapse; width: 100%; min-width: 460px; font-size: 17px; }
  .facts th, .facts td { text-align: left; padding: 14px 20px; border-top: 1px solid var(--line); vertical-align: top; }
  .facts th { font-weight: 700; white-space: nowrap; width: 1%; }
  .facts tr:first-child th, .facts tr:first-child td { border-top: none; }

  .ad-slot { margin: 44px 0; }
  .ad-slot-inner {
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; min-height: 90px;
    border: 1.5px dashed var(--line); border-radius: 10px; background: var(--surface-2); padding: 14px; text-align: center;
  }
  .ad-slot-label { font-size: 12px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink-faint); }
  .ad-slot-note { font-size: 13px; color: var(--ink-faint); }

  .byline { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; font-size: 16px; color: var(--ink-soft); margin: 0 0 14px; border-top: 1px solid var(--line); padding-top: 16px; }
  .byline strong { color: var(--ink); font-size: 17px; }
  .byline span { color: var(--ink-faint); font-size: 15px; }

  .author {
    display: flex; gap: 18px; align-items: flex-start; margin: 40px 0 8px; padding: 26px 28px;
    background: var(--surface-2); border-radius: var(--radius); border-left: 4px solid var(--pine);
  }
  .author .initials {
    flex: none; width: 54px; height: 54px; border-radius: 50%; background: var(--pine);
    color: #FBFAF4; font-family: 'Fraunces', serif; font-weight: 700; font-size: 20px;
    display: flex; align-items: center; justify-content: center; letter-spacing: 0.02em;
  }
  .author h2 { font-family: 'Fraunces', serif; font-weight: 700; font-size: 19px; margin: 0 0 8px; }
  .author p { margin: 0 0 10px; font-size: 16px; color: var(--ink-soft); max-width: 62ch; }
  .author p:last-child { margin-bottom: 0; }

  /* Reader-story call. Replaces the invented "composite" features: same
     warmth, real people, and the strongest content this site can own. */
  .reader-call {
    margin: 40px 0; padding: 28px 30px; border-radius: var(--radius);
    background: var(--surface); border: 2px solid var(--pine); box-shadow: var(--shadow);
  }
  .reader-call .label { display: flex; align-items: center; gap: 9px; font-size: 13.5px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--pine-strong); margin: 0 0 10px; }
  .reader-call .label svg { width: 19px; height: 19px; stroke: var(--pine-strong); flex: none; }
  .reader-call h2 { font-family: 'Fraunces', serif; font-weight: 700; font-size: 23px; margin: 0 0 12px; }
  .reader-call p { margin: 0 0 14px; font-size: 17px; color: var(--ink-soft); max-width: 60ch; }
  .reader-call a.btn {
    display: inline-flex; font-weight: 700; font-size: 16px; padding: 12px 20px; border-radius: 10px;
    background: var(--pine); color: #FBFAF4; text-decoration: none;
  }
  .reader-call a.btn:hover { background: var(--pine-strong); }
  .reader-call .fine { font-size: 14.5px; color: var(--ink-faint); margin: 14px 0 0; }

  .sources { margin: 48px 0 8px; padding: 26px 28px; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); }
  .sources h2 { font-family: 'Fraunces', serif; font-weight: 700; font-size: 20px; margin: 0 0 6px; }
  .sources p.checked { font-size: 15px; color: var(--ink-faint); margin: 0 0 14px; }
  .sources ul { margin: 0; padding-left: 22px; font-size: 16px; }
  .sources li { margin-bottom: 9px; color: var(--ink-soft); }

  .next-up {
    margin: 40px 0 8px; padding: 30px; background: var(--surface); border: 1px solid var(--line);
    border-radius: var(--radius); box-shadow: var(--shadow);
  }
  .next-up p.label { font-size: 13.5px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--pine-strong); margin: 0 0 8px; }
  .next-up h3 { font-family: 'Fraunces', serif; font-weight: 700; font-size: 22px; margin: 0 0 10px; }
  .next-up p { margin: 0 0 16px; color: var(--ink-soft); }
  .next-up a.btn {
    display: inline-flex; font-weight: 700; font-size: 16px; padding: 12px 20px; border-radius: 10px;
    background: var(--pine); color: #FBFAF4; text-decoration: none;
  }
  .next-up a.btn:hover { background: var(--pine-strong); }

  @media (max-width: 600px) {
    .article-head { padding-top: 36px; }
    .facts th, .facts td { padding: 12px 16px; }
  }
"""

CHECK_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" '
             'stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>')
INFO_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" '
            'stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>')

AD_INLINE = """      <div class="ad-slot">
        <div class="ad-slot-inner">
          <span class="ad-slot-label">Advertisement</span>
          <span class="ad-slot-note">In-article unit &middot; activates after AdSense approval</span>
        </div>
      </div>
"""

READER_CALL = """      <div class="reader-call">
        <p class="label">
          <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.4 8.4 0 01-9 8.4 9 9 0 01-3.9-.9L3 21l1.9-4.6A8.4 8.4 0 013 11.5a8.4 8.4 0 019-8.4 8.4 8.4 0 019 8.4z"/></svg>
          Has this happened to you?
        </p>
        <h2>I&rsquo;d like to hear about it</h2>
        <p>If someone tried this on you &mdash; whether it worked or you spotted it in time &mdash;
        write and tell me what happened. What did they say? What made you doubt it, or what made you
        believe it? The near-misses are often the most useful stories of all.</p>
        <p>I publish these with permission, first names only, or completely anonymously if you&rsquo;d
        rather. Nothing goes up without you seeing it first.</p>
        <a class="btn" href="mailto:hello@thesecondhalfguide.com?subject=My%20story">Tell me what happened &rarr;</a>
        <p class="fine">These are real accounts from real readers. We don&rsquo;t invent stories or
        characters, here or anywhere else on this site.</p>
      </div>
"""

AUTHOR = """    <div class="author">
      <div class="initials" aria-hidden="true">ES</div>
      <div>
        <h2>Edward Silva</h2>
        <p>Edward spent more than forty years as a computer professional &mdash; long enough to pick up
        one useful occupational habit: when somebody hands you a summary, go and read the actual
        documentation. He started The Second Half Guide after noticing that most writing aimed at people
        his age was either talking down to him or quietly selling him something, and that the plain
        facts &mdash; the dates, the thresholds, the dollar figures &mdash; were somehow the hardest part
        to find.</p>
        <p>He's married, with two grown sons, both married themselves. He is not a financial adviser, an
        attorney or an insurance agent, and this site doesn't tell you what to do with your money. It
        tells you what the rules actually say, and links to where he checked.</p>
      </div>
    </div>
"""

DISCLAIMER = """      <div class="callout">
        %s
        <p><strong>This is general information, not personal advice.</strong> We report the rules, the
        numbers and the deadlines as clearly as we can. We don't know your income, your state, your
        health or your family &mdash; and all four can change the answer. Treat this as a good place to
        find the right questions, not a substitute for someone looking at your actual situation.</p>
      </div>
""" % INFO_SVG


def check(items):
    lis = '\n'.join(
        f'        <li>\n          {CHECK_SVG}\n          <span>{t}</span>\n        </li>'
        for t in items)
    return f'      <ul class="checklist">\n{lis}\n      </ul>\n'


def facts(head, rows):
    trs = '\n'.join(f'            <tr><th>{k}</th><td>{v}</td></tr>' for k, v in rows)
    return (f'      <div class="facts">\n        <div class="facts-head">{head}</div>\n'
            f'        <div class="facts-scroll">\n          <table>\n{trs}\n'
            f'          </table>\n        </div>\n      </div>\n')


def article(a, links, nav):
    """Render one article. `nav` maps slug -> URL for cross-links."""
    src = '\n'.join(
        f'        <li>{n} &mdash; <a href="{u}">{u}</a></li>' for n, u in a['sources'])
    nxt = a.get('next')
    next_html = ''
    if nxt:
        href = nav.get(nxt['slug'], HUB)
        next_html = f"""    <div class="next-up">
      <p class="label">Next up</p>
      <h3>{nxt['title']}</h3>
      <p>{nxt['blurb']}</p>
      <a class="btn" href="{href}">Read it &rarr;</a>
    </div>
"""
    body = f"""  <div class="wrap">
    <div class="article-head">
      <span class="eyebrow">{a['eyebrow']}</span>
      <h1>{a['h1']}</h1>
      <p class="dek">{a['dek']}</p>
      <p class="byline"><strong>By Edward Silva</strong> <span>&middot; {a['meta']}</span></p>
    </div>

    <div class="prose">
{a['body']}
{READER_CALL if a.get('reader') else ''}{DISCLAIMER}    </div>

    <div class="sources">
      <h2>Where these facts come from</h2>
      <p class="checked">Checked against primary sources on {a['checked']}. Dollar limits and program
      rules change &mdash; if you're reading this well after that date, verify the numbers at the links below.</p>
      <ul>
{src}
      </ul>
    </div>

{AUTHOR}
{next_html}  </div>

  <div class="wrap-wide ad-slot">
    <div class="ad-slot-inner">
      <span class="ad-slot-label">Advertisement</span>
      <span class="ad-slot-note">Footer unit &middot; activates after AdSense approval</span>
    </div>
  </div>
"""
    return f"""<title>{a['title']}</title>
<style>{SHARED_CSS}{ARTICLE_CSS}</style>

<header class="topbar">
  <div class="wrap-wide">
    <a class="wordmark" href="{HUB}">The <em>Second Half</em> Guide</a>
    <a class="topbar-cta" href="{HUB}#ask">Send us a topic &rarr;</a>
  </div>
</header>

<main>
{body}</main>

<footer>
  <div class="wrap-wide foot-grid">
    <span>&copy; 2026 The Second Half Guide</span>
    <span class="foot-links">
      <a href="{links['about']}">About</a>
      <a href="{links['contact']}">Contact</a>
      <a href="{links['privacy']}">Privacy &amp; Terms</a>
    </span>
  </div>
</footer>
"""


CHECKED = '10 August 2026'

ARTICLES = {}

# ---------------------------------------------------------------- senior-age
ARTICLES['senior-age'] = {
    'title': '55, 60, 62, 65: When Does &ldquo;Senior&rdquo; Actually Start? &mdash; The Second Half Guide',
    'eyebrow': 'Facts &amp; thresholds',
    'h1': '55, 60, 62, 65: when does &ldquo;senior&rdquo; actually start?',
    'dek': 'There is no senior birthday. There are about a dozen unrelated clocks, set by different '
           'institutions, that happen to use nearby numbers &mdash; and only some of them matter.',
    'meta': '6 minute read &middot; Verified against 2026 program rules',
    'checked': CHECKED,
    'body': """      <p>A pizza chain decides you're a senior at 55. The National Park Service won't agree until 62.
      Amtrak's standard senior fare starts at 65. Social Security will let you file at 62 but won't call
      it your full retirement age until 67. Medicare mostly shows up at 65.</p>

      <p>None of these organizations consulted each other. &ldquo;Senior&rdquo; sounds like a category
      you enter on a particular morning, the way you became eligible to vote at 18. It isn't. It's a
      patchwork of unrelated definitions, and the single most useful habit you can build in this decade
      is asking a follow-up question: <em>senior for what?</em></p>

      <p>Because the honest answer is that some of these thresholds are worth a few dollars off a train
      ticket, and one or two of them can permanently change what you pay for health care for the rest of
      your life. Telling those apart is the whole game.</p>

""" + facts('The thresholds, roughly in order', [
        ('Age 55', 'A private-market marketing number. Restaurants, retailers, hotels, gyms and some '
                   'housing communities use it. No federal meaning whatsoever.'),
        ('Age 59&frac12;', 'The age at which withdrawals from most retirement accounts stop carrying the '
                           '10% early-withdrawal penalty. A real tax threshold, and the odd half-year is genuine.'),
        ('Age 60', 'Scattered and specific. Some travel programs use it &mdash; Amtrak applies age 60 on '
                   'certain cross-border services with VIA Rail Canada, while its standard U.S. senior '
                   'discount waits until 65. Survivor benefits from Social Security can also begin around here.'),
        ('Age 62', 'Two very different things share this number: the earliest you can claim Social Security '
                   'retirement benefits, and the age you can buy the America the Beautiful Senior Pass.'),
        ('Age 65', 'The big one. Medicare eligibility generally begins, with a seven-month enrollment window '
                   'centred on your birthday month. Amtrak’s standard 10% senior discount also starts here.'),
        ('Age 67', 'Full retirement age for Social Security if you were born in 1960 or later. Not 65 &mdash; '
                   'a genuinely widespread misconception.'),
        ('Age 73', 'Required withdrawals from most traditional retirement accounts begin.'),
    ]) + """
      <h2>The two that actually carry consequences</h2>

      <p>Strip out the marketing and two ages on that list behave differently from the rest, because
      missing them costs money permanently rather than temporarily.</p>

      <p><strong>65, for Medicare.</strong> Your Initial Enrollment Period runs seven months &mdash; the
      three months before your 65th birthday month, that month, and the three months after. If you don't
      have qualifying coverage from a current employer and you miss that window, you can be charged a
      late-enrollment penalty that is added to your premium <em>for as long as you have Part B</em>. Not
      for a year. For as long as you have it. Of every date in this article, this is the one to put on a
      calendar.</p>

      <p><strong>62, for Social Security.</strong> Not because 62 is a deadline &mdash; it's the opposite,
      an opening &mdash; but because the age you choose between 62 and 70 sets your monthly benefit for
      life. Claiming at 62 with a full retirement age of 67 produces a permanently reduced monthly check.
      Waiting past 67 earns delayed retirement credits up to 70. There is no universally correct answer
      here, and anyone who gives you one without asking about your health, your savings and your spouse
      is selling something.</p>

      <blockquote class="pull">
        <p>A discount birthday and a benefits birthday can share a number and have nothing else in
        common. At 62 you can save $80 on park entry or reshape your income for thirty years.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>Why the senior discount is sometimes a trap</h2>

      <p>Here's the part nobody enjoys hearing: &ldquo;10% senior discount&rdquo; does not mean &ldquo;the
      lowest price available to you.&rdquo;</p>

      <p>A public sale, an advance-purchase fare, a membership rate, a credit-card offer or a package
      price can all beat it. Worse, senior rates frequently <em>cannot be combined</em> with other
      promotions, which means asking for the senior price can quietly opt you out of a better one. The
      satisfaction of unlocking the senior rate is real. It is not the same thing as paying less.</p>

      <p>The fix is unglamorous. Get the senior price, then check the price without it, and book the
      smaller number.</p>

      <h2>What's worth doing about any of this</h2>

""" + check([
        'If you are within about a year of 65, put your seven-month Medicare window on a calendar now. '
        'It is the only genuinely unforgiving date in this decade.',
        'Pull your Social Security statement at <em>ssa.gov</em> and check the earnings record for gaps '
        'or errors. They happen, and they quietly shrink a benefit you haven’t claimed yet.',
        'At 62, if you visit federal recreation sites at all, the $80 lifetime Senior Pass is one of the '
        'few thresholds on this list that pays for itself in a couple of trips.',
        'Everywhere else &mdash; restaurants, hotels, retailers &mdash; just ask, then compare against '
        'the regular price. Nothing is lost by asking and something is occasionally lost by assuming.',
    ]) + """
      <p>The years from 55 to 67 are not one door you walk through. They're a corridor of staggered
      thresholds, most of them trivial, two of them consequential. Knowing which is which is most of what
      this decade actually asks of you.</p>
""",
    'sources': [
        ('National Park Service &mdash; Entrance passes', 'https://www.nps.gov/planyourvisit/passes.htm'),
        ('Medicare &mdash; When does Medicare coverage start?',
         'https://www.medicare.gov/basics/get-started-with-medicare/sign-up/when-does-medicare-coverage-start'),
        ('Social Security &mdash; Starting benefits early',
         'https://www.ssa.gov/benefits/retirement/planner/agereduction.html'),
        ('Amtrak &mdash; Senior discount', 'https://www.amtrak.com/seniors-discount'),
    ],
    'next': {'slug': 'parks-pass',
             'title': 'Is the National Parks Senior Pass still one of America’s best deals?',
             'blurb': '$80 for life sounds too good to be true. Mostly it isn’t &mdash; but what the '
                      'pass doesn’t cover surprises people.'},
}

# ---------------------------------------------------------------- five-minute
ARTICLES['five-minute-rule'] = {
    'reader': True,
    'title': 'The Five-Minute Rule: Why Scammers Need You to Act Right Now &mdash; The Second Half Guide',
    'eyebrow': 'Protecting yourself',
    'h1': 'The five-minute rule: why scammers need you to act right now',
    'dek': 'Modern fraud isn’t an intelligence test. It’s an attack on your decision time &mdash; '
           'which is why one boring habit beats memorising every scam.',
    'meta': '6 minute read &middot; FBI and FTC figures current for 2025 reporting year',
    'checked': CHECKED,
    'body': """      <p>A text says money is leaving your account right now. A caller says your Social Security number
      turned up at a crime scene. A pop-up says hackers are inside your computer and you must not shut it
      down.</p>

      <p>The stories are all different. The architecture underneath them is nearly identical: something
      terrible is happening, and there is no time to think.</p>

      <p>That last clause is the actual product. Everything else is set dressing. Once you see modern
      fraud as an attack on your decision time rather than on your intelligence, the defence gets a lot
      simpler &mdash; and a lot more durable, because it doesn't require you to have heard of this
      particular scam before.</p>

      <h2>The scale of it, in numbers</h2>

      <p>This is not a rare misfortune that happens to unusually careless people.</p>

""" + facts('Elder fraud, 2025 reporting year', [
        ('201,266', 'Complaints filed with the FBI’s Internet Crime Complaint Center by people aged '
                    '60 and older &mdash; up 37% on the prior year.'),
        ('$7.75 billion', 'Reported losses from that age group, a 59% increase year over year.'),
        ('$38,000+', 'Average reported loss per older victim.'),
        ('12,400+', 'Older victims reporting losses of at least $100,000 each.'),
        ('20% / 37%', 'People 60+ filed a fifth of all complaints but absorbed well over a third of all '
                      'the money lost.'),
    ]) + """
      <p>That last row is the one worth sitting with. The problem is not that older adults get targeted
      more often. It's that when it lands, it lands much harder &mdash; because that's where the
      retirement accounts and the home equity are.</p>

      <h2>The script, more or less unchanged</h2>

      <p>Whatever the surface story, the sequence tends to run the same way:</p>

      <ul>
        <li>A <strong>trusted institution appears to contact you first</strong> &mdash; a bank, a
        government agency, a well-known company, a family member.</li>
        <li>A <strong>threat is introduced</strong>: theft in progress, an arrest warrant, hacked
        accounts, tax trouble, a grandchild in a cell.</li>
        <li>You are told <strong>normal procedures are too slow</strong>. The branch can't help. The
        website is compromised. It has to be now.</li>
        <li><strong>Secrecy is framed as protective</strong> &mdash; don't tell anyone, it's an active
        investigation, you could compromise it, your spouse might be involved.</li>
        <li>Money is directed into a channel that is <strong>hard or impossible to reverse</strong>:
        wire transfer, cryptocurrency ATM, gift cards, a courier who comes to your door for cash or gold.</li>
      </ul>

      <blockquote class="pull">
        <p>A scammer only has control while you stay inside their channel. Hanging up is not rude. It is
        the entire defence.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>Why a deliberate pause works</h2>

      <p>The five minutes are not magic. Nothing chemical resets at the three-hundred-second mark. What a
      self-imposed delay does is create room for a <em>second source of information</em> to enter a
      decision that the caller has carefully designed to have only one.</p>

      <p>The FTC's guidance is blunt on the two things that break the spell: don't move money to
      &ldquo;protect&rdquo; it, and verify any unexpected contact using a phone number or website you
      already know is real &mdash; the number on the back of your card, the agency's public website, the
      contact already in your phone. Never the number they gave you, and never by pressing 1.</p>

      <h2>Why competent people get caught</h2>

      <p>There's a comforting story that fraud victims were gullible. It doesn't survive contact with the
      case files.</p>

      <p>Expertise is domain-specific. A retired engineer can understand enormously complex systems and
      still have no idea how a bank's actual fraud department behaves. A former executive spent forty
      years being rewarded for responding decisively to urgent problems &mdash; which is precisely the
      reflex being exploited. A grandparent hears panic in a familiar voice and stops processing
      anything else.</p>

      <p>If anything, being good at solving problems quickly is a risk factor. The scam is shaped like a
      problem you can fix.</p>

      <h2>The habit worth building</h2>

""" + check([
        'Decide now, while nothing is happening, that <strong>no legitimate organisation will ever be '
        'harmed by you hanging up and calling back</strong> on a number you looked up yourself. That '
        'single sentence is the rule.',
        'Treat any demand for secrecy as the tell. Real banks and real agencies do not ask you to keep '
        'things from your spouse.',
        'Treat gift cards, crypto ATMs, wire transfers and couriers as a hard stop. There is no ordinary '
        'reason for any institution to want money that way.',
        'Say the sentence out loud so it’s ready: <em>&ldquo;I’m going to verify this '
        'separately and call you back.&rdquo;</em> You do not owe anyone an explanation for it.',
        'If money has already moved, contact your bank and report it at <em>ReportFraud.ftc.gov</em> and '
        '<em>ic3.gov</em>. Speed matters for recovery, and embarrassment is the scammer’s last '
        'weapon &mdash; it’s what keeps people quiet long enough for the trail to go cold.',
    ]) + """
      <p>Most fraud prevention is taught as a recognition test: here are this year's scams, learn to spot
      them. That approach ages badly, because the scripts get rewritten constantly and the next one won't
      look like the last one.</p>

      <p>A process rule ages better, because it targets the structure rather than the story &mdash;
      urgency, isolation, irreversibility. The most important sentence in a high-pressure financial call
      is also the least dramatic one. Their entire advantage is speed. A pause takes it away.</p>
""",
    'sources': [
        ('FBI IC3 &mdash; Elder fraud', 'https://www.ic3.gov/crimeinfo/elderfraud'),
        ('FTC &mdash; Scammers use fake emergencies to steal your money',
         'https://consumer.ftc.gov/articles/scammers-use-fake-emergencies-steal-your-money'),
        ('FTC data spotlight &mdash; How scammers are stealing older adults’ life savings',
         'https://www.ftc.gov/news-events/data-visualizations/data-spotlight/2025/08/false-alarm-real-scam-how-scammers-are-stealing-older-adults-life-savings'),
        ('FTC &mdash; Report fraud', 'https://reportfraud.ftc.gov/'),
    ],
    'next': {'slug': 'voice-cloning',
             'title': 'When the voice really does sound like your grandchild',
             'blurb': 'AI voice cloning removed the one flaw that used to give the grandparent scam away. '
                      'Here’s what replaces it.'},
}

# ---------------------------------------------------------------- voice clone
ARTICLES['voice-cloning'] = {
    'reader': True,
    'title': 'When the Voice Really Sounds Like Your Grandchild &mdash; The Second Half Guide',
    'eyebrow': 'Protecting yourself',
    'h1': 'When the voice really does sound like your grandchild',
    'dek': 'The grandparent scam used to have one reliable flaw: the caller never sounded quite right. '
           'Voice cloning removed it. The thing that still works has nothing to do with the voice.',
    'meta': '5 minute read &middot; Reflects current FTC guidance on AI-assisted fraud',
    'checked': CHECKED,
    'body': """      <p>For years the &ldquo;grandchild in trouble&rdquo; call had a weakness. The voice was wrong.
      Muffled, hurried, a bit off &mdash; and the script had to explain that away, usually with a broken
      nose or a bad connection. Plenty of people caught it right there.</p>

      <p>That weakness is gone. With a short sample of real audio, software can now generate speech that
      resembles a specific person closely enough to survive a panicked thirty-second phone call. The FTC
      has been warning about exactly this since 2023: cloned voices paired with the traditional
      family-emergency script &mdash; an accident, an arrest, a hospital, a lawyer, and an urgent need
      for money.</p>

      <h2>What actually changed</h2>

      <p>Here's the important nuance. The technology does not need to recreate your grandson perfectly
      for an hour of conversation. It never gets asked to.</p>

      <p>An emergency call is <em>naturally</em> short, emotional and noisy. That's not a limitation the
      scammer works around; it's the format they chose. A few convincing seconds are enough, because at
      that point you supply the rest yourself. You fill in the familiarity. You explain away the
      oddities. The call is engineered so that your own memory does most of the impersonation.</p>

      <p>The source audio is easier to come by than people assume. A social media video, a voicemail
      greeting, a church livestream, a podcast interview, a school play posted by a proud parent.</p>

      <blockquote class="pull">
        <p>Caller ID once felt like identity, until spoofing. Voice once felt like identity. That's the
        step we just took.</p>
      </blockquote>

      <h2>What didn't change at all</h2>

      <p>This is the part worth holding onto, because it's genuinely reassuring.</p>

      <p>A real-sounding voice proves exactly one thing: that the audio sounds real. It says nothing
      about who is controlling the call, and nothing whatsoever about whether the emergency exists.</p>

      <p>Those were always separate questions. We just never had to notice, because for most of human
      history a familiar voice was reliable evidence of a familiar person. The verification problem
      hasn't got harder &mdash; it has moved off the sensory cue and onto the event itself. And the
      event is still perfectly checkable.</p>

""" + AD_INLINE + """
      <h2>Two defences, and the honest limits of each</h2>

      <h3>A family code word</h3>

      <p>Some families agree on a private word or question that wouldn't appear anywhere online. The
      appeal is speed: in a genuine emergency, your grandchild can just answer it.</p>

      <p>The limits are real, though. Code words get forgotten, especially by the person in actual
      distress. They can be overheard or shared. And a frightened 19-year-old in a police station is not
      at their most retrieval-ready. Treat it as a useful supplement, not a system.</p>

      <h3>A second channel</h3>

      <p>This is the stronger one. End the call &mdash; end it, don't negotiate &mdash; and reach the
      person through a number already stored in your phone. Or call their parent. Or their sibling.</p>

      <p>The elegance here is that you stop trying to detect synthetic audio, which is a contest you may
      well lose, and instead test whether the underlying event happened, which is a contest you almost
      always win. The FTC's consumer guidance recommends precisely this: call the person on a number you
      know is theirs, or contact another family member to verify the story.</p>

      <p>And when the caller insists there's no time for that, you have your answer. Real emergencies
      survive a two-minute callback. Manufactured ones don't.</p>

      <h2>The tells that still hold</h2>

""" + check([
        'The caller pushes <strong>secrecy</strong> &mdash; especially &ldquo;don’t tell Mom and '
        'Dad.&rdquo; Real trouble almost never comes with a gag order.',
        'A <strong>second authority figure</strong> takes the phone &mdash; a lawyer, a bail bondsman, '
        'an officer. Ask for a name and call the courthouse or department on its published number.',
        'The money is needed in an <strong>unusual form</strong>: gift cards, crypto, wire, or a courier '
        'coming to your door. No legitimate legal process collects that way.',
        'Consider how much of your family’s audio is <strong>public</strong>. This isn’t a '
        'reason to delete anything &mdash; just useful context for how plausible a clone might be.',
        'Have the conversation with your family <em>before</em> it happens. Ten unhurried minutes now is '
        'worth far more than any tip you’ll remember mid-call.',
    ]) + """
      <p>AI doesn't have to fool you for an hour. It only has to beat the first few seconds of your
      scepticism. Which is why the useful skill isn't learning to hear the seams in synthetic
      audio &mdash; it's having a household habit that doesn't depend on hearing anything at all.</p>

      <p>&ldquo;I know that voice&rdquo; is no longer the same sentence as &ldquo;I know who is
      calling.&rdquo; Identity has quietly become something you verify rather than something you
      recognise.</p>
""",
    'sources': [
        ('FTC &mdash; Scammers use AI to enhance their family emergency schemes',
         'https://consumer.ftc.gov/consumer-alerts/2023/03/scammers-use-ai-enhance-their-family-emergency-schemes'),
        ('FTC &mdash; Scammers use fake emergencies to steal your money',
         'https://consumer.ftc.gov/articles/scammers-use-fake-emergencies-steal-your-money'),
        ('FBI IC3 &mdash; Elder fraud', 'https://www.ic3.gov/crimeinfo/elderfraud'),
    ],
    'next': {'slug': 'five-minute-rule',
             'title': 'The five-minute rule',
             'blurb': 'Why nearly every scam is really an attack on your decision time &mdash; and the one '
                      'habit that works against all of them.'},
}

# ---------------------------------------------------------------- parks pass
ARTICLES['parks-pass'] = {
    'title': 'Is the National Parks Senior Pass Still One of America’s Best Deals? &mdash; The Second Half Guide',
    'eyebrow': 'Getting out there',
    'h1': 'Is the National Parks Senior Pass still one of America’s best deals?',
    'dek': '$80 for life, starting at 62. The headline is as good as it sounds &mdash; but the word '
           '&ldquo;parks&rdquo; misleads people about what they’re actually buying.',
    'meta': '5 minute read &middot; Prices verified against NPS listings for 2026',
    'checked': CHECKED,
    'body': """      <p>Some deals are so cheap they make you suspicious. The America the Beautiful Senior Pass is one
      of them: $80, once, and it doesn't expire.</p>

      <p>There isn't a catch, exactly. But there is a widespread misunderstanding about what the pass
      covers, and it's baked into the nickname. People call it the national parks pass. It is not really
      a parks pass, and that distinction decides whether it's a bargain for you specifically.</p>

""" + facts('The Senior Pass at a glance, 2026', [
        ('Who qualifies', 'U.S. citizens and permanent residents aged 62 or older, with documentation of '
                          'age and residency.'),
        ('Lifetime pass', '$80, one time, no expiry.'),
        ('Annual pass', '$20 for a year &mdash; and NPS allows annual passes to be applied toward a '
                        'lifetime pass under program rules.'),
        ('At per-vehicle sites', 'Covers the passholder and everyone else in a non-commercial vehicle.'),
        ('At per-person sites', 'Covers the passholder plus up to three additional adults. Children under '
                                '16 are generally free anyway.'),
        ('Bonus', 'May give 50% off some amenity fees &mdash; camping, boat launch, swimming and certain '
                  'interpretive services.'),
        ('Watch for', 'Buying online or by mail can add a processing charge, so $80 isn’t always the '
                      'checkout total.'),
    ]) + """
      <h2>Why the maths looks so good</h2>

      <p>A single vehicle entry at a marquee park runs a substantial fraction of the lifetime pass price.
      Visit two or three fee-charging federal sites and you're roughly even. Everything after that is
      free entry for the rest of your life, which is not a sentence that appears often in consumer
      pricing.</p>

      <p>The per-vehicle rule is where it gets quietly generous. At most big parks the fee is charged per
      car, not per head &mdash; so one passholder driving four friends through the gate covers all of
      them. Grandparents on a road trip with the family get particularly good value out of this and
      frequently don't realise it.</p>

      <blockquote class="pull">
        <p>The pass covers entrance and standard amenity fees at federal recreation sites. It does not
        cover most of the things you'll actually spend money on.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>What it doesn’t cover</h2>

      <p>This is the part worth reading before you buy.</p>

      <ul>
        <li><strong>State parks.</strong> Not federal, not covered. This surprises people constantly,
        because state parks are often the ones nearest home.</li>
        <li><strong>City and county parks.</strong> Same story.</li>
        <li><strong>Concessionaire charges.</strong> Lodges, restaurants, gift shops, guided tours and
        boat trips run by private operators inside a park are their own businesses, and they charge their
        own prices.</li>
        <li><strong>Lodging and camping in full.</strong> Some camping fees get the 50% discount. Many
        don't. Reservations through private systems generally don't.</li>
        <li><strong>Special recreation permits.</strong> Lottery permits, backcountry permits and
        specialised access usually sit outside the pass.</li>
        <li><strong>Timed-entry reservations.</strong> Increasingly common at busy parks, usually a
        separate small booking fee, and the pass doesn't exempt you from needing one.</li>
      </ul>

      <p>There's one more wrinkle that cuts the other way: a great many federal sites are free to enter
      anyway. Someone whose travel is mostly national monuments, historic sites and free-entry parks
      could hold the pass for a decade and never once use the entrance benefit.</p>

      <h2>So who should actually buy it</h2>

""" + check([
        '<strong>Road trippers.</strong> If a multi-park drive through the West is anywhere in your '
        'plans, buy it before you go. It pays for itself somewhere around the second gate.',
        '<strong>RV and camping travellers.</strong> The amenity discounts on campsites and boat launches '
        'can quietly outrun the entrance savings.',
        '<strong>Anyone who drives companions.</strong> One pass, one carload &mdash; the per-vehicle '
        'rule is the most underused part of the deal.',
        '<strong>Not sure yet? Buy the $20 annual.</strong> It applies toward the lifetime pass under '
        'program rules, so the decision isn’t all-or-nothing.',
        '<strong>Probably skip it if</strong> your outdoor life is mostly state parks, or your travel '
        'budget goes to hotels and tours rather than gate fees.',
    ]) + """
      <p>One last thing that doesn't fit in a spreadsheet. A lifetime pass changes behaviour. When entry
      is already paid for, a federal recreation site becomes the low-friction default &mdash; the place
      you stop on the way somewhere else, the detour you take because why not. Several people have
      described buying the pass and then visiting more parks in the following three years than in the
      previous twenty.</p>

      <p>That's not a financial return. It's arguably the better one.</p>
""",
    'sources': [
        ('National Park Service &mdash; Entrance passes', 'https://www.nps.gov/planyourvisit/passes.htm'),
        ('National Park Service &mdash; Senior Pass changes and FAQs',
         'https://www.nps.gov/planyourvisit/senior-pass-changes.htm'),
    ],
    'next': {'slug': 'senior-age',
             'title': '55, 60, 62, 65: when does &ldquo;senior&rdquo; actually start?',
             'blurb': 'Every institution picked its own number. Here’s the full list, and the two '
                      'that genuinely matter.'},
}

# ---------------------------------------------------------------- beneficiary
ARTICLES['beneficiary-form'] = {
    'title': 'Your Beneficiary Form May Outrank Your Will &mdash; The Second Half Guide',
    'eyebrow': 'Paperwork that matters',
    'h1': 'Your beneficiary form may outrank your will',
    'dek': 'A will is the document everyone has heard of. For a lot of households, it isn’t the one '
           'that decides where the largest accounts go.',
    'meta': '6 minute read &middot; General information &mdash; state law varies considerably',
    'checked': CHECKED,
    'body': """      <p>Picture a will that says, in plain language, &ldquo;divide everything equally among my
      children.&rdquo; Now picture the 401(k) that makes up most of the estate, still carrying a
      beneficiary form completed in 2007, naming one child, filled in during a different marriage.</p>

      <p>Both documents are valid. They say different things. And in many cases it's the eighteen-year-old
      form, not the carefully drafted will, that determines where the money goes.</p>

      <p>This is probably the single most common gap between what people believe their estate plan says
      and what it actually does &mdash; and unlike most estate-planning problems, it's genuinely quick to
      check.</p>

      <h2>Why the form is so powerful</h2>

      <p>Certain assets don't pass through your will at all. They pass by contract, directly to whoever
      is named on the account, and they do it before probate gets involved.</p>

""" + facts('Which assets travel which way', [
        ('By beneficiary form', '401(k) and similar employer plans, IRAs, life insurance, annuities, and '
                                'payable-on-death or transfer-on-death bank and brokerage accounts.'),
        ('By ownership', 'Property held in joint tenancy with right of survivorship typically passes to '
                         'the surviving owner automatically.'),
        ('By your will', 'Most everything else &mdash; solely owned property, personal belongings, '
                         'vehicles, and anything with no beneficiary named or a beneficiary who has died.'),
        ('By trust', 'Assets actually retitled into a trust, which is a step people sometimes skip after '
                     'paying to have the trust drawn up.'),
    ]) + """
      <p>The reason the form wins so often is that it's <em>specific</em>. A plan administrator doesn't
      have to interpret your family history or your intentions. There's a name on file and a set of rules
      for paying out. That specificity is a feature &mdash; it makes payment fast and unambiguous. It's
      also exactly why an obsolete form is dangerous: it preserves a decision long after the reason for
      it disappeared.</p>

      <blockquote class="pull">
        <p>A will is not a master remote control for every asset you own. It governs the estate. Quite a
        lot of money never enters the estate.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>Where this goes wrong in practice</h2>

      <ul>
        <li><strong>Divorce and remarriage.</strong> The classic case. Some states automatically revoke an
        ex-spouse's designation and some don't, and federal rules governing employer plans can override
        state law entirely. Do not rely on it sorting itself out.</li>
        <li><strong>A beneficiary who died first.</strong> If there's no contingent beneficiary named, the
        account may default to the estate &mdash; which can mean probate and, for retirement accounts,
        potentially less favourable tax treatment for whoever inherits.</li>
        <li><strong>Rolling an account to a new provider.</strong> A rollover creates a <em>new</em>
        account. The old beneficiary designation does not necessarily follow it. This one catches
        careful people.</li>
        <li><strong>Naming a minor grandchild directly.</strong> Well-intentioned and frequently messy;
        minors generally can't receive accounts outright, and a court may end up appointing someone to
        manage it.</li>
        <li><strong>Blank forms.</strong> More common than you'd think, especially with older employer
        plans and small life insurance policies from a job three employers ago.</li>
      </ul>

      <h2>The spousal wrinkle</h2>

      <p>Employer-sponsored retirement plans generally give a surviving spouse strong protection. Under
      federal rules, a married participant typically needs the spouse's written consent to name someone
      else as primary beneficiary. IRAs work differently &mdash; they're individual accounts, and outside
      community-property states there's often no equivalent consent requirement.</p>

      <p>So &ldquo;the beneficiary form always wins&rdquo; is too simple. Spousal protections, court
      orders, plan language and state statutes all bear on the outcome. The reliable takeaway isn't that
      one document beats another &mdash; it's that <em>different assets travel by different routes</em>,
      and the routes need to agree with each other.</p>

      <h2>The afternoon that fixes most of this</h2>

""" + check([
        'List every account that could have a beneficiary: workplace retirement plans (including ones at '
        'former employers), IRAs, life insurance, annuities, HSAs, bank and brokerage accounts.',
        'Log in and <strong>actually look at what each one says</strong>. Don’t rely on memory &mdash; '
        'this is the entire exercise, and most people find at least one surprise.',
        'Name a <strong>contingent beneficiary</strong> everywhere, not just a primary one. This is the '
        'most commonly skipped field and the one that most often forces an account into probate.',
        'Check any account you rolled over or moved in the last few years. New account, new form.',
        'Read your will alongside the list and ask one question: <em>do these tell the same story?</em> '
        'If they don’t, that’s the conversation to bring to an attorney.',
    ]) + """
      <p>Estate planning gets discussed as a drafting exercise &mdash; get the right documents written.
      In practice it's closer to a reconciliation exercise. The will, the plan forms, the bank
      registrations, the insurance beneficiaries and the way each asset is titled can every one of them
      be perfectly valid and still point in four different directions.</p>

      <p>Which means the useful question isn't &ldquo;do we have a will?&rdquo; It's &ldquo;do all our
      documents agree?&rdquo;</p>
""",
    'sources': [
        ('IRS &mdash; Retirement topics: beneficiary',
         'https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-beneficiary'),
        ('U.S. Department of Labor &mdash; FAQs about retirement plans and ERISA',
         'https://www.dol.gov/agencies/ebsa/about-ebsa/our-activities/resource-center/faqs/retirement-plans-and-erisa'),
        ('FDIC &mdash; Your insured deposits',
         'https://www.fdic.gov/resources/deposit-insurance/brochures/insured-deposits'),
    ],
    'next': {'slug': 'digital-estate',
             'title': 'Who gets your digital life?',
             'blurb': 'The photos, the email, the subscriptions that keep charging. None of it fits the '
                      'old idea of an estate.'},
}

# ---------------------------------------------------------------- digital
ARTICLES['digital-estate'] = {
    'title': 'Who Gets Your Digital Life When You Die? &mdash; The Second Half Guide',
    'eyebrow': 'Paperwork that matters',
    'h1': 'Who gets your digital life when you die?',
    'dek': 'A generation ago an executor opened a filing cabinet. Now the photographs, the bills and the '
           'password resets all live behind a login &mdash; and a password is not the same thing as '
           'permission.',
    'meta': '6 minute read &middot; Platform tools verified against current provider documentation',
    'checked': CHECKED,
    'body': """      <p>Not long ago, settling an estate involved walking through a house. Open the filing cabinet,
      find the folders, and within an afternoon you had a fair picture of someone's financial life.</p>

      <p>Try that now. The bank statements are paperless. The photographs &mdash; thousands of them,
      possibly the most treasured thing in the estate &mdash; exist only in cloud storage. The bills
      arrive by email, and the email account is also the reset mechanism for every other account. The
      phone that receives the two-factor codes is locked.</p>

      <p>The question sounds simple: who can get into all of that? The answer is not &ldquo;whoever has
      the password,&rdquo; and the gap between those two things causes families real grief at exactly the
      wrong moment.</p>

      <h2>Why a password isn’t enough</h2>

      <p>Two separate systems are in play, and people tend to plan for neither.</p>

      <p><strong>The legal layer.</strong> Most states have adopted a version of the Revised Uniform
      Fiduciary Access to Digital Assets Act &mdash; RUFADAA &mdash; which gives executors, trustees and
      agents under a power of attorney a framework for accessing digital assets when the owner dies or
      loses capacity. It doesn't treat everything alike: the <em>contents</em> of private communications
      generally get more protection than a list of files or account records, and your own recorded
      instructions carry weight.</p>

      <p><strong>The platform layer.</strong> Separately, the provider has security systems whose entire
      purpose is keeping unauthorised people out &mdash; and those systems cannot tell the difference
      between an intruder and a grieving spouse. Logging in with the deceased's credentials may also
      violate the terms of service, which is a genuinely awkward position for an executor.</p>

      <blockquote class="pull">
        <p>The security that protects an account during life is the same security that locks out your
        family after it. It doesn't know which situation it's in.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>The tools the big platforms already give you</h2>

      <p>The good news is that the major providers have built legacy tools, most of them free, most of
      them taking about ten minutes. Almost nobody sets them up.</p>

""" + facts('Legacy tools worth setting up', [
        ('Apple', 'Legacy Contact. You nominate someone; they receive an access key and can request '
                  'access to your Apple Account data after death with a death certificate.'),
        ('Google', 'Inactive Account Manager. You choose how long counts as inactive, who gets notified, '
                   'what data they receive, and whether the account is then deleted.'),
        ('Facebook / Meta', 'Legacy Contact, who can manage a memorialised profile &mdash; or you can '
                            'instruct that the account be deleted instead.'),
        ('Password managers', 'Most offer emergency access, where a named person can request entry and '
                              'receives it after a waiting period if you don’t decline.'),
    ]) + """
      <p>These matter precisely because they grant <em>authorised</em> access rather than borrowed
      credentials. A handwritten list of passwords in a desk drawer is better than nothing, but it goes
      stale fast, it's a security risk while you're alive, and it confers no legal authority at all.</p>

      <h2>What’s actually in a digital estate</h2>

      <ul>
        <li><strong>Photos and video</strong> that exist nowhere else. For most families this is the part
        that causes genuine heartbreak when it's lost.</li>
        <li><strong>Email</strong>, which contains the bills, the contracts, the receipts &mdash; and the
        reset link for nearly everything else.</li>
        <li><strong>Subscriptions that keep charging.</strong> Streaming, software, storage, deliveries.
        They bill a dead person's card indefinitely until someone cancels them.</li>
        <li><strong>Social accounts and private messages</strong>, which raise questions that go well
        beyond money.</li>
        <li><strong>Websites, domain names, online businesses</strong> or creator income.</li>
        <li><strong>Digital wallets and crypto</strong>, where losing the credentials can mean the asset
        is simply gone. No customer service line exists for this.</li>
        <li><strong>The phone itself</strong>, which is often the two-factor gatekeeper for everything
        above.</li>
      </ul>

      <h2>The question traditional estate planning skips</h2>

      <p>There's a real tension here that's worth naming rather than glossing over.</p>

      <p>Families want enough access to close accounts, stop the charges, find the records and rescue the
      photographs. That's a practical, sympathetic need. But not everyone wants every message, search
      history, journal entry and private conversation opened by their children. Both instincts are
      legitimate, and they pull in opposite directions.</p>

      <p>Which is why the platform tools are useful beyond convenience: they let you be specific.
      Photographs to your daughter, email account closed unread. Access is not an all-or-nothing
      setting.</p>

      <h2>A short list, genuinely doable in an evening</h2>

""" + check([
        'Set up <strong>Apple Legacy Contact</strong> and <strong>Google Inactive Account Manager</strong> '
        'if you use those services. Ten minutes each, and they do most of the work.',
        'Make sure someone can get into your <strong>phone</strong> &mdash; it’s the two-factor key '
        'to everything else.',
        'Write down <strong>where things are</strong> rather than every password: which bank, which email '
        'provider, which cloud service, which password manager. A list of locations ages far better than '
        'a list of credentials.',
        'Note any <strong>recurring subscriptions</strong> and which card pays them.',
        'Tell your executor that <strong>digital access exists as a category</strong>. Many people simply '
        'never think to ask.',
        'If crypto or an online business is involved, raise it specifically with an attorney. The '
        'consequences of getting it wrong are unusually final.',
    ]) + """
      <p>The digital estate isn't mainly about cryptocurrency and social media, whatever the headlines
      suggest. It's the mundane items that cause the trouble: the email account needed to reset the
      utility password, the phone that receives the codes, the cloud folder holding the only copy of the
      tax records.</p>

      <p>The old question was &ldquo;who gets my things?&rdquo; The digital version adds two more that
      are just as important: who can <em>find</em> them, and who is actually <em>allowed</em> to open
      them?</p>
""",
    'sources': [
        ('Uniform Law Commission &mdash; Revised Uniform Fiduciary Access to Digital Assets Act',
         'https://www.uniformlaws.org/committees/community-home?CommunityKey=f7237fc4-74c2-4728-81c6-b39a91ecdf22'),
        ('Apple Support &mdash; How to add a Legacy Contact', 'https://support.apple.com/en-us/102631'),
        ('Google Account Help &mdash; About Inactive Account Manager',
         'https://support.google.com/accounts/answer/3036546'),
    ],
    'next': {'slug': 'beneficiary-form',
             'title': 'Your beneficiary form may outrank your will',
             'blurb': 'The quiet paperwork that decides where retirement accounts actually go &mdash; '
                      'regardless of what your will says.'},
}

# ---------------------------------------------------------------- deduction
ARTICLES['senior-deduction'] = {
    'title': 'The New $6,000 Senior Deduction, Explained &mdash; The Second Half Guide',
    'eyebrow': 'Facts &amp; thresholds',
    'h1': 'The new $6,000 senior deduction, explained',
    'dek': 'A genuinely new tax break for people 65 and over &mdash; temporary, income-limited, and '
           'widely misdescribed as &ldquo;no tax on Social Security.&rdquo; Here’s what it actually is.',
    'meta': '5 minute read &middot; Verified against IRS guidance for tax years 2025&ndash;2028',
    'checked': CHECKED,
    'body': """      <p>If you turned 65 recently, you've probably seen a headline claiming Social Security benefits
      are now tax-free. That's not what happened, and the gap between the headline and the law is worth
      understanding &mdash; because the real provision is still useful to a great many people, just not
      in the way it's been described.</p>

      <p>What the One Big Beautiful Bill Act created is a <strong>new additional deduction of $6,000 per
      qualifying person aged 65 and over</strong>. It's a deduction against your taxable income. It is
      not an exemption for Social Security, and it doesn't change how benefits are taxed at all.</p>

""" + facts('The senior deduction at a glance', [
        ('Amount', '$6,000 per qualifying individual &mdash; $12,000 for a married couple where both '
                   'spouses are 65 or older.'),
        ('Who qualifies', 'Taxpayers who are 65 or older by the end of the tax year, with a Social '
                          'Security number on the return.'),
        ('Years covered', 'Tax years 2025 through 2028. It expires after that unless Congress extends it.'),
        ('Phase-out starts', 'Modified adjusted gross income above $75,000 single / $150,000 married '
                             'filing jointly.'),
        ('Phase-out rate', 'The deduction shrinks by 6 cents for every dollar of MAGI above the threshold.'),
        ('Fully gone at', '$175,000 MAGI single / $250,000 married filing jointly.'),
        ('Stacks with', 'The standard deduction and the existing additional standard deduction for those '
                        '65+. It is on top of, not instead of.'),
    ]) + """
      <h2>Why the &ldquo;no tax on Social Security&rdquo; framing is wrong</h2>

      <p>The rules for how Social Security benefits are taxed &mdash; the provisional income calculation
      that determines whether 0%, up to 50%, or up to 85% of your benefits are taxable &mdash; were not
      changed. They work exactly as they did before.</p>

      <p>What changed is that many older taxpayers now have $6,000 more in deductions, which for some
      households is enough to wipe out their federal income tax liability entirely. If your tax bill goes
      to zero, it's understandable to describe that as your benefits not being taxed. But the mechanism
      matters, because it explains who gets nothing from this: anyone whose income is already too low to
      owe federal income tax sees no benefit from an additional deduction, and anyone above the phase-out
      ceiling sees no benefit either.</p>

      <blockquote class="pull">
        <p>A deduction only helps if you owe tax. The households this was most loudly advertised to
        include quite a few that get nothing from it.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>The phase-out is where it gets interesting</h2>

      <p>That 6% taper deserves a moment, because it creates a genuine planning consideration in the
      band between the thresholds.</p>

      <p>For a married couple with both spouses over 65, the combined $12,000 deduction begins shrinking
      above $150,000 of MAGI and is gone by $250,000. Inside that range, an extra dollar of income
      doesn't just get taxed &mdash; it also shaves the deduction. That's an effective marginal rate
      somewhat higher than the headline bracket suggests.</p>

      <p>This matters most for people with some control over the <em>timing</em> of income: a Roth
      conversion, a capital gain, an IRA withdrawal beyond what's required. Not a reason to avoid any of
      those things, but a reason for the conversation to include the phase-out rather than just the
      bracket.</p>

      <h2>What to actually do</h2>

""" + check([
        'Check whether you and your spouse are both 65 by <strong>31 December</strong> of the tax year. '
        'Turning 65 in the year counts &mdash; the deduction is not prorated.',
        'Find your <strong>MAGI</strong> and see where it lands against $75,000 / $150,000. If you’re '
        'well below, this simply applies and there’s nothing to plan.',
        'If you’re in the taper band, mention it before any large discretionary withdrawal or Roth '
        'conversion. The interaction is the whole point.',
        'Remember it is <strong>scheduled to expire after 2028</strong>. Any multi-year plan built on it '
        'should assume it may not be there.',
        'Don’t restructure your finances around a headline. Confirm how it applies to your actual '
        'return before acting.',
    ]) + """
      <p>This is one of the clearer new provisions to arrive in a while: a fixed amount, a defined age, a
      published phase-out, an expiry date. For a household in the middle of the income range with both
      spouses over 65, $12,000 of additional deduction is a real reduction in tax owed.</p>

      <p>It's just not the thing the headlines said it was.</p>
""",
    'sources': [
        ('IRS &mdash; Check your eligibility for the new enhanced deduction for seniors',
         'https://www.irs.gov/newsroom/check-your-eligibility-for-the-new-enhanced-deduction-for-seniors'),
        ('IRS &mdash; 2026 filing season updates and resources for seniors',
         'https://www.irs.gov/newsroom/2026-filing-season-updates-and-resources-for-seniors'),
        ('Social Security &mdash; Benefits planner: income taxes and your benefits',
         'https://www.ssa.gov/benefits/retirement/planner/taxes.html'),
    ],
    'next': {'slug': 'senior-age',
             'title': '55, 60, 62, 65: when does &ldquo;senior&rdquo; actually start?',
             'blurb': 'Every age threshold in this decade, and the two that carry permanent consequences.'},
}

# ---------------------------------------------------------------- grandparent
ARTICLES['on-call'] = {
    'title': 'Being Available Without Being On Call &mdash; The Second Half Guide',
    'eyebrow': 'Family life',
    'h1': 'Being available without being on call',
    'dek': 'Grandparenting can be the best thing about this decade. It can also become a job nobody '
           'remembers offering you, and that nobody remembers accepting.',
    'meta': '5 minute read &middot; Family life',
    'checked': CHECKED,
    'body': """      <p>Retirement produces something young families are desperate for: an adult with daytime
      flexibility.</p>

      <p>Which is how you become the answer to the school closure, the sick day, the gap between daycare
      and the new nanny, the airport run, the vet emergency, and the text that opens &ldquo;any chance
      you could...&rdquo;</p>

      <p>For a lot of grandparents that usefulness is one of the genuine pleasures of this stage. It
      buys ordinary time with grandchildren &mdash; not holiday time, ordinary time, which is where the
      good stuff actually accumulates. The trouble starts somewhere much subtler: the point where
      <em>available</em> quietly becomes <em>assumed</em>.</p>

      <h2>Nobody has to behave badly for this to go wrong</h2>

      <p>That's the part worth understanding, because families tend to look for a villain here and there
      usually isn't one.</p>

      <p>Your adult children experience you as flexible, which is accurate. You experience retirement as
      the first stretch in forty years where your calendar belongs to you, which is also accurate. Both
      of those things are true at once, and neither party is being unreasonable.</p>

      <p>The friction comes from the difference between a request and an expectation. A request can be
      declined; that's what makes it a request. An expectation turns a no into a disruption &mdash;
      suddenly you're not declining, you're causing a problem. And people who love each other will
      generally say yes rather than cause a problem, right up until the resentment surfaces somewhere
      unrelated and disproportionate.</p>

      <blockquote class="pull">
        <p>A request allows a no. An expectation turns a no into a crisis. Most family resentment lives
        in the gap between those two things.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>The other retirement budget</h2>

      <p>Retirement planning talks endlessly about money, because dollars are easy to count. Time is the
      other finite asset and it gets no spreadsheet at all.</p>

      <p>Two afternoons a week is over a hundred afternoons a year. That may be precisely how you want to
      spend them &mdash; plenty of grandparents would take that trade instantly and never look back. The
      point isn't that it's too much. The point is that recurring commitments have a scale, and it's
      worth seeing the number before agreeing to it indefinitely.</p>

      <p>It's also worth noticing who in a couple is actually carrying it. Childcare inside a
      grandparent partnership is frequently much less evenly split than either person would say out loud.</p>

      <h2>Both sides are reasonable</h2>

      <p><strong>Your children's side:</strong> childcare is expensive and structurally brittle. One sick
      child collapses the whole week. When a trusted grandparent lives nearby, leaning on family feels
      sensible rather than exploitative &mdash; and your visible enthusiasm reads, fairly, as evidence
      you want to be asked.</p>

      <p><strong>Your side:</strong> &ldquo;retired&rdquo; describes your employment status and almost
      nothing else. You may be caring for a spouse or a parent, managing your own health, travelling,
      working part-time, or simply protecting a stretch of unscheduled life you waited decades for. None
      of that is visible from outside.</p>

      <h2>The conversation, and how to have it early</h2>

""" + check([
        'Have it <strong>before</strong> there’s a problem. A boundary set calmly in a good week '
        'reads completely differently from one set in frustration.',
        'Be concrete rather than principled. &ldquo;Tuesdays and Thursdays work; Fridays I’d rather '
        'keep&rdquo; is easy to plan around. &ldquo;I need more space&rdquo; is not.',
        'Separate <strong>scheduled</strong> from <strong>emergency</strong>. Most people are happy to be '
        'the genuine backstop &mdash; it’s the standing obligation that wears thin.',
        'Say what you <em>do</em> want, not only what you don’t. &ldquo;I’d love the school run '
        'twice a week&rdquo; gives everyone something to build on.',
        'Check in every so often. Children’s schedules change constantly and an arrangement that '
        'fitted last year may not fit now.',
        'If you’re part of a couple, agree between yourselves first. Otherwise one of you ends up '
        'negotiating on behalf of a position the other hasn’t actually agreed to.',
    ]) + """
      <p>Boundaries get talked about as a way of keeping people out. Inside a family they do close to the
      opposite. A grandparent who isn't quietly resentful about Wednesday is much better company on
      Wednesday.</p>

      <p>There's no correct number of hours. The distinction that matters isn't between generous and
      selfish &mdash; it's between generosity you chose and an obligation that arrived without anyone
      ever having the conversation.</p>
""",
    'sources': [
        ('Federal Reserve &mdash; Economic well-being of U.S. households: living arrangements and care work',
         'https://www.federalreserve.gov/publications/2026-economic-well-being-of-us-households-in-2025-living-arrangements-care-work.htm'),
        ('Pew Research Center &mdash; Why U.S. adults live in multigenerational homes',
         'https://www.pewresearch.org/social-trends/2022/03/24/financial-issues-top-the-list-of-reasons-u-s-adults-live-in-multigenerational-homes/'),
    ],
    'next': {'slug': 'senior-age',
             'title': '55, 60, 62, 65: when does &ldquo;senior&rdquo; actually start?',
             'blurb': 'The age thresholds nobody coordinated, sorted into the ones that matter and the '
                      'ones that don’t.'},
}


def _load_batches():
    # Imported lazily inside main(): the batch modules import back from this
    # one, so merging at module scope would recurse when run as a script.
    import importlib
    for mod, name in (('articles_batch2', 'ARTICLES2'), ('articles_batch3', 'ARTICLES3')):
        ARTICLES.update(getattr(importlib.import_module(mod), name))


def main():
    _load_batches()
    links = {'about': HUB, 'contact': HUB, 'privacy': HUB}
    if len(sys.argv) >= 4:
        links = {'about': sys.argv[1], 'contact': sys.argv[2], 'privacy': sys.argv[3]}

    nav = {}
    if os.path.exists('article_urls.json'):
        with open('article_urls.json') as f:
            nav = json.load(f)

    os.makedirs('articles', exist_ok=True)
    for slug, a in ARTICLES.items():
        html = article(a, links, nav)
        path = f'articles/{slug}.html'
        with open(path, 'w') as f:
            f.write(html)
        print(path, len(html))


if __name__ == '__main__':
    main()
